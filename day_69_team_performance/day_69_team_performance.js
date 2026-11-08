"use strict";

/**
 * Team Performance Evaluation Platform
 *
 * Event-driven evaluation using:
 * - Weighted performance indicators
 * - Team objectives and key results
 * - Productivity and quality measurements
 * - Collaboration and reliability
 * - Historical performance
 * - Improvement action tracking
 * - Asynchronous evaluation and event reporting
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

const PerformanceBand = Object.freeze({
    EXCELLENT: "Excellent",
    STRONG: "Strong",
    SATISFACTORY: "Satisfactory",
    NEEDS_IMPROVEMENT: "Needs Improvement",
    CRITICAL: "Critical"
});

const DEFAULT_WEIGHTS = Object.freeze({
    goalAchievement: 0.25,
    productivity: 0.20,
    workQuality: 0.20,
    collaboration: 0.15,
    reliability: 0.10,
    deliveryConsistency: 0.10
});

function validateScore(value, field) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 100
    ) {
        throw new ValidationError(
            `${field} must be a finite number between 0 and 100.`
        );
    }
}

function getPerformanceBand(score) {
    validateScore(score, "Performance score");

    if (score >= 90) return PerformanceBand.EXCELLENT;
    if (score >= 80) return PerformanceBand.STRONG;
    if (score >= 70) return PerformanceBand.SATISFACTORY;
    if (score >= 60) return PerformanceBand.NEEDS_IMPROVEMENT;

    return PerformanceBand.CRITICAL;
}

class Team {

    constructor({
        id,
        name,
        department,
        members,
        manager,
        period,
        metrics
    }) {
        if (!id || !name || !department || !manager || !period) {
            throw new ValidationError("Team identity fields are required.");
        }

        if (!Number.isInteger(members) || members <= 0) {
            throw new ValidationError("Invalid team member count.");
        }

        this.id = String(id);
        this.name = name;
        this.department = department;
        this.members = members;
        this.manager = manager;
        this.period = period;
        this.metrics = Team.validateMetrics(metrics);
    }

    static validateMetrics(metrics) {
        const keys = Object.keys(DEFAULT_WEIGHTS);

        if (!metrics || typeof metrics !== "object") {
            throw new ValidationError("Metrics must be an object.");
        }

        const normalized = {};

        for (const key of keys) {
            validateScore(metrics[key], key);
            normalized[key] = metrics[key];
        }

        return Object.freeze(normalized);
    }

    updateMetrics(metrics) {
        this.metrics = Team.validateMetrics(metrics);
    }
}

class PerformancePolicy {

    constructor(weights = DEFAULT_WEIGHTS) {
        const entries = Object.entries(weights);

        if (entries.length !== Object.keys(DEFAULT_WEIGHTS).length) {
            throw new ValidationError("All performance weights are required.");
        }

        for (const [key, value] of entries) {
            if (!(key in DEFAULT_WEIGHTS)) {
                throw new ValidationError(`Unknown weight: ${key}`);
            }

            if (
                typeof value !== "number" ||
                !Number.isFinite(value) ||
                value < 0 ||
                value > 1
            ) {
                throw new ValidationError(`Invalid weight: ${key}`);
            }
        }

        const total = entries.reduce(
            (sum, [, value]) => sum + value,
            0
        );

        if (Math.abs(total - 1) > 0.000001) {
            throw new ValidationError("Weights must total 1.0.");
        }

        this.weights = Object.freeze({ ...weights });
    }

    calculate(metrics) {
        return Number(
            Object.entries(this.weights)
                .reduce(
                    (score, [key, weight]) =>
                        score + metrics[key] * weight,
                    0
                )
                .toFixed(2)
        );
    }
}

class PerformanceHistory {

    #records = new Map();

    add(teamId, score, period) {
        validateScore(score, "Historical score");

        if (!teamId || !period) {
            throw new ValidationError(
                "Team ID and period are required."
            );
        }

        const records = this.#records.get(teamId) ?? [];

        if (records.some(record => record.period === period)) {
            throw new ValidationError(
                `An evaluation already exists for ${period}.`
            );
        }

        records.push(
            Object.freeze({
                score,
                period,
                timestamp: new Date().toISOString()
            })
        );

        records.sort((a, b) => a.period.localeCompare(b.period));

        this.#records.set(teamId, records);
    }

    getPrevious(teamId, currentPeriod) {
        const records = this.#records.get(teamId) ?? [];

        return records
            .filter(record => record.period < currentPeriod)
            .at(-1) ?? null;
    }

    getTrend(teamId, currentScore, currentPeriod) {
        const previous = this.getPrevious(teamId, currentPeriod);

        if (!previous) {
            return {
                direction: "Not Available",
                change: null
            };
        }

        const change = Number(
            (currentScore - previous.score).toFixed(2)
        );

        return {
            direction:
                change > 0 ? "Improving" :
                change < 0 ? "Declining" :
                "Stable",
            change
        };
    }
}

class ImprovementTracker {

    #actions = new Map();

    createAction(teamId, metric, description, owner, dueDate) {
        if (!teamId || !owner || !description) {
            throw new ValidationError(
                "Action details are incomplete."
            );
        }

        if (!(metric in DEFAULT_WEIGHTS)) {
            throw new ValidationError("Unknown performance metric.");
        }

        if (
            !Number.isFinite(Date.parse(dueDate)) ||
            new Date(dueDate).toISOString().slice(0, 10) !== dueDate
        ) {
            throw new ValidationError("Invalid due date.");
        }

        const id = `ACTION-${this.#actions.size + 1}`;

        const action = {
            id,
            teamId,
            metric,
            description,
            owner,
            dueDate,
            status: "OPEN",
            createdAt: new Date().toISOString()
        };

        this.#actions.set(id, action);

        return { ...action };
    }

    updateStatus(actionId, status) {
        const allowed = new Set([
            "OPEN",
            "IN_PROGRESS",
            "COMPLETED",
            "CANCELLED"
        ]);

        const action = this.#actions.get(actionId);

        if (!action) {
            throw new ValidationError("Improvement action not found.");
        }

        if (!allowed.has(status)) {
            throw new ValidationError("Invalid action status.");
        }

        if (action.status === "COMPLETED" || action.status === "CANCELLED") {
            throw new ValidationError("Action is already in a terminal state.");
        }

        action.status = status;
        action.updatedAt = new Date().toISOString();

        return { ...action };
    }

    getByTeam(teamId) {
        return [...this.#actions.values()]
            .filter(action => action.teamId === teamId)
            .map(action => ({ ...action }));
    }
}

class TeamPerformanceEngine extends EventEmitter {

    constructor(policy = new PerformancePolicy()) {
        super();

        this.policy = policy;
        this.history = new PerformanceHistory();
        this.improvements = new ImprovementTracker();

        this.teams = new Map();
        this.results = new Map();
    }

    registerTeam(team) {
        if (!(team instanceof Team)) {
            throw new ValidationError("Expected a Team instance.");
        }

        if (this.teams.has(team.id)) {
            throw new ValidationError("Duplicate team ID.");
        }

        this.teams.set(team.id, team);

        this.emit("teamRegistered", {
            teamId: team.id,
            teamName: team.name
        });
    }

    evaluate(teamId) {
        const team = this.teams.get(teamId);

        if (!team) {
            throw new ValidationError("Team not found.");
        }

        const score = this.policy.calculate(team.metrics);

        const strengths = Object.entries(team.metrics)
            .filter(([, value]) => value >= 85)
            .map(([metric]) => metric);

        const improvementAreas = Object.entries(team.metrics)
            .filter(([, value]) => value < 70)
            .map(([metric]) => metric);

        const trend = this.history.getTrend(
            teamId,
            score,
            team.period
        );

        const result = Object.freeze({
            teamId,
            teamName: team.name,
            department: team.department,
            period: team.period,
            members: team.members,
            score,
            band: getPerformanceBand(score),
            strengths,
            improvementAreas,
            trend,
            evaluatedAt: new Date().toISOString()
        });

        this.results.set(teamId, result);

        this.emit("teamEvaluated", result);

        return result;
    }

    async evaluateAll() {
        // Independent team calculations are scheduled concurrently.
        const evaluations = [...this.teams.keys()].map(
            teamId => Promise.resolve().then(
                () => this.evaluate(teamId)
            )
        );

        const settled = await Promise.allSettled(evaluations);

        const successful = [];
        const failures = [];

        for (const item of settled) {
            if (item.status === "fulfilled") {
                successful.push(item.value);
            } else {
                failures.push({
                    error: item.reason.message
                });
            }
        }

        successful.sort((a, b) => b.score - a.score);

        const report = {
            generatedAt: new Date().toISOString(),
            successfulEvaluations: successful.length,
            failedEvaluations: failures.length,
            averageScore: successful.length
                ? Number((
                    successful.reduce(
                        (sum, item) => sum + item.score,
                        0
                    ) / successful.length
                ).toFixed(2))
                : 0,
            teams: successful,
            failures
        };

        this.emit("reportGenerated", report);

        return report;
    }

    recordHistoricalScore(teamId, score, period) {
        if (!this.teams.has(teamId)) {
            throw new ValidationError("Unknown team.");
        }

        this.history.add(teamId, score, period);
    }
}

class ReportExporter {

    static async exportJSON(report, filename) {
        if (!filename || path.extname(filename) !== ".json") {
            throw new ValidationError("A JSON filename is required.");
        }

        const destination = path.resolve(filename);

        const content = JSON.stringify(report, null, 2);

        await fs.mkdir(path.dirname(destination), {
            recursive: true
        });

        await fs.writeFile(destination, content, {
            encoding: "utf8",
            flag: "w",
            mode: 0o600
        });

        return destination;
    }
}

async function main() {
    const engine = new TeamPerformanceEngine();

    engine.on("teamEvaluated", result => {
        console.log(
            `[EVALUATED] ${result.teamName}: ` +
            `${result.score} (${result.band})`
        );
    });

    engine.on("reportGenerated", report => {
        console.log(
            `[REPORT] ${report.successfulEvaluations} teams evaluated.`
        );
    });

    const teams = [
        new Team({
            id: "T001",
            name: "Engineering",
            department: "Technology",
            members: 12,
            manager: "Manager A",
            period: "2026-Q4",
            metrics: {
                goalAchievement: 92,
                productivity: 88,
                workQuality: 95,
                collaboration: 85,
                reliability: 90,
                deliveryConsistency: 87
            }
        }),

        new Team({
            id: "T002",
            name: "Customer Support",
            department: "Operations",
            members: 10,
            manager: "Manager B",
            period: "2026-Q4",
            metrics: {
                goalAchievement: 78,
                productivity: 85,
                workQuality: 82,
                collaboration: 91,
                reliability: 88,
                deliveryConsistency: 80
            }
        }),

        new Team({
            id: "T003",
            name: "Research",
            department: "R&D",
            members: 8,
            manager: "Manager C",
            period: "2026-Q4",
            metrics: {
                goalAchievement: 95,
                productivity: 72,
                workQuality: 90,
                collaboration: 80,
                reliability: 75,
                deliveryConsistency: 78
            }
        })
    ];

    for (const team of teams) {
        engine.registerTeam(team);
    }

    engine.recordHistoricalScore("T001", 84, "2026-Q3");
    engine.recordHistoricalScore("T002", 82, "2026-Q3");
    engine.recordHistoricalScore("T003", 80, "2026-Q3");

    const report = await engine.evaluateAll();

    const action = engine.improvements.createAction(
        "T003",
        "productivity",
        "Improve research task estimation and workflow planning.",
        "Research Manager",
        "2026-12-15"
    );

    console.log("\nIMPROVEMENT ACTION");
    console.log(action);

    console.log("\nTEAM PERFORMANCE REPORT");
    console.table(
        report.teams.map(team => ({
            team: team.teamName,
            score: team.score,
            band: team.band,
            trend: team.trend.direction
        }))
    );

    const output = await ReportExporter.exportJSON(
        report,
        "reports/team-performance.json"
    );

    console.log(`Report exported: ${output}`);
}

main().catch(error => {
    console.error("Performance evaluation failed:", error.message);
    process.exitCode = 1;
});
