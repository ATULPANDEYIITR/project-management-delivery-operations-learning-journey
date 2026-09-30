/**
 * Scope Review: Reviewing Scope Management
 *
 * This implementation models scope review as an event-driven workflow.
 * It focuses on the relationship between:
 *
 *   approved scope -> proposed change -> scope analysis -> findings
 *   -> change-control decision -> audit event
 *
 * The implementation intentionally does not treat a technically valid
 * implementation as automatically being within the approved scope.
 *
 * Runtime: Node.js 18+
 */

"use strict";

const ScopeStatus = Object.freeze({
  IN_SCOPE: "in_scope",
  PARTIALLY_IN_SCOPE: "partially_in_scope",
  OUT_OF_SCOPE: "out_of_scope",
  REQUIRES_CHANGE_CONTROL: "requires_change_control",
});

const FindingSeverity = Object.freeze({
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical",
});

const ReviewDecision = Object.freeze({
  ACCEPT: "accept",
  ACCEPT_WITH_NOTES: "accept_with_notes",
  REVISE_SCOPE: "revise_scope",
  REJECT: "reject",
});

class ScopeValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ScopeValidationError";
  }
}

class ScopeBaseline {
  constructor({
    repository,
    version,
    objective,
    items,
    exclusions = [],
    assumptions = [],
  }) {
    this.repository = repository;
    this.version = version;
    this.objective = objective;
    this.items = new Map(items.map((item) => [item.id, Object.freeze(item)]));
    this.exclusions = [...exclusions];
    this.assumptions = [...assumptions];
    this.approvedAt = new Date();

    this.validate();
  }

  validate() {
    if (!this.repository?.trim()) {
      throw new ScopeValidationError("Repository is required.");
    }

    if (!this.version?.trim()) {
      throw new ScopeValidationError("Scope version is required.");
    }

    if (!this.objective?.trim()) {
      throw new ScopeValidationError("Scope objective is required.");
    }

    if (this.items.size === 0) {
      throw new ScopeValidationError(
        "At least one approved scope item is required."
      );
    }

    for (const [id, item] of this.items) {
      if (id !== item.id) {
        throw new ScopeValidationError(
          `Scope map key '${id}' does not match item ID '${item.id}'.`
        );
      }

      if (!item.name?.trim() || !item.description?.trim()) {
        throw new ScopeValidationError(
          `Scope item '${id}' is missing required descriptive data.`
        );
      }

      if (!Array.isArray(item.acceptanceCriteria) ||
          item.acceptanceCriteria.length === 0) {
        throw new ScopeValidationError(
          `Scope item '${id}' needs acceptance criteria.`
        );
      }
    }
  }

  getItem(id) {
    return this.items.get(id);
  }

  isApproved(id) {
    const item = this.getItem(id);
    return Boolean(item && !item.excluded);
  }
}

class ScopeReviewEngine {
  constructor(baseline) {
    this.baseline = baseline;
    this.listeners = new Set();
    this.auditEvents = [];
    this.reviews = new Map();
  }

  on(listener) {
    if (typeof listener !== "function") {
      throw new TypeError("Scope review listener must be a function.");
    }

    this.listeners.add(listener);

    return () => this.listeners.delete(listener);
  }

  emit(eventName, payload) {
    const event = {
      eventName,
      timestamp: new Date().toISOString(),
      payload,
    };

    this.auditEvents.push(event);

    for (const listener of this.listeners) {
      listener(event);
    }
  }

  createFinding({
    requestId,
    severity,
    subject,
    description,
    affectedItems = [],
    recommendation,
  }) {
    return {
      id: `F-${requestId}-${this.auditEvents.length + 1}`,
      severity,
      subject,
      description,
      affectedItems,
      recommendation,
      resolved: false,
    };
  }

  classify(request) {
    this.validateRequest(request);

    const findings = [];
    const matchedItems = [];
    const unmatchedReferences = [];

    for (const scopeId of request.relatedScopeItems) {
      const item = this.baseline.getItem(scopeId);

      if (!item) {
        unmatchedReferences.push(scopeId);

        findings.push(
          this.createFinding({
            requestId: request.id,
            severity: FindingSeverity.MEDIUM,
            subject: "Unknown scope reference",
            description:
              `The request references '${scopeId}', which is not present ` +
              "in the approved baseline.",
            recommendation:
              "Map the request to an approved item or initiate scope change control.",
          })
        );

        continue;
      }

      if (item.excluded) {
        unmatchedReferences.push(scopeId);

        findings.push(
          this.createFinding({
            requestId: request.id,
            severity: FindingSeverity.HIGH,
            subject: "Excluded scope item",
            description:
              `The request references '${scopeId}', but that item is ` +
              "explicitly excluded from this release.",
            affectedItems: [scopeId],
            recommendation:
              "Do not treat the work as baseline scope without changing the approved baseline.",
          })
        );

        continue;
      }

      matchedItems.push(scopeId);
    }

    if (request.relatedScopeItems.length === 0) {
      findings.push(
        this.createFinding({
          requestId: request.id,
          severity: FindingSeverity.HIGH,
          subject: "Unmapped change",
          description:
            "The proposed work is not linked to any approved scope item.",
          recommendation:
            "Create a formal scope item or remove the unapproved work.",
        })
      );
    }

    const expansionPatterns = [
      { pattern: /\bnew\b/i, label: "new functionality" },
      { pattern: /\bredesign\b/i, label: "redesign" },
      { pattern: /\bmigration\b/i, label: "migration" },
      { pattern: /\bunrelated\b/i, label: "unrelated work" },
      { pattern: /\breplace\b/i, label: "replacement work" },
      { pattern: /\badditional\b/i, label: "additional functionality" },
    ];

    const expansionSignals = expansionPatterns
      .filter(({ pattern }) => pattern.test(request.description))
      .map(({ label }) => label);

    if (expansionSignals.length > 0) {
      findings.push(
        this.createFinding({
          requestId: request.id,
          severity: FindingSeverity.MEDIUM,
          subject: "Potential scope expansion",
          description:
            `The request contains scope-expansion indicators: ` +
            expansionSignals.join(", ") +
            ".",
          affectedItems: matchedItems,
          recommendation:
            "Compare the requested behavior with the baseline acceptance criteria before treating it as in scope.",
        })
      );
    }

    if (request.estimatedHours > 16) {
      findings.push(
        this.createFinding({
          requestId: request.id,
          severity: FindingSeverity.MEDIUM,
          subject: "Material effort delta",
          description:
            `The request estimates ${request.estimatedHours} hours, ` +
            "which may represent a material change from the approved delivery boundary.",
          affectedItems: matchedItems,
          recommendation:
            "Validate the effort against the baseline and process the change through scope governance when necessary.",
        })
      );
    }

    let status;

    if (
      matchedItems.length > 0 &&
      unmatchedReferences.length === 0 &&
      expansionSignals.length === 0
    ) {
      status = ScopeStatus.IN_SCOPE;
    } else if (matchedItems.length > 0) {
      status = ScopeStatus.PARTIALLY_IN_SCOPE;
    } else {
      status = ScopeStatus.OUT_OF_SCOPE;
    }

    if (
      status !== ScopeStatus.IN_SCOPE ||
      request.estimatedHours > 16
    ) {
      status = ScopeStatus.REQUIRES_CHANGE_CONTROL;
    }

    const review = {
      request,
      status,
      findings,
      matchedItems,
      unmatchedReferences,
      estimatedScopeDeltaHours: request.estimatedHours,
      decision: null,
      reviewer: null,
      reviewedAt: null,
    };

    this.reviews.set(request.id, review);

    this.emit("scope.reviewed", {
      requestId: request.id,
      status,
      findingCount: findings.length,
    });

    return review;
  }

  resolveFinding(reviewId, findingId) {
    const review = this.reviews.get(reviewId);

    if (!review) {
      throw new ScopeValidationError(`Unknown review '${reviewId}'.`);
    }

    const finding = review.findings.find((item) => item.id === findingId);

    if (!finding) {
      throw new ScopeValidationError(`Unknown finding '${findingId}'.`);
    }

    finding.resolved = true;

    this.emit("scope.finding_resolved", {
      reviewId,
      findingId,
    });
  }

  finalize(reviewId, reviewer, decision) {
    const review = this.reviews.get(reviewId);

    if (!review) {
      throw new ScopeValidationError(`Unknown review '${reviewId}'.`);
    }

    if (!reviewer?.trim()) {
      throw new ScopeValidationError("Reviewer is required.");
    }

    if (!Object.values(ReviewDecision).includes(decision)) {
      throw new ScopeValidationError(`Unsupported decision '${decision}'.`);
    }

    const unresolved = review.findings.filter((finding) => !finding.resolved);

    if (
      decision === ReviewDecision.ACCEPT &&
      unresolved.length > 0
    ) {
      throw new ScopeValidationError(
        "A review with unresolved scope findings cannot be accepted."
      );
    }

    review.reviewer = reviewer;
    review.decision = decision;
    review.reviewedAt = new Date().toISOString();

    this.emit("scope.decision_recorded", {
      reviewId,
      decision,
      reviewer,
    });

    return review;
  }

  validateRequest(request) {
    if (!request?.id?.trim()) {
      throw new ScopeValidationError("Change request ID is required.");
    }

    if (!request.title?.trim()) {
      throw new ScopeValidationError("Change request title is required.");
    }

    if (!request.description?.trim()) {
      throw new ScopeValidationError(
        "Change request description is required."
      );
    }

    if (!request.requestedBy?.trim()) {
      throw new ScopeValidationError("Requester identity is required.");
    }

    if (!Array.isArray(request.relatedScopeItems)) {
      throw new ScopeValidationError(
        "relatedScopeItems must be an array."
      );
    }

    if (
      !Number.isFinite(request.estimatedHours) ||
      request.estimatedHours < 0
    ) {
      throw new ScopeValidationError(
        "estimatedHours must be a non-negative finite number."
      );
    }
  }

  buildReport() {
    const reviews = [...this.reviews.values()];

    const statusCounts = reviews.reduce((counts, review) => {
      counts[review.status] = (counts[review.status] || 0) + 1;
      return counts;
    }, {});

    const totalEstimatedHours = reviews.reduce(
      (sum, review) => sum + review.estimatedScopeDeltaHours,
      0
    );

    return {
      repository: this.baseline.repository,
      baselineVersion: this.baseline.version,
      reviewCount: reviews.length,
      statusCounts,
      totalEstimatedHours,
      auditEventCount: this.auditEvents.length,
    };
  }
}

function createBaseline() {
  return new ScopeBaseline({
    repository: "release-governance-portal",
    version: "2.3",
    objective:
      "Control release scope through a traceable baseline and formal scope review.",
    items: [
      {
        id: "SCOPE-101",
        name: "Release scope dashboard",
        description:
          "Display approved release items and their implementation state.",
        acceptanceCriteria: [
          "Approved scope items are visible.",
          "Items retain stable identifiers.",
          "Reviewers can inspect scope state.",
        ],
        excluded: false,
      },
      {
        id: "SCOPE-102",
        name: "Scope change register",
        description:
          "Record proposed modifications to approved release scope.",
        acceptanceCriteria: [
          "Requests have unique identifiers.",
          "Requests include business justification.",
          "Requests can be reviewed against the baseline.",
        ],
        excluded: false,
      },
      {
        id: "SCOPE-103",
        name: "Scope findings",
        description:
          "Record discrepancies discovered during scope review.",
        acceptanceCriteria: [
          "Findings identify the affected scope.",
          "Findings have severity.",
          "Findings have resolution guidance.",
        ],
        excluded: false,
      },
      {
        id: "SCOPE-104",
        name: "Mobile redesign",
        description:
          "Full mobile interface redesign for a later release.",
        acceptanceCriteria: [
          "No mobile redesign is delivered in this release.",
        ],
        excluded: true,
      },
    ],
    exclusions: [
      "Full mobile redesign",
      "External billing migration",
      "Unrelated analytics platform replacement",
    ],
    assumptions: [
      "Existing authentication remains unchanged.",
      "The release remains within the approved governance boundary.",
    ],
  });
}

function displayReview(review) {
  console.log("\nScope Review");
  console.log("------------");
  console.log(`Request: ${review.request.id}`);
  console.log(`Title: ${review.request.title}`);
  console.log(`Status: ${review.status}`);
  console.log(
    `Matched scope: ${review.matchedItems.join(", ") || "none"}`
  );
  console.log(
    `Unmatched references: ${
      review.unmatchedReferences.join(", ") || "none"
    }`
  );
  console.log(`Estimated delta: ${review.estimatedScopeDeltaHours} hours`);

  for (const finding of review.findings) {
    console.log(
      `[${finding.severity.toUpperCase()}] ${finding.subject}`
    );
    console.log(`  ${finding.description}`);
    console.log(`  Action: ${finding.recommendation}`);
  }
}

function main() {
  const baseline = createBaseline();
  const engine = new ScopeReviewEngine(baseline);

  // Event-driven behavior makes every scope-review transition observable.
  engine.on((event) => {
    console.log(
      `[AUDIT] ${event.timestamp} ${event.eventName}`,
      JSON.stringify(event.payload)
    );
  });

  const requests = [
    {
      id: "CR-301",
      title: "Improve scope dashboard filtering",
      description:
        "Add filtering to the existing scope dashboard so reviewers can isolate high-priority items.",
      requestedBy: "release-manager",
      relatedScopeItems: ["SCOPE-101"],
      estimatedHours: 6,
      businessJustification:
        "Reviewers need to inspect high-priority scope efficiently.",
    },
    {
      id: "CR-302",
      title: "Add mobile redesign",
      description:
        "Add a new mobile interface and redesign the existing mobile workflow.",
      requestedBy: "product-team",
      relatedScopeItems: ["SCOPE-101", "SCOPE-104"],
      estimatedHours: 24,
      businessJustification:
        "Improve mobile usability before release.",
    },
    {
      id: "CR-303",
      title: "Introduce external billing",
      description:
        "Add a new external billing integration to the release.",
      requestedBy: "commercial-team",
      relatedScopeItems: [],
      estimatedHours: 20,
      businessJustification:
        "Support a future commercial workflow.",
    },
  ];

  const reviews = requests.map((request) => {
    const review = engine.classify(request);
    displayReview(review);
    return review;
  });

  // A low-risk request is accepted only after its review findings are handled.
  for (const finding of reviews[0].findings) {
    engine.resolveFinding(reviews[0].request.id, finding.id);
  }

  engine.finalize(
    reviews[0].request.id,
    "scope-controller",
    ReviewDecision.ACCEPT
  );

  engine.finalize(
    reviews[1].request.id,
    "scope-controller",
    ReviewDecision.REVISE_SCOPE
  );

  engine.finalize(
    reviews[2].request.id,
    "scope-controller",
    ReviewDecision.REJECT
  );

  console.log("\nGovernance Report");
  console.log("-----------------");
  console.log(JSON.stringify(engine.buildReport(), null, 2));

  console.log("\nFailure-condition demonstration");

  try {
    engine.classify({
      id: "CR-INVALID",
      title: "Invalid request",
      description: "Invalid effort value.",
      requestedBy: "tester",
      relatedScopeItems: ["SCOPE-101"],
      estimatedHours: -5,
      businessJustification: "Validation test.",
    });
  } catch (error) {
    console.log(
      `Validation correctly rejected the request: ${error.message}`
    );
  }
}

main();
