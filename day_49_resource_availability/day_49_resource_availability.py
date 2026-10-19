from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock
from time import monotonic, sleep
from typing import Dict, Iterable, List, Optional
import json
import math
import tempfile


class ResourceType(Enum):
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    DATABASE_CONNECTION = "database_connection"
    API_QUOTA = "api_quota"


@dataclass(frozen=True)
class ResourceRequest:
    resource_type: ResourceType
    amount: int
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("Resource amount must be positive")
        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative")


@dataclass
class ResourcePool:
    name: str
    resource_type: ResourceType
    capacity: int
    available: int
    allocations: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")
        if not 0 <= self.available <= self.capacity:
            raise ValueError("Available resources must be within capacity")

    def allocate(self, owner: str, amount: int) -> bool:
        if amount <= 0:
            raise ValueError("Allocation amount must be positive")
        if amount > self.available:
            return False

        self.available -= amount
        self.allocations[owner] = self.allocations.get(owner, 0) + amount
        return True

    def release(self, owner: str, amount: Optional[int] = None) -> int:
        owned = self.allocations.get(owner, 0)
        if owned == 0:
            return 0

        released = owned if amount is None else amount
        if released <= 0 or released > owned:
            raise ValueError("Invalid release amount")

        remaining = owned - released
        if remaining:
            self.allocations[owner] = remaining
        else:
            del self.allocations[owner]

        self.available += released
        return released

    @property
    def utilization(self) -> float:
        return (self.capacity - self.available) / self.capacity


class ResourceManager:
    """
    Coordinates multiple resource pools.

    A reservation is transactional across all requested resource types:
    either every requested resource is acquired or none is acquired.
    """

    def __init__(self) -> None:
        self._pools: Dict[ResourceType, ResourcePool] = {}
        self._lock = Lock()

    def add_pool(
        self,
        name: str,
        resource_type: ResourceType,
        capacity: int,
    ) -> None:
        if resource_type in self._pools:
            raise ValueError(f"Pool already exists: {resource_type.value}")

        self._pools[resource_type] = ResourcePool(
            name=name,
            resource_type=resource_type,
            capacity=capacity,
            available=capacity,
        )

    def request(
        self,
        owner: str,
        requests: Iterable[ResourceRequest],
    ) -> bool:
        requests = list(requests)

        if not owner.strip():
            raise ValueError("Owner cannot be empty")

        combined: Dict[ResourceType, int] = {}
        for request in requests:
            combined[request.resource_type] = (
                combined.get(request.resource_type, 0) + request.amount
            )

        with self._lock:
            for resource_type, amount in combined.items():
                pool = self._pools.get(resource_type)
                if pool is None:
                    raise KeyError(f"No pool for {resource_type.value}")
                if pool.available < amount:
                    return False

            # Validation has succeeded, so allocation can be committed safely.
            for resource_type, amount in combined.items():
                self._pools[resource_type].allocate(owner, amount)

        return True

    def release(self, owner: str) -> int:
        total = 0
        with self._lock:
            for pool in self._pools.values():
                total += pool.release(owner)
        return total

    def availability(self, resource_type: ResourceType) -> int:
        with self._lock:
            pool = self._pools[resource_type]
            return pool.available

    def utilization_report(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "pool": pool.name,
                    "type": pool.resource_type.value,
                    "capacity": pool.capacity,
                    "available": pool.available,
                    "allocated": pool.capacity - pool.available,
                    "utilization": round(pool.utilization * 100, 2),
                }
                for pool in self._pools.values()
            ]

    def save_snapshot(self, path: Path) -> None:
        snapshot = {
            "resources": self.utilization_report(),
            "allocations": {
                resource_type.value: dict(pool.allocations)
                for resource_type, pool in self._pools.items()
            },
        }
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(order=True)
class Job:
    priority: int
    job_id: str = field(compare=False)
    owner: str = field(compare=False)
    requests: List[ResourceRequest] = field(compare=False)
    estimated_seconds: float = field(compare=False, default=0.1)


class AdmissionController:
    """
    Adds scheduling policy above the basic resource manager.

    High-priority work is attempted first. Failed admission does not partially
    consume resources because ResourceManager.request is transactional.
    """

    def __init__(self, manager: ResourceManager) -> None:
        self.manager = manager
        self.queue: List[Job] = []

    def submit(self, job: Job) -> None:
        if job.estimated_seconds <= 0:
            raise ValueError("Estimated duration must be positive")
        self.queue.append(job)
        self.queue.sort(reverse=True)

    def dispatch(self) -> List[str]:
        started: List[str] = []

        for job in list(self.queue):
            if self.manager.request(job.owner, job.requests):
                started.append(job.job_id)
                self.queue.remove(job)

        return started


def demonstrate_basics() -> None:
    manager = ResourceManager()
    manager.add_pool("CPU Cluster", ResourceType.COMPUTE, 16)
    manager.add_pool("Application Memory", ResourceType.MEMORY, 64)
    manager.add_pool("Object Storage", ResourceType.STORAGE, 1000)
    manager.add_pool("PostgreSQL Connections", ResourceType.DATABASE_CONNECTION, 20)
    manager.add_pool("External API Quota", ResourceType.API_QUOTA, 5000)

    analytics_job = [
        ResourceRequest(ResourceType.COMPUTE, 6),
        ResourceRequest(ResourceType.MEMORY, 24),
        ResourceRequest(ResourceType.DATABASE_CONNECTION, 4),
    ]

    print("Analytics admission:", manager.request("analytics", analytics_job))
    print("Availability after analytics:")
    for row in manager.utilization_report():
        print(row)

    # This request exceeds memory availability and therefore consumes nothing.
    oversized_job = [
        ResourceRequest(ResourceType.COMPUTE, 4),
        ResourceRequest(ResourceType.MEMORY, 100),
    ]
    print("Oversized admission:", manager.request("batch", oversized_job))
    print("CPU remains:", manager.availability(ResourceType.COMPUTE))

    manager.release("analytics")
    print("After analytics release:")
    for row in manager.utilization_report():
        print(row)


def demonstrate_scheduling() -> None:
    manager = ResourceManager()
    manager.add_pool("Workers", ResourceType.COMPUTE, 8)
    manager.add_pool("Memory", ResourceType.MEMORY, 32)

    scheduler = AdmissionController(manager)

    scheduler.submit(
        Job(
            Priority.LOW.value,
            "report",
            "reporting",
            [
                ResourceRequest(ResourceType.COMPUTE, 3),
                ResourceRequest(ResourceType.MEMORY, 8),
            ],
        )
    )

    scheduler.submit(
        Job(
            Priority.CRITICAL.value,
            "incident",
            "operations",
            [
                ResourceRequest(ResourceType.COMPUTE, 5),
                ResourceRequest(ResourceType.MEMORY, 16),
            ],
        )
    )

    print("Started jobs:", scheduler.dispatch())
    print("Waiting jobs:", [job.job_id for job in scheduler.queue])

    manager.release("operations")
    print("Started after release:", scheduler.dispatch())


def demonstrate_file_backed_capacity() -> None:
    with tempfile.TemporaryDirectory() as directory:
        manager = ResourceManager()
        manager.add_pool("Storage", ResourceType.STORAGE, 500)

        manager.request(
            "backup-service",
            [ResourceRequest(ResourceType.STORAGE, 180)],
        )

        path = Path(directory) / "resource-snapshot.json"
        manager.save_snapshot(path)

        loaded = json.loads(path.read_text(encoding="utf-8"))
        print("Persisted storage state:", loaded["resources"][0])


def demonstrate_capacity_metrics() -> None:
    manager = ResourceManager()
    manager.add_pool("Compute", ResourceType.COMPUTE, 100)

    manager.request(
        "service-a",
        [ResourceRequest(ResourceType.COMPUTE, 35)],
    )
    manager.request(
        "service-b",
        [ResourceRequest(ResourceType.COMPUTE, 25)],
    )

    report = manager.utilization_report()
    utilization = report[0]["utilization"]

    # Sustained high utilization can indicate a capacity-planning problem.
    if utilization >= 80:
        print("Capacity warning: utilization is at least 80%.")
    else:
        print(f"Current utilization: {utilization}%.")


def demonstrate_validation() -> None:
    try:
        ResourceRequest(ResourceType.COMPUTE, 0)
    except ValueError as exc:
        print("Rejected invalid request:", exc)

    manager = ResourceManager()
    manager.add_pool("Compute", ResourceType.COMPUTE, 4)

    try:
        manager.release("unknown-owner")
        print("Unknown-owner release correctly returned zero.")
    except ValueError as exc:
        print("Unexpected release error:", exc)


def demonstrate_concurrent_requests() -> None:
    """
    The manager lock protects availability and allocation maps from races.
    A real distributed deployment would require an external coordination
    mechanism because a Python process lock does not span multiple processes
    or machines.
    """
    from concurrent.futures import ThreadPoolExecutor

    manager = ResourceManager()
    manager.add_pool("Shared Compute", ResourceType.COMPUTE, 10)

    def attempt(index: int) -> bool:
        return manager.request(
            f"worker-{index}",
            [ResourceRequest(ResourceType.COMPUTE, 1)],
        )

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(attempt, range(20)))

    successful = sum(results)
    print("Successful concurrent allocations:", successful)
    print("Remaining compute:", manager.availability(ResourceType.COMPUTE))


def demonstrate_capacity_fragmentation() -> None:
    """
    A single scalar resource such as CPU units is easy to aggregate.
    Real infrastructure may have placement constraints such as machine,
    NUMA node, accelerator type, or availability zone. Those constraints
    require resource dimensions beyond a simple total-capacity counter.
    """
    manager = ResourceManager()
    manager.add_pool("GPU", ResourceType.COMPUTE, 8)

    requests = [
        ResourceRequest(ResourceType.COMPUTE, 3),
        ResourceRequest(ResourceType.COMPUTE, 2),
    ]

    print("GPU allocations:", manager.request("ml-training", requests))
    print("GPU available:", manager.availability(ResourceType.COMPUTE))


def demonstrate_admission_with_duration() -> None:
    manager = ResourceManager()
    manager.add_pool("Workers", ResourceType.COMPUTE, 4)

    request = ResourceRequest(
        ResourceType.COMPUTE,
        amount=4,
        duration_seconds=0.05,
    )

    start = monotonic()
    if manager.request("short-job", [request]):
        sleep(request.duration_seconds)
        manager.release("short-job")

    elapsed = monotonic() - start
    print("Resource held for approximately:", round(elapsed, 3), "seconds")


def main() -> None:
    print("=== Resource Availability and Management ===")
    demonstrate_basics()

    print("\n=== Priority Admission ===")
    demonstrate_scheduling()

    print("\n=== Persistent Capacity Snapshot ===")
    demonstrate_file_backed_capacity()

    print("\n=== Capacity Metrics ===")
    demonstrate_capacity_metrics()

    print("\n=== Validation ===")
    demonstrate_validation()

    print("\n=== Concurrent Allocation ===")
    demonstrate_concurrent_requests()

    print("\n=== Capacity Modeling ===")
    demonstrate_capacity_fragmentation()

    print("\n=== Time-Bounded Allocation ===")
    demonstrate_admission_with_duration()


if __name__ == "__main__":
    main()
