from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4


# ============================================================
# PROJECT DOCUMENTATION MANAGEMENT SYSTEM
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("project_documentation")


# ============================================================
# ENUMERATIONS
# ============================================================

class DocumentType(Enum):
    REQUIREMENTS = "requirements"
    PROJECT_PLAN = "project_plan"
    TECHNICAL_SPECIFICATION = "technical_specification"
    DESIGN = "design"
    MEETING_MINUTES = "meeting_minutes"
    PROGRESS_REPORT = "progress_report"
    RISK_REGISTER = "risk_register"
    TEST_REPORT = "test_report"
    USER_GUIDE = "user_guide"
    CLOSURE_REPORT = "closure_report"


class DocumentStatus(Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class UserRole(Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    AUTHOR = "author"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class ReviewDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


# ============================================================
# EXCEPTIONS
# ============================================================

class DocumentationError(Exception):
    pass


class ValidationError(DocumentationError):
    pass


class PermissionError(DocumentationError):
    pass


class DocumentNotFoundError(DocumentationError):
    pass


class InvalidTransitionError(DocumentationError):
    pass


class VersionConflictError(DocumentationError):
    pass


# ============================================================
# DOMAIN MODELS
# ============================================================

@dataclass(frozen=True)
class User:
    user_id: UUID
    name: str
    email: str
    role: UserRole
    active: bool = True


@dataclass
class DocumentVersion:
    version_id: UUID
    version_number: int
    content: str
    checksum: str
    author_id: UUID
    created_at: datetime
    change_description: str


@dataclass
class Review:
    review_id: UUID
    reviewer_id: UUID
    version_number: int
    decision: ReviewDecision
    comments: str
    created_at: datetime


@dataclass
class ProjectDocument:
    document_id: UUID
    project_id: UUID
    title: str
    document_type: DocumentType
    owner_id: UUID
    status: DocumentStatus
    current_version: int
    versions: list[DocumentVersion] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class AuditEvent:
    event_id: UUID
    document_id: UUID
    actor_id: UUID
    action: str
    details: dict
    timestamp: datetime


# ============================================================
# DOCUMENT MANAGEMENT SERVICE
# ============================================================

class ProjectDocumentationManager:

    ALLOWED_TRANSITIONS = {
        DocumentStatus.DRAFT: {
            DocumentStatus.UNDER_REVIEW,
            DocumentStatus.ARCHIVED
        },
        DocumentStatus.UNDER_REVIEW: {
            DocumentStatus.DRAFT,
            DocumentStatus.APPROVED,
            DocumentStatus.REJECTED
        },
        DocumentStatus.APPROVED: {
            DocumentStatus.DRAFT,
            DocumentStatus.ARCHIVED
        },
        DocumentStatus.REJECTED: {
            DocumentStatus.DRAFT,
            DocumentStatus.ARCHIVED
        },
        DocumentStatus.ARCHIVED: set()
    }

    def __init__(self):
        self.users: dict[UUID, User] = {}
        self.documents: dict[UUID, ProjectDocument] = {}
        self.audit_log: list[AuditEvent] = []
        self.projects: set[UUID] = set()

    # --------------------------------------------------------
    # USER MANAGEMENT
    # --------------------------------------------------------

    def register_user(
        self,
        name: str,
        email: str,
        role: UserRole
    ) -> User:

        if not name.strip():
            raise ValidationError("User name cannot be empty.")

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        ):
            raise ValidationError("Invalid email address.")

        if any(
            user.email.lower() == email.lower()
            for user in self.users.values()
        ):
            raise ValidationError("Email already registered.")

        user = User(
            user_id=uuid4(),
            name=name.strip(),
            email=email.lower(),
            role=role
        )

        self.users[user.user_id] = user
        return user

    def _get_user(self, user_id: UUID) -> User:

        user = self.users.get(user_id)

        if user is None:
            raise PermissionError("Unknown user.")

        if not user.active:
            raise PermissionError("User account is inactive.")

        return user

    def _authorize(
        self,
        user_id: UUID,
        allowed_roles: set[UserRole]
    ) -> User:

        user = self._get_user(user_id)

        if user.role not in allowed_roles:
            raise PermissionError(
                f"Role {user.role.value} is not authorized."
            )

        return user

    # --------------------------------------------------------
    # AUDIT MANAGEMENT
    # --------------------------------------------------------

    def _audit(
        self,
        document_id: UUID,
        actor_id: UUID,
        action: str,
        details: Optional[dict] = None
    ):

        self.audit_log.append(
            AuditEvent(
                event_id=uuid4(),
                document_id=document_id,
                actor_id=actor_id,
                action=action,
                details=details or {},
                timestamp=datetime.now(timezone.utc)
            )
        )

    # --------------------------------------------------------
    # PROJECT MANAGEMENT
    # --------------------------------------------------------

    def create_project(self, actor_id: UUID) -> UUID:

        self._authorize(
            actor_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER}
        )

        project_id = uuid4()
        self.projects.add(project_id)

        return project_id

    # --------------------------------------------------------
    # DOCUMENT VALIDATION
    # --------------------------------------------------------

    @staticmethod
    def _validate_document(
        title: str,
        content: str
    ):

        if not title.strip():
            raise ValidationError("Document title is required.")

        if len(title) > 200:
            raise ValidationError("Document title is too long.")

        if not content.strip():
            raise ValidationError("Document content is required.")

        if len(content.encode("utf-8")) > 5_000_000:
            raise ValidationError("Document exceeds the 5 MB limit.")

    @staticmethod
    def _checksum(content: str) -> str:

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    # --------------------------------------------------------
    # DOCUMENT CREATION
    # --------------------------------------------------------

    def create_document(
        self,
        actor_id: UUID,
        project_id: UUID,
        title: str,
        document_type: DocumentType,
        content: str,
        tags: Optional[set[str]] = None
    ) -> ProjectDocument:

        actor = self._authorize(
            actor_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.AUTHOR}
        )

        if project_id not in self.projects:
            raise ValidationError("Project does not exist.")

        self._validate_document(title, content)

        version = DocumentVersion(
            version_id=uuid4(),
            version_number=1,
            content=content,
            checksum=self._checksum(content),
            author_id=actor_id,
            created_at=datetime.now(timezone.utc),
            change_description="Initial document creation"
        )

        document = ProjectDocument(
            document_id=uuid4(),
            project_id=project_id,
            title=title.strip(),
            document_type=document_type,
            owner_id=actor_id,
            status=DocumentStatus.DRAFT,
            current_version=1,
            versions=[version],
            tags={
                tag.strip().lower()
                for tag in (tags or set())
                if tag.strip()
            }
        )

        self.documents[document.document_id] = document

        self._audit(
            document.document_id,
            actor_id,
            "DOCUMENT_CREATED",
            {"version": 1, "title": title}
        )

        return document

    # --------------------------------------------------------
    # DOCUMENT RETRIEVAL
    # --------------------------------------------------------

    def get_document(
        self,
        document_id: UUID,
        actor_id: UUID
    ) -> ProjectDocument:

        self._get_user(actor_id)

        document = self.documents.get(document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found.")

        self._audit(
            document_id,
            actor_id,
            "DOCUMENT_ACCESSED"
        )

        return document

    def list_documents(
        self,
        project_id: UUID,
        actor_id: UUID,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None
    ) -> list[ProjectDocument]:

        self._get_user(actor_id)

        if project_id not in self.projects:
            raise ValidationError("Project does not exist.")

        results = [
            document
            for document in self.documents.values()
            if document.project_id == project_id
            and (
                document_type is None
                or document.document_type == document_type
            )
            and (
                status is None
                or document.status == status
            )
        ]

        return sorted(
            results,
            key=lambda document: document.updated_at,
            reverse=True
        )

    # --------------------------------------------------------
    # DOCUMENT VERSIONING
    # --------------------------------------------------------

    def update_document(
        self,
        document_id: UUID,
        actor_id: UUID,
        content: str,
        change_description: str,
        expected_version: int
    ) -> DocumentVersion:

        actor = self._authorize(
            actor_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.AUTHOR}
        )

        document = self.get_document(document_id, actor_id)

        if actor.role == UserRole.AUTHOR and document.owner_id != actor_id:
            raise PermissionError(
                "Authors can modify only documents they own."
            )

        if document.status == DocumentStatus.ARCHIVED:
            raise InvalidTransitionError(
                "Archived documents cannot be modified."
            )

        if document.current_version != expected_version:
            raise VersionConflictError(
                "Document was modified by another user."
            )

        self._validate_document(document.title, content)

        next_version = document.current_version + 1

        version = DocumentVersion(
            version_id=uuid4(),
            version_number=next_version,
            content=content,
            checksum=self._checksum(content),
            author_id=actor_id,
            created_at=datetime.now(timezone.utc),
            change_description=change_description.strip()
        )

        document.versions.append(version)
        document.current_version = next_version

        # A changed document must undergo review again.
        if document.status in {
            DocumentStatus.APPROVED,
            DocumentStatus.REJECTED,
            DocumentStatus.UNDER_REVIEW
        }:
            document.status = DocumentStatus.DRAFT

        document.updated_at = datetime.now(timezone.utc)

        self._audit(
            document_id,
            actor_id,
            "DOCUMENT_VERSION_CREATED",
            {"version": next_version}
        )

        return version

    # --------------------------------------------------------
    # REVIEW WORKFLOW
    # --------------------------------------------------------

    def submit_for_review(
        self,
        document_id: UUID,
        actor_id: UUID
    ):

        document = self.get_document(document_id, actor_id)

        if actor_id != document.owner_id:
            self._authorize(
                actor_id,
                {UserRole.ADMIN, UserRole.PROJECT_MANAGER}
            )

        if document.status != DocumentStatus.DRAFT:
            raise InvalidTransitionError(
                "Only draft documents can be submitted."
            )

        document.status = DocumentStatus.UNDER_REVIEW
        document.updated_at = datetime.now(timezone.utc)

        self._audit(
            document_id,
            actor_id,
            "SUBMITTED_FOR_REVIEW"
        )

    def review_document(
        self,
        document_id: UUID,
        reviewer_id: UUID,
        decision: ReviewDecision,
        comments: str
    ) -> Review:

        self._authorize(
            reviewer_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER}
        )

        document = self.documents.get(document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found.")

        if document.status != DocumentStatus.UNDER_REVIEW:
            raise InvalidTransitionError(
                "Document is not awaiting review."
            )

        if reviewer_id == document.owner_id:
            raise PermissionError(
                "Document owners cannot approve their own documents."
            )

        if not comments.strip():
            raise ValidationError(
                "Review comments are required."
            )

        review = Review(
            review_id=uuid4(),
            reviewer_id=reviewer_id,
            version_number=document.current_version,
            decision=decision,
            comments=comments.strip(),
            created_at=datetime.now(timezone.utc)
        )

        document.reviews.append(review)

        if decision == ReviewDecision.APPROVED:
            document.status = DocumentStatus.APPROVED

        elif decision == ReviewDecision.REJECTED:
            document.status = DocumentStatus.REJECTED

        elif decision == ReviewDecision.CHANGES_REQUESTED:
            document.status = DocumentStatus.DRAFT

        document.updated_at = datetime.now(timezone.utc)

        self._audit(
            document_id,
            reviewer_id,
            "DOCUMENT_REVIEWED",
            {
                "decision": decision.value,
                "version": document.current_version
            }
        )

        return review

    # --------------------------------------------------------
    # DOCUMENT ARCHIVING
    # --------------------------------------------------------

    def archive_document(
        self,
        document_id: UUID,
        actor_id: UUID
    ):

        self._authorize(
            actor_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER}
        )

        document = self.documents.get(document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found.")

        if document.status == DocumentStatus.UNDER_REVIEW:
            raise InvalidTransitionError(
                "Documents under review cannot be archived."
            )

        if document.status == DocumentStatus.ARCHIVED:
            raise InvalidTransitionError(
                "Document is already archived."
            )

        document.status = DocumentStatus.ARCHIVED
        document.updated_at = datetime.now(timezone.utc)

        self._audit(
            document_id,
            actor_id,
            "DOCUMENT_ARCHIVED"
        )

    # --------------------------------------------------------
    # DOCUMENT SEARCH
    # --------------------------------------------------------

    def search_documents(
        self,
        project_id: UUID,
        actor_id: UUID,
        keyword: str
    ) -> list[ProjectDocument]:

        self._get_user(actor_id)

        keyword = keyword.strip().lower()

        if not keyword:
            raise ValidationError("Search keyword is required.")

        results = []

        for document in self.documents.values():

            if document.project_id != project_id:
                continue

            latest = document.versions[-1]

            searchable = (
                document.title.lower()
                + " "
                + latest.content.lower()
                + " "
                + " ".join(document.tags)
            )

            if keyword in searchable:
                results.append(document)

        return results

    # --------------------------------------------------------
    # FILE EXPORT
    # --------------------------------------------------------

    def export_document(
        self,
        document_id: UUID,
        actor_id: UUID,
        destination: Path
    ) -> Path:

        document = self.get_document(document_id, actor_id)
        version = document.versions[-1]

        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file before replacing the destination.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            delete=False
        ) as temporary:

            json.dump(
                {
                    "document_id": str(document.document_id),
                    "project_id": str(document.project_id),
                    "title": document.title,
                    "type": document.document_type.value,
                    "status": document.status.value,
                    "version": version.version_number,
                    "checksum": version.checksum,
                    "content": version.content,
                    "exported_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                },
                temporary,
                indent=2
            )

            temporary_path = Path(temporary.name)

        temporary_path.replace(destination)

        self._audit(
            document_id,
            actor_id,
            "DOCUMENT_EXPORTED",
            {"destination_name": destination.name}
        )

        return destination

    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    def generate_project_report(
        self,
        project_id: UUID,
        actor_id: UUID
    ) -> dict:

        documents = self.list_documents(
            project_id,
            actor_id
        )

        status_counts = {
            status.value: 0
            for status in DocumentStatus
        }

        type_counts = {
            document_type.value: 0
            for document_type in DocumentType
        }

        for document in documents:
            status_counts[document.status.value] += 1
            type_counts[document.document_type.value] += 1

        return {
            "project_id": str(project_id),
            "total_documents": len(documents),
            "status_distribution": status_counts,
            "document_type_distribution": type_counts,
            "total_versions": sum(
                len(document.versions)
                for document in documents
            ),
            "pending_reviews": status_counts[
                DocumentStatus.UNDER_REVIEW.value
            ]
        }

    # --------------------------------------------------------
    # AUDIT REPORT
    # --------------------------------------------------------

    def get_audit_history(
        self,
        document_id: UUID,
        actor_id: UUID
    ) -> list[AuditEvent]:

        self._authorize(
            actor_id,
            {UserRole.ADMIN, UserRole.PROJECT_MANAGER}
        )

        return [
            event
            for event in self.audit_log
            if event.document_id == document_id
        ]


# ============================================================
# EXECUTABLE DEMONSTRATION AND TESTS
# ============================================================

def run_demonstration():

    manager = ProjectDocumentationManager()

    admin = manager.register_user(
        "Project Administrator",
        "admin@example.com",
        UserRole.ADMIN
    )

    author = manager.register_user(
        "Technical Author",
        "author@example.com",
        UserRole.AUTHOR
    )

    reviewer = manager.register_user(
        "Technical Reviewer",
        "reviewer@example.com",
        UserRole.REVIEWER
    )

    project_id = manager.create_project(admin.user_id)

    document = manager.create_document(
        actor_id=author.user_id,
        project_id=project_id,
        title="Project Technical Requirements",
        document_type=DocumentType.REQUIREMENTS,
        content=(
            "The project shall provide secure authentication, "
            "document versioning, audit logging and reporting."
        ),
        tags={"requirements", "security", "documentation"}
    )

    assert document.current_version == 1
    assert document.status == DocumentStatus.DRAFT

    # Create a second version.
    manager.update_document(
        document_id=document.document_id,
        actor_id=author.user_id,
        content=(
            "The project shall provide secure authentication, "
            "document versioning, audit logging, reporting "
            "and controlled document access."
        ),
        change_description="Added access control requirements.",
        expected_version=1
    )

    assert document.current_version == 2

    manager.submit_for_review(
        document.document_id,
        author.user_id
    )

    review = manager.review_document(
        document.document_id,
        reviewer.user_id,
        ReviewDecision.APPROVED,
        "Requirements are complete and technically consistent."
    )

    assert review.version_number == 2
    assert document.status == DocumentStatus.APPROVED

    # Search documents.
    search_results = manager.search_documents(
        project_id,
        author.user_id,
        "authentication"
    )

    assert len(search_results) == 1

    # Verify optimistic version conflict handling.
    try:
        manager.update_document(
            document.document_id,
            author.user_id,
            "An outdated document update.",
            "Testing version conflict.",
            expected_version=1
        )
    except VersionConflictError as error:
        logger.info("Expected version conflict: %s", error)

    # Export the document.
    with tempfile.TemporaryDirectory() as directory:

        export_path = Path(directory) / "requirements.json"

        manager.export_document(
            document.document_id,
            author.user_id,
            export_path
        )

        assert export_path.exists()

        exported = json.loads(
            export_path.read_text(encoding="utf-8")
        )

        assert exported["version"] == 2

    # Generate project report.
    report = manager.generate_project_report(
        project_id,
        admin.user_id
    )

    print("\nPROJECT DOCUMENTATION REPORT")
    print(json.dumps(report, indent=2))

    print("\nAUDIT HISTORY")

    for event in manager.get_audit_history(
        document.document_id,
        admin.user_id
    ):
        print(
            event.timestamp.isoformat(),
            event.action,
            event.details
        )

    # Verify self-approval restriction.
    second_document = manager.create_document(
        author.user_id,
        project_id,
        "Project Design",
        DocumentType.DESIGN,
        "The system uses a modular architecture."
    )

    manager.submit_for_review(
        second_document.document_id,
        author.user_id
    )

    try:
        manager.review_document(
            second_document.document_id,
            author.user_id,
            ReviewDecision.APPROVED,
            "Self-approval attempt."
        )
    except PermissionError as error:
        logger.info("Expected permission denial: %s", error)

    print("\nAll demonstration checks passed.")


if __name__ == "__main__":
    run_demonstration()
