# Project Constraints: Time, Cost, Scope, Quality, and Resources

## Topic Introduction

Project constraints are the conditions that limit how a project can be planned and executed. The most important constraint dimensions covered in this study are **time, cost, scope, quality, and resources**.

A project cannot normally maximize every dimension simultaneously. A shorter schedule may require additional resources and cost. A lower budget may require a longer schedule or reduced scope. Additional scope may require more time, more money, greater capacity, or changes to quality expectations.

The Python script accompanying this README presents these relationships through executable examples, calculations, simulations, validation logic, and an integrated project case.

The central principle is:

> A project decision should be evaluated across the entire constraint system rather than against one isolated metric.

---

## 1. Fundamental Project Terminology

### Project

A project is a temporary effort undertaken to create a unique product, service, result, or outcome.

Projects generally have:

- A defined objective
- A beginning and an end
- Deliverables
- Stakeholders
- Requirements
- Constraints
- Resources
- Risks
- Acceptance conditions

### Constraint

A constraint is a limitation or condition that restricts project choices.

Examples include:

- A contractual completion date
- A maximum budget
- A minimum quality requirement
- A limited number of developers
- A required regulatory standard
- A fixed facility capacity

### Deliverable

A deliverable is a measurable output produced by project work.

Examples include:

- A software application
- A building
- A report
- A training program
- A manufacturing line
- A deployed business process

### Baseline

A baseline is an approved reference point against which project performance is measured.

Common baselines include:

- Scope baseline
- Schedule baseline
- Cost baseline

A baseline is important because actual performance has meaning only when compared with an approved reference.

### Assumption

An assumption is something considered true for planning purposes without complete verification.

Examples:

- A specialist will be available in June.
- A supplier will deliver within ten days.
- A technical dependency will be available before development begins.

Unverified assumptions can become sources of risk.

### Dependency

A dependency exists when one activity depends on another activity, decision, deliverable, or external event.

For example:

Requirements must be completed before architecture can begin.

### Milestone

A milestone is a significant project event or point in time. A milestone normally represents an event rather than a duration.

---

# 2. The Five Major Constraint Dimensions

## 2.1 Time

Time represents the temporal limitations of a project.

Time constraints include:

- Start date
- Completion date
- Milestones
- Activity durations
- Dependencies
- Release windows
- Contractual deadlines
- Resource availability periods

A project may have a fixed deadline, a target deadline, or a flexible completion date.

### Example

A project must be delivered within 90 days.

If the current forecast is 105 days, the project has a 15-day schedule problem unless another constraint or project strategy changes.

---

## 2.2 Cost

Cost represents the financial resources consumed by the project.

Typical project costs include:

- Employee labor
- Contractors
- Equipment
- Software licenses
- Cloud infrastructure
- Materials
- Facilities
- Training
- Travel
- Testing
- External services

The script distinguishes direct, indirect, fixed, variable, and opportunity costs.

### Cost Estimate vs Budget

A **cost estimate** is a forecast of expected cost.

A **budget** is an authorized financial allocation.

**Actual cost** is the amount actually spent.

These terms should not be treated as interchangeable.

---

## 2.3 Scope

Scope defines what the project is expected to deliver.

Scope includes:

- Requirements
- Features
- Functions
- Deliverables
- Work packages
- Acceptance conditions
- Explicit exclusions

A strong scope definition also identifies what is **not** part of the project.

### Scope Creep

Scope creep is uncontrolled expansion of project work without corresponding changes to schedule, cost, resources, or formal approval.

For example, a software project initially includes:

- Login
- Reporting
- User management

Later, stakeholders informally request:

- Mobile application
- Advanced analytics
- Custom themes
- Automated recommendations

If these additions are accepted without changing the plan, the project may experience schedule and cost problems.

Scope changes themselves are not inherently bad. The problem is uncontrolled change.

---

## 2.4 Quality

Quality describes the degree to which a product, service, process, or deliverable satisfies defined requirements.

Quality should ideally be measurable.

Examples include:

- Availability of 99.9%
- Response time below 500 milliseconds
- Defect rate below 2%
- Test coverage above 90%
- Accuracy above 95%
- Zero critical defects

A statement such as "the product should be high quality" is difficult to manage because it lacks measurable acceptance criteria.

---

## 2.5 Resources

Resources are the inputs required to perform project work.

### Human resources

- Developers
- Analysts
- Project managers
- Designers
- Testers
- Engineers
- Subject-matter experts

### Physical resources

- Machines
- Buildings
- Equipment
- Vehicles
- Materials

### Technical resources

- Servers
- Cloud capacity
- Storage
- Software licenses
- APIs
- Development environments

Resource constraints are not limited to headcount.

A project may have sufficient total employees but still be constrained by a shortage of a specific specialist skill.

---

# 3. The Traditional Project Constraint Triangle

The traditional project constraint model emphasizes three closely related dimensions:

- Scope
- Time
- Cost

These are frequently visualized as a triangle.

A simplified representation is:

    SCOPE
    /   \
   /     \
 TIME --- COST

Changing one dimension often creates pressure elsewhere.

For example:

### Increase scope

Possible consequences:

- More time
- Higher cost
- More resources
- Reduced schedule flexibility
- Greater quality risk

### Reduce time

Possible responses:

- Add resources
- Increase overtime
- Automate work
- Overlap activities
- Reduce scope
- Increase cost

### Reduce cost

Possible responses:

- Reduce scope
- Reduce resource allocation
- Extend the schedule
- Change technology
- Reduce discretionary work

Quality is closely connected to all three even when it is not explicitly represented as one of the three triangle corners.

---

# 4. Quality and Resources as Constraint Dimensions

Modern project environments frequently require a broader model because quality and resource availability have direct operational effects.

A project can have:

- Adequate budget but insufficient skills
- Adequate resources but unrealistic quality requirements
- Adequate time but insufficient funding
- Adequate scope definition but an impossible deadline

This makes project constraint management a multidimensional decision problem.

---

# 5. Constraint Prioritization

Not all constraints have equal flexibility.

The script uses four illustrative priority levels:

| Priority | Meaning |
|---|---|
| Fixed | Effectively non-negotiable |
| High | Changes require significant approval |
| Medium | Changes are possible through normal governance |
| Low | Relatively flexible |

For example:

| Constraint | Possible Priority |
|---|---|
| Regulatory requirement | Fixed |
| Contractual deadline | Fixed or High |
| Budget ceiling | High |
| Preferred technology | Medium |
| Nice-to-have feature | Low |

A project manager should avoid declaring every constraint "fixed."

If time, cost, scope, quality, and resources are all absolutely fixed while conditions change, the project may become mathematically or operationally infeasible.

---

# 6. Hard Constraints and Soft Constraints

## Hard Constraint

A hard constraint must be satisfied.

Examples:

- Legal compliance
- Safety requirement
- Regulatory requirement
- Contractual limit
- Mandatory quality threshold

## Soft Constraint

A soft constraint represents a preference.

Examples:

- Preferred technology
- Preferred team size
- Preferred delivery method
- Optional feature

A strong decision process usually follows this sequence:

1. Eliminate options that violate hard constraints.
2. Compare the remaining feasible alternatives.
3. Use soft preferences to rank the feasible options.

A weighted score should not allow an option violating a mandatory regulatory requirement to beat an option that satisfies it.

---

# 7. Time Management and Schedule Constraints

Time planning requires more than assigning a duration to the project.

A schedule normally requires:

- Activities
- Durations
- Dependencies
- Resource requirements
- Milestones
- Calendars
- Availability
- Constraints
- Acceptance events

The Python script demonstrates a simplified Critical Path Method implementation.

---

# 8. Critical Path Method

Critical Path Method, or CPM, identifies the sequence of activities that determines the minimum project duration under the assumptions represented in the schedule model.

The basic process is:

1. Define activities.
2. Estimate durations.
3. Define dependencies.
4. Calculate earliest start and finish.
5. Calculate latest start and finish.
6. Calculate float or slack.
7. Identify critical activities.

An activity with zero float is typically considered critical in the simplified model used by the script.

### Example

Suppose:

- Requirements = 3 days
- Architecture = 4 days
- Development = 8 days
- Testing = 4 days
- Deployment = 2 days

If these activities are sequential, the duration is:

3 + 4 + 8 + 4 + 2 = 21 days

A delay to any activity on that critical sequence can delay the project unless recovery action is taken.

---

# 9. Float and Slack

Float represents the amount of schedule flexibility available before an activity affects a relevant project or schedule constraint.

A simplified relationship is:

    Float = Latest Start - Earliest Start

Activities with greater float have more scheduling flexibility.

Activities with zero float require greater attention because delays can directly affect the project completion date.

Multiple critical paths are possible. When multiple paths have zero or near-zero float, schedule sensitivity increases.

---

# 10. Schedule Compression

When a project is behind schedule, schedule compression may be considered.

Two major techniques are:

## Crashing

Crashing means adding resources or spending additional money to shorten activity duration.

Examples:

- Additional developers
- Overtime
- Specialist contractors
- Additional testing capacity
- Automation
- Additional equipment

Crashing generally increases cost.

The script calculates:

    Cost per day saved =
        Additional cost / Time saved

This helps compare schedule-compression alternatives.

---

## Fast-Tracking

Fast-tracking means performing activities in parallel that were originally planned sequentially.

For example:

Instead of:

    Design -> Development -> Testing

Some development preparation might begin while parts of the design are still being finalized.

Fast-tracking can reduce schedule duration but increases:

- Coordination risk
- Rework risk
- Dependency risk
- Communication requirements

---

# 11. Cost Management

A basic project budget can be represented as:

    Direct Cost
    + Contingency
    = Project Budget

The script calculates these components programmatically.

## Direct Cost

A cost directly attributable to project work.

Examples:

- Dedicated developer labor
- Project-specific equipment
- Project-specific contractor

## Indirect Cost

A shared organizational cost that may require allocation.

Examples:

- Shared office facilities
- Corporate IT support
- General administration

## Fixed Cost

A cost that remains relatively stable over the relevant activity range.

Example:

- Annual software license

## Variable Cost

A cost that changes with volume or usage.

Example:

- Cloud processing charges based on transaction volume

## Opportunity Cost

The value of the best alternative that is sacrificed when a decision is made.

A project can be within its financial budget and still be economically unattractive because another opportunity was more valuable.

---

# 12. Contingency

Contingency is reserved capacity intended to address identified uncertainty or risk exposure.

For example:

    Direct cost = $100,000
    Contingency = 10%

    Contingency = $10,000
    Budget = $110,000

The script calculates this relationship directly.

Contingency should not be treated as unexplained spare money. It should have a planning rationale and appropriate governance.

---

# 13. Scope Prioritization

When available capacity is insufficient for the entire desired scope, scope prioritization becomes necessary.

The script demonstrates a simplified value-density approach:

    Value Density = Value / Effort

High-value, low-effort items may be attractive candidates for inclusion.

Mandatory scope is treated separately because mandatory work cannot simply be removed by an optimization heuristic.

If mandatory scope itself exceeds available capacity, the project is infeasible under the current constraints.

Possible responses include:

- Increase capacity
- Increase budget
- Extend time
- Reduce mandatory requirements through formal change
- Change the solution design

---

# 14. Scope Baseline

A scope baseline provides an approved reference for the work and deliverables expected from the project.

Scope control requires distinguishing:

- Approved scope
- Requested change
- Approved change
- Rejected change
- Uncontrolled addition

A project should not silently incorporate new requirements without evaluating their effect on time, cost, resources, and quality.

---

# 15. Quality Management

The script distinguishes between:

## Quality Assurance

Quality assurance is primarily process-oriented.

It asks:

> Are appropriate processes being followed to produce reliable results?

Examples:

- Process audits
- Standards
- Training
- Process improvement
- Development practices

## Quality Control

Quality control is primarily output-oriented.

It asks:

> Does the resulting product or deliverable satisfy the required criteria?

Examples:

- Testing
- Inspection
- Measurement
- Defect detection
- Acceptance testing

Both are important.

---

# 16. Acceptance Criteria

Acceptance criteria define the conditions under which a deliverable will be considered acceptable.

Examples:

- At least 95% transaction success
- Response time no greater than 500 ms
- Zero critical defects
- Availability of at least 99.9%

The Python script includes an executable acceptance-validation mechanism.

A deliverable should not automatically be considered complete simply because development work has finished.

Completion and acceptance are related but distinct concepts.

---

# 17. Cost of Quality

The script presents a simplified Cost of Quality model consisting of:

- Prevention
- Appraisal
- Internal failure
- External failure

### Prevention

Activities intended to prevent defects.

Examples:

- Training
- Process design
- Automation
- Standards
- Engineering practices

### Appraisal

Activities used to detect problems.

Examples:

- Testing
- Inspection
- Auditing

### Internal Failure

Problems detected before delivery.

Examples:

- Rework
- Scrap
- Failed testing

### External Failure

Problems discovered after delivery.

Examples:

- Customer complaints
- Warranty work
- Production incidents
- Remediation
- Reputation damage

Increasing prevention and appraisal expenditure can sometimes reduce failure costs.

The objective is not simply to minimize testing expenditure. The objective is to achieve an economically and operationally appropriate quality level.

---

# 18. Resource Constraints

Resource constraints occur when the required capacity exceeds available capacity.

A simplified capacity relationship is:

    Capacity =
        Number of resources
        × Productivity
        × Available time

This model is useful for initial planning but does not guarantee linear productivity.

Real projects contain:

- Communication overhead
- Coordination costs
- Onboarding time
- Shared dependencies
- Specialist bottlenecks
- Management overhead
- Rework

---

# 19. Resource Leveling

A logically valid schedule can still be resource-infeasible.

Suppose two activities can logically occur at the same time:

    Activity A -> 3 developers
    Activity B -> 3 developers

Available developers:

    4

Simultaneous execution requires:

    3 + 3 = 6 developers

Therefore, the schedule violates the resource constraint.

Resource leveling may delay one activity.

This can increase total project duration even though the original dependency network indicated that parallel execution was possible.

---

# 20. Logical Schedule vs Resource-Feasible Schedule

These are different concepts.

### Logical schedule

Respects activity dependencies.

### Resource-feasible schedule

Respects:

- Activity dependencies
- Resource availability
- Resource calendars
- Capacity limitations

A schedule is not operationally executable simply because its dependency relationships are correct.

---

# 21. Constraint Interaction

The script demonstrates several project scenarios:

- Baseline
- Fast delivery
- Lower cost
- Reduced scope
- Quality pressure

Each scenario changes several dimensions.

This illustrates constraint coupling.

For example:

    Faster delivery
        -> more resources
        -> higher cost
        -> greater coordination
        -> potential quality risk

Another example:

    Lower cost
        -> fewer resources
        -> longer duration
        -> possible schedule risk

Another:

    Increased scope
        -> more work
        -> more time or resources
        -> higher cost
        -> greater coordination

---

# 22. Constraint Migration

Constraint migration occurs when solving one constraint creates pressure elsewhere.

For example:

A team is behind schedule.

Management adds five developers.

The schedule may improve, but:

- Cost increases.
- Existing developers must train new members.
- Communication paths increase.
- Integration complexity increases.
- Quality may temporarily decrease.

The original schedule problem may therefore become a cost and coordination problem.

A good manager asks:

> Where does the constraint move after this decision?

---

# 23. Change Control

Project changes should be evaluated systematically.

A change-control process can include:

1. Identify the requested change.
2. Understand the reason for the change.
3. Determine scope impact.
4. Determine schedule impact.
5. Determine cost impact.
6. Determine resource impact.
7. Determine quality impact.
8. Analyze risks and dependencies.
9. Identify alternatives.
10. Obtain approval.
11. Update affected plans and baselines.
12. Communicate the decision.

The script includes a `ChangeRequest` structure that models changes across all five constraint dimensions.

---

# 24. Feasibility Analysis

Feasibility analysis asks:

> Can the proposed project configuration satisfy the current constraints?

For a scenario to be feasible, it may need to satisfy:

    Time <= Maximum Time
    Cost <= Maximum Cost
    Scope >= Required Scope
    Quality >= Required Quality
    Resources <= Available Resources

These relationships are directional because some constraints are minimized while others are maximized.

For example:

- Lower duration is generally preferable.
- Lower cost is generally preferable.
- Higher delivered scope is generally preferable.
- Higher quality is preferable up to the required level.
- Lower resource demand is generally preferable when capacity is limited.

---

# 25. Infeasible Projects

If mandatory requirements exceed available capacity, the project cannot be made feasible through wishful planning.

For example:

    Required scope = 100 units
    Available capacity = 70 units

If the scope requirement is mandatory, at least one constraint must change.

Possible actions:

- Increase resources
- Increase budget
- Extend schedule
- Reduce scope
- Improve productivity
- Change technology
- Change architecture
- Split the release
- Renegotiate the requirement

---

# 26. Multi-Criteria Trade-Off Analysis

Not all decisions can be made using a single metric.

The script demonstrates weighted scoring across:

- Time
- Cost
- Scope
- Quality
- Resources

For example:

    Time       = 25%
    Cost       = 20%
    Scope      = 25%
    Quality    = 25%
    Resources   = 5%

The weights represent decision-maker priorities.

Weighted scoring is useful, but it has limitations.

## Limitations

- Weight selection may be subjective.
- Normalization may distort results.
- Scores can create false precision.
- Different stakeholders may choose different weights.
- A numerical score may hide a serious risk.
- Hard constraints should generally be evaluated separately.

A better approach is:

    Hard constraints
        -> feasibility filter
        -> soft-criteria scoring
        -> risk analysis
        -> stakeholder decision

---

# 27. Earned Value Management

Earned Value Management connects scope progress, planned work, and actual spending.

The script implements the basic metrics.

## Planned Value

PV is the budgeted value of work planned to be completed.

## Earned Value

EV is the budgeted value of work actually completed.

## Actual Cost

AC is the actual amount spent for the work performed.

---

# 28. Cost Variance

The basic formula is:

    CV = EV - AC

Interpretation:

    CV > 0
        Favorable cost performance

    CV < 0
        Unfavorable cost performance

    CV = 0
        Earned value equals actual cost

---

# 29. Schedule Variance

The basic EVM formula is:

    SV = EV - PV

Interpretation:

    SV > 0
        Progress is ahead of planned value

    SV < 0
        Progress is behind planned value

    SV = 0
        Earned value equals planned value

Schedule Variance in EVM is a value-based measure. It should not be confused directly with a calendar-day difference.

---

# 30. Cost Performance Index

The Cost Performance Index is:

    CPI = EV / AC

Interpretation:

    CPI > 1
        Favorable cost efficiency

    CPI < 1
        Unfavorable cost efficiency

    CPI = 1
        Earned value equals actual cost

Example:

    EV = $80,000
    AC = $100,000

    CPI = 0.80

This indicates that each dollar of actual cost is producing only $0.80 of earned value under the simplified EVM interpretation.

---

# 31. Schedule Performance Index

The Schedule Performance Index is:

    SPI = EV / PV

Interpretation:

    SPI > 1
        Ahead of planned value

    SPI < 1
        Behind planned value

    SPI = 1
        Exactly at planned value

Example:

    EV = $80,000
    PV = $100,000

    SPI = 0.80

The project has earned 80% of the planned value at the measurement point.

---

# 32. Estimate at Completion

A simplified Estimate at Completion model is:

    EAC = BAC / CPI

Where:

- EAC = Estimate at Completion
- BAC = Budget at Completion
- CPI = Cost Performance Index

The model assumes current cost efficiency continues.

The script also calculates:

    ETC = EAC - AC

where ETC represents the estimated cost required to complete the remaining work under the simplified model.

Forecasting assumptions must be examined carefully. A single formula cannot represent every project.

---

# 33. Uncertainty and Risk

Project estimates are uncertain.

A duration estimate such as:

    100 days

does not necessarily mean the project will finish exactly on day 100.

Possible outcomes could be:

- 80 days
- 100 days
- 130 days

The script demonstrates expected value using probability-weighted outcomes.

The expected value is:

    Expected Value =
        Sum of Probability × Outcome

Expected value is a mathematical decision-analysis construct. It is not a guarantee that the actual result will equal the expected value.

---

# 34. Contingency and Uncertainty

Uncertainty can affect:

- Schedule
- Cost
- Resource requirements
- Scope
- Quality

Contingency provides planned capacity for identified uncertainty or risk exposure.

Good planning distinguishes:

- Known requirements
- Assumptions
- Risks
- Issues
- Contingency
- Approved reserves

---

# 35. Probabilistic Schedule Simulation

The script includes a simplified Monte Carlo-style simulation.

Instead of assigning one fixed duration to each activity, it defines a range.

For example:

    Development:
        minimum = 8 days
        maximum = 15 days

The script repeatedly samples possible durations and calculates project completion.

It reports:

- Minimum
- Mean
- P50
- P80
- P90
- P95
- Maximum

### Interpretation

P90 represents a duration at or below which approximately 90% of the simulated outcomes fall under the assumptions of the model.

This is useful for understanding schedule uncertainty.

The implementation is deliberately simplified and assumes:

- Uniform duration distributions
- Independent activity durations
- Finish-to-start dependencies
- Unlimited resources

Real quantitative risk models may require:

- Triangular distributions
- Beta distributions
- Historical data
- Correlations
- Resource calendars
- Resource constraints
- External dependencies
- Validated statistical assumptions

---

# 36. Constraint Negotiation

Constraint negotiation is not simply an argument about who absorbs additional work.

A structured approach is:

    Problem
        ↓
    Identify constraint
        ↓
    Generate alternatives
        ↓
    Quantify impacts
        ↓
    Evaluate priorities
        ↓
    Approve decision
        ↓
    Update project plan

Possible negotiation outcomes include:

- Extend the deadline
- Increase the budget
- Reduce scope
- Increase capacity
- Change technology
- Change delivery strategy
- Split delivery into releases

---

# 37. Progressive Elaboration

Project plans become more detailed as information becomes available.

Typical planning maturity is:

### Concept

High-level:

- Business outcome
- Rough duration
- Rough cost

### Initiation

Initial:

- Stakeholders
- Scope
- Assumptions
- Constraints
- Risks

### Planning

Detailed:

- Work packages
- Activities
- Schedule
- Budget
- Resources
- Quality criteria

### Execution

Actual information:

- Progress
- Cost
- Issues
- Changes
- Forecasts

### Closing

Final information:

- Acceptance
- Actual cost
- Final schedule
- Lessons learned

Progressive elaboration does not mean planning can be ignored. It means planning detail should match the maturity and certainty of available information.

---

# 38. Baseline Control

A baseline is valuable only when it is controlled.

Suppose:

    Approved budget = $100,000
    Actual cost = $106,000

The project has a $6,000 cost variance.

If the approved budget is changed to $110,000 without appropriate governance, the original performance problem can disappear from the measurement system.

Therefore, baseline changes should be:

- Justified
- Approved
- Documented
- Traceable
- Communicated

---

# 39. Variance and Escalation

Monitoring systems often use thresholds.

An illustrative model might be:

| Variance | Status |
|---|---|
| Below 5% | Normal |
| 5% to below 10% | Warning |
| 10% or more | Critical |

Actual thresholds should depend on:

- Project criticality
- Contractual requirements
- Organizational policy
- Risk appetite
- Project size
- Regulatory conditions

Thresholds convert raw measurements into management actions.

---

# 40. Capacity Planning

The script calculates the number of resources required using:

    Required Resources =
        Work Units /
        (Productivity per Resource per Day × Available Days)

Example:

    Work = 1,200 units
    Productivity = 6 units/person/day
    Time = 40 days

Capacity per person:

    6 × 40 = 240 units

Required people:

    1,200 / 240 = 5

This is a simplified model.

Real productivity is affected by:

- Experience
- Coordination
- Interruptions
- Dependencies
- Tools
- Process maturity
- Quality requirements
- Rework
- Training

---

# 41. Diminishing Returns

Adding resources does not necessarily increase productivity linearly.

If one developer produces a certain amount of work, ten developers may not produce exactly ten times that amount.

Reasons include:

- Communication overhead
- Coordination
- Integration
- Shared decisions
- Training
- Management overhead
- Architectural constraints
- Limited parallelism

This is particularly important when using crashing as a schedule-recovery technique.

A useful decision question is:

> What is the marginal schedule benefit of one additional resource compared with its marginal cost and risk?

---

# 42. Real-World Applications

Project constraints apply across industries.

## Software Development

Constraints may include:

- Release date
- Feature scope
- Engineering capacity
- Test quality
- Cloud cost
- Security requirements

## Construction

Constraints may include:

- Completion date
- Material budget
- Design scope
- Safety standards
- Labor
- Equipment availability

## Healthcare

Constraints may include:

- Go-live date
- Implementation cost
- Clinical functionality
- Patient safety
- Specialist availability
- Regulatory compliance

## Manufacturing

Constraints may include:

- Production schedule
- Unit cost
- Product configuration
- Defect rate
- Machine capacity

## Consulting

Constraints may include:

- Client deadline
- Contract fee
- Deliverables
- Analytical quality
- Consultant availability

---

# 43. Edge Cases

The script explicitly considers several edge cases.

## Zero Scope

A project can theoretically have zero deliverable scope, but it should have a clear reason for existing.

## Zero Resources

A positive-duration project generally cannot execute without some execution capacity.

## Zero Cost

A project may have no incremental monetary expenditure while still consuming economic resources.

For example, internal employees may be used without a new external invoice.

## 100% Quality

A perfect quality requirement may be inappropriate depending on how quality is defined and measured.

## Negative Float

Negative float can occur when required completion dates are earlier than the current schedule can support.

## Mandatory Scope Exceeds Capacity

The project is infeasible unless at least one constraint changes.

## Multiple Critical Paths

Several paths may have zero or near-zero float, increasing schedule sensitivity.

## Shared Specialist

Two activities may independently be feasible while being jointly infeasible because both require the same specialist at the same time.

---

# 44. Common Project Constraint Mistakes

## Treating Everything as Fixed

If every variable is declared non-negotiable, there may be no feasible recovery option.

## Ignoring Scope Boundaries

Unclear scope leads to unreliable estimates and uncontrolled work.

## Compressing Every Activity

Only activities affecting the relevant schedule constraint should normally be considered for expensive compression.

## Adding People Automatically

More people can introduce coordination and onboarding costs.

## Measuring Success by Budget Alone

A project can be under budget while:

- Late
- Incomplete
- Poor quality
- Under-resourced
- Unaccepted

## Treating Quality as an Afterthought

Poor quality creates:

- Rework
- Support costs
- Delays
- Customer dissatisfaction
- Operational risk

## Ignoring Resource Calendars

A resource can exist but still be unavailable at the required time.

## Moving Baselines Without Governance

Repeated baseline changes can make project performance difficult to interpret.

## Using Weighted Scoring for Mandatory Requirements

An option violating a hard requirement should normally be rejected before weighted scoring.

## Confusing Estimates with Commitments

An estimate is a forecast.

A commitment is an agreed obligation.

The two have different managerial implications.

---

# 45. Security and Governance Considerations

Project constraint management can contain commercially and operationally sensitive information.

Relevant controls include:

## Access Control

Only authorized personnel should be able to modify:

- Budgets
- Schedules
- Requirements
- Resource plans
- Approvals

## Change Authorization

Material changes should require appropriate approval.

## Auditability

Important decisions should be traceable.

Useful records include:

- Original baseline
- Requested change
- Approval decision
- Approved change
- Responsible authority
- Date of decision

## Data Integrity

Constraint data should be protected from unauthorized or accidental modification.

## Separation of Duties

For sensitive projects, the person requesting a change may be different from the person approving it.

## Confidentiality

Sensitive information may include:

- Vendor rates
- Salaries
- Contract values
- Staffing information
- Commercial strategies
- Project risks

Technology projects may also require:

- Least privilege
- Secure change management
- Credential protection
- Production access controls
- Privacy controls
- Third-party risk management

---

# 46. Implementing Constraint Monitoring Systems

A project-control system can be conceptually structured as:

    Raw Data
       ↓
    Validation
       ↓
    Baseline Comparison
       ↓
    Variance Calculation
       ↓
    Threshold Evaluation
       ↓
    Alert / Investigation
       ↓
    Decision
       ↓
    Approved Action
       ↓
    Updated Plan

The Python script represents this concept using a `ConstraintRecord` structure.

Each record stores:

- Name
- Baseline
- Current value
- Unit
- Tolerance

It then calculates:

- Absolute variance
- Percentage variance
- Status

A production system should preserve historical records rather than simply replacing old values.

---

# 47. Testing and Validation

The Python script includes built-in assertion tests.

These test:

- Constraint validation
- Quality requirements
- Budget calculations
- Critical-path calculations
- Feasibility
- Earned Value metrics
- Acceptance criteria

Testing is important because project-management software can influence financial, contractual, and operational decisions.

Incorrect calculations can lead to incorrect:

- Forecasts
- Resource plans
- Escalations
- Budget decisions
- Schedule decisions

---

# 48. Implementation Considerations

A production project-constraint system should consider:

### Data validation

Reject:

- Negative durations
- Negative costs
- Invalid quality ranges
- Invalid probabilities
- Missing dependencies
- Circular activity networks

### Traceability

Maintain:

- Baseline history
- Change history
- Approval history
- Forecast history
- Decision records

### Numerical accuracy

Financial systems should consider decimal arithmetic and currency-specific rounding rather than relying blindly on binary floating-point arithmetic.

The educational script uses ordinary Python numeric types because the focus is project-constraint logic.

### Scalability

Large project networks may require more efficient graph algorithms, persistent storage, caching, and incremental recalculation.

### Auditability

Important project decisions should be reproducible from recorded data.

---

# 49. Integrated Constraint Case

The script includes an integrated customer-service platform case.

Approved constraints:

    Time      = 120 days
    Cost      = $250,000
    Scope     = 100 units
    Quality   = 92/100 minimum
    Resources = 12 units maximum

Current forecast:

    Time      = 135 days
    Cost      = $275,000
    Scope     = 100 units
    Quality   = 94/100
    Resources = 14 units

The project is:

- Late
- Over budget
- Resource constrained
- Meeting scope
- Above the quality requirement

This is an important situation because improving quality is not necessarily the appropriate response. Quality is already above the required threshold.

Possible recovery strategies include:

### Reduce scope

Potential effect:

- Lower duration
- Lower cost
- Lower resource demand
- Reduced delivered functionality

### Increase budget and resources

Potential effect:

- Lower duration
- Higher cost
- Potentially lower resource pressure if capacity increases

### Extend deadline

Potential effect:

- Schedule constraint becomes less restrictive
- Cost may decrease through reduced compression pressure
- Delivery occurs later

### Replan delivery

Potential effect:

- Changes the method of achieving the same objective
- May improve schedule and cost simultaneously if the current approach is inefficient

The correct answer depends on which constraints are actually negotiable.

---

# 50. Advanced Constraint Principles

## Constraint Coupling

Constraints interact.

A change in one dimension can affect multiple other dimensions.

## Constraint Migration

Solving one constraint may create another problem.

## Bottleneck Management

A single scarce capacity can limit total system throughput.

## Marginal Analysis

Compare incremental benefit against incremental cost and risk.

## Feasibility Before Optimization

First determine whether an option is feasible.

Only then compare feasible options.

## Baseline Integrity

Controlled baselines are essential for meaningful performance measurement.

## Uncertainty Awareness

Point estimates can conceal substantial variation.

## Quality as a System Property

Quality depends on:

- Requirements
- Design
- Process
- Testing
- Resources
- Schedule pressure
- Operating environment

## Lifecycle Perspective

The cheapest project implementation may not have the lowest lifecycle cost.

For example, reducing testing can lower development cost while increasing:

- Production defects
- Support costs
- Rework
- Customer dissatisfaction

## Decision Latency

Slow decisions can themselves become project constraints.

A team may have sufficient technical capacity but remain blocked because required stakeholder decisions are delayed.

---

# 51. Practical Constraint Decision Framework

A disciplined project manager can use the following sequence:

1. Define the desired project outcome.
2. Define measurable deliverables.
3. Identify time constraints.
4. Identify cost constraints.
5. Identify scope constraints.
6. Define quality requirements.
7. Identify resource limitations.
8. Classify constraints by flexibility.
9. Identify assumptions.
10. Identify dependencies.
11. Establish baselines.
12. Build the schedule.
13. Estimate cost.
14. Plan resources.
15. Define acceptance criteria.
16. Identify risks.
17. Monitor actual performance.
18. Compare performance with baselines.
19. Identify constraint conflicts.
20. Analyze root causes.
21. Generate alternative responses.
22. Quantify time, cost, scope, quality, and resource effects.
23. Reject infeasible alternatives.
24. Compare feasible alternatives.
25. Obtain appropriate approval.
26. Update controlled plans and baselines.
27. Monitor the consequences of the decision.

---

# 52. Key Formulas Used in the Script

## Budget

    Total Budget =
        Direct Cost + Contingency

## Contingency

    Contingency =
        Direct Cost × Contingency Rate

## Critical Path

For a simple finish-to-start network:

    Earliest Finish =
        Earliest Start + Duration

    Earliest Start =
        Maximum predecessor finish

## Float

    Float =
        Latest Start - Earliest Start

## Schedule Compression

    Cost per Day Saved =
        Additional Cost / Time Saved

## Capacity

    Capacity =
        Resources × Productivity × Available Time

## Required Resources

    Required Resources =
        Work /
        (Productivity × Available Time)

## Cost Variance

    CV = EV - AC

## Schedule Variance

    SV = EV - PV

## Cost Performance Index

    CPI = EV / AC

## Schedule Performance Index

    SPI = EV / PV

## Simplified Estimate at Completion

    EAC = BAC / CPI

## Estimate to Complete

    ETC = EAC - AC

## Expected Value

    EV(expected) =
        Sum(Probability × Outcome)

## Percentage Variance

    Variance % =
        (Current - Baseline) / Baseline × 100

---

# 53. Important Distinctions

| Concept | Meaning |
|---|---|
| Scope | What the project delivers |
| Time | When it must be delivered |
| Cost | Financial expenditure |
| Quality | Required performance or conformance |
| Resources | Capacity available to perform work |
| Estimate | Forecast |
| Budget | Authorized funding |
| Actual Cost | Amount actually spent |
| Baseline | Approved reference |
| Risk | Uncertain future condition |
| Issue | Current problem |
| Assumption | Planning condition believed to be true |
| Dependency | Relationship between activities or decisions |
| Constraint | Limitation on project choices |
| Scope Creep | Uncontrolled scope expansion |
| Change Request | Formal proposed change |
| Milestone | Significant project event |
| Acceptance Criterion | Condition for deliverable acceptance |

---

# 54. Limitations of Simplified Models

The Python script is designed for education and demonstrates project-management concepts through executable models.

Several models are deliberately simplified.

The Critical Path implementation does not fully model:

- Resource calendars
- Holidays
- Multiple calendars
- Complex dependency types
- Leads and lags
- Constraints beyond finish-to-start dependencies

The schedule simulation does not model:

- Correlated risks
- Non-uniform distributions
- Resource contention
- Calendar effects
- Historical statistical calibration

The cost-of-quality model is illustrative rather than a universal economic model.

The weighted scenario score is a decision-support mechanism, not an objective measure of project value.

Real projects require context-specific planning and governance.

---

# 55. Structure of the Python Script

The script progresses from fundamentals to advanced applications.

Its major sections are:

1. Fundamental terminology
2. Constraint triangle
3. Constraint prioritization
4. Time and critical path
5. Schedule compression
6. Cost management
7. Cost classifications
8. Scope management
9. Quality constraints
10. Cost of quality
11. Resource constraints
12. Resource leveling
13. Constraint interactions
14. Change control
15. Trade-off scoring
16. Hard vs soft constraints
17. Feasibility analysis
18. Earned Value Management
19. Cost forecasting
20. Uncertainty and contingency
21. Probabilistic schedule simulation
22. Constraint negotiation
23. Progressive elaboration
24. Baseline control
25. Acceptance criteria
26. Variance thresholds
27. Capacity planning
28. Diminishing returns
29. Real-world applications
30. Edge cases
31. Common mistakes
32. Security and governance
33. Constraint monitoring implementation
34. Automated tests
35. Integrated case study
36. Decision framework
37. Advanced principles
38. Knowledge check

Each section contains executable Python demonstrations rather than relying only on theoretical descriptions.
