# Project initiation: How a project begins

## Introduction

Project initiation is the stage in which an organization determines whether an idea, problem, opportunity, requirement, or strategic need should become an authorized project.

Initiation establishes the reason for the project, the expected value, the major boundaries, the important stakeholders, the initial risks, the feasibility of the proposed effort, and the authority responsible for approving it.

The Python script accompanying this README presents project initiation as both a management discipline and an executable learning model. It moves from basic definitions to business cases, feasibility analysis, stakeholder analysis, risk management, project charters, governance, prioritization, Agile and predictive approaches, and an integrated initiation simulation.

The examples use only the Python standard library.

## What is a project?

A project is a temporary effort undertaken to create a unique product, service, result, or change.

The two characteristics that distinguish projects from routine operations are particularly important:

- A project is temporary.
- A project creates a unique result or change.

Examples include:

- Implementing a customer relationship management system
- Developing a new banking application
- Constructing a manufacturing facility
- Migrating organizational data to a new platform
- Launching a new product
- Implementing a new business process
- Establishing a new distribution center

A project eventually reaches a point at which its planned work is completed, cancelled, transferred, or otherwise terminated.

## Projects and operations

Projects and operations can interact closely, but they are not the same.

| Dimension | Project | Operations |
|---|---|---|
| Duration | Temporary | Continuous or recurring |
| Purpose | Create a change or unique result | Sustain recurring activities |
| Output | Unique result | Repetitive output |
| End point | Defined or identifiable | Usually ongoing |
| Example | Implement a CRM | Operate the CRM |
| Management focus | Change and delivery | Stability and continuity |

An organization may operate a system for many years after a project has implemented it.

For example, implementing an online banking platform is a project. Processing customer transactions through that platform after implementation is operational work.

## What project initiation means

Project initiation converts a concept into a decision-ready proposition.

The initiation stage normally establishes:

- Why the project is needed
- What problem or opportunity exists
- What outcome is desired
- What business value is expected
- Who sponsors the work
- Who owns the business outcome
- Who will be affected
- Whether the project is feasible
- What the project broadly includes
- What it explicitly excludes
- What major risks exist
- What assumptions and constraints apply
- What resources and funding may be required
- How success will be measured
- Who has authority to approve the project

The objective is not to produce every detail required for execution. The objective is to establish enough clarity and evidence for an informed authorization decision.

## Why projects are initiated

The script defines several common project drivers.

### Business problems

A measurable condition may require improvement.

Examples include:

- High operating costs
- Slow customer service
- Poor data quality
- Manual processing
- High error rates
- Low employee productivity
- System instability

### Business opportunities

A project may be initiated because an organization sees a potential advantage.

Examples include:

- Entering a new market
- Launching a product
- Automating a process
- Expanding a service
- Developing a new revenue stream

### Strategic objectives

Projects are frequently used to implement organizational strategy.

For example, a company may have a strategic goal of becoming digitally enabled. Individual technology and process-transformation projects can support that objective.

### Regulatory and compliance requirements

Some projects exist because the organization must satisfy a legal, regulatory, contractual, security, safety, or governance requirement.

Financial return may not be the primary reason for such projects.

### Customer requirements

A customer requirement may lead to a project when fulfilling the requirement requires a significant temporary effort.

### Technology changes

Major technology transitions can require projects involving architecture, implementation, migration, training, testing, and organizational change.

### Risk reduction

An organization may initiate a project to reduce the probability or impact of a major future problem.

## Problem statement

A project should normally begin with a clear understanding of the underlying need.

A useful problem statement separates three elements:

1. Current state
2. Business impact
3. Desired direction

For example:

Current state:

> Customer support requests are processed manually.

Business impact:

> Average resolution time is four business days and customers frequently escalate.

Desired direction:

> Reduce resolution time while maintaining service quality.

This structure prevents the discussion from immediately becoming a discussion about a particular technology.

## Problem versus solution

One of the most important initiation disciplines is separating the problem from the proposed solution.

Weak initiation:

> We need a new customer-service platform.

Better initiation:

> Customer requests are fragmented across multiple workflows, producing long resolution times and poor visibility.

The second statement permits the organization to evaluate multiple solutions.

Potential alternatives could include:

- Process redesign
- Automation
- Configuration of an existing system
- Purchase of a commercial platform
- Development of a custom platform
- Organizational changes
- A combination of these approaches

A technology solution may eventually be selected, but it should not automatically become the project definition before the problem has been understood.

## Root-cause analysis

The script demonstrates a five-whys style investigation.

The purpose is to move from symptoms toward underlying causes.

For example:

1. Customer requests remain unresolved for several days.
2. Requests are manually assigned.
3. There is no centralized queue.
4. Teams use different tracking methods.
5. The existing workflow was designed for a much smaller customer base.
6. Business growth increased demand without a corresponding process redesign.

This type of investigation can prevent an organization from solving only the visible symptom.

The five-whys technique does not require exactly five questions. The appropriate depth depends on the problem.

## Project idea

A project idea is an early concept.

The script represents an idea using:

- Project name
- Problem
- Expected benefit
- Proposed solution
- Strategic alignment

At this stage, information is usually incomplete.

An idea should not automatically be treated as an approved project.

## Project proposal

A project proposal is more structured.

The example includes:

- Business problem
- Objective
- Expected benefits
- High-level scope
- Estimated cost
- Estimated duration
- Strategic alignment
- Feasibility

The proposal provides a stronger basis for investigation and decision-making.

## Outputs, deliverables, outcomes, and benefits

These concepts are related but should not be treated as interchangeable.

### Output

An output is something produced by project work.

Example:

> Centralized customer service platform

### Deliverable

A deliverable is a defined project result that can be reviewed or accepted.

Examples:

- Approved requirements
- Configured platform
- Migration package
- Training materials
- Deployment package

### Outcome

An outcome is a change produced by using the project result.

Example:

> Agents can access and process customer requests through one workflow.

### Benefit

A benefit is the measurable business advantage associated with the outcome.

Example:

> Reduced customer-resolution time.

The relationship can therefore be expressed as:

Output → Outcome → Benefit

A project can deliver its outputs successfully without producing the intended business benefits. Benefits may depend on adoption, operations, market conditions, organizational behavior, and other factors outside direct project control.

## Project objectives

A project objective states what the project intends to achieve.

The script implements a SMART objective model.

### Specific

The objective should identify what is being changed.

### Measurable

There should be a way to determine whether the desired result occurred.

### Achievable

The objective should be plausible given known resources, technology, time, and organizational conditions.

### Relevant

The objective should address the business need.

### Time-bound

The objective should identify an appropriate time boundary.

Example:

> Reduce average customer-resolution time from four days to 2.4 days within six months after implementation.

This is stronger than:

> Improve customer service.

The second statement expresses an intention but does not provide enough information for objective measurement.

## Scope

Project scope describes the boundaries of the project.

The script distinguishes between:

- In-scope work
- Out-of-scope work
- Undefined work

Example in-scope items:

- Customer-service workflow
- Platform configuration
- Data migration
- Training
- Reporting dashboard

Example out-of-scope items:

- Replacement of the corporate ERP
- International expansion
- Unrelated marketing automation

Explicit exclusions are valuable because stakeholders may otherwise assume that the project covers related activities.

## Scope should not be unnecessarily detailed during initiation

Initiation normally establishes high-level boundaries.

Detailed scope definition belongs primarily to planning or iterative discovery.

There is an important balance:

- Too little scope definition creates ambiguity.
- Excessive early detail can waste effort before the project has been authorized.

The appropriate level depends on project uncertainty and delivery approach.

## Stakeholders

A stakeholder is a person, group, or organization that can affect, be affected by, or perceive itself to be affected by the project.

Typical stakeholders include:

- Sponsor
- Business owner
- Project manager
- Project team
- Customers
- End users
- Technology teams
- Security teams
- Finance
- Legal
- Compliance
- Suppliers
- Regulators
- Operations teams
- Senior management

Stakeholders can have different levels of influence and interest.

## Stakeholder influence-interest analysis

The script uses a simple matrix.

| Influence | Interest | Typical approach |
|---|---|---|
| High | High | Manage closely |
| High | Low | Keep satisfied |
| Low | High | Keep informed |
| Low | Low | Monitor |

This is a simplified model.

Real stakeholder relationships can be more complex. A stakeholder with formally low authority may still possess significant informal influence or specialized knowledge.

## Project roles

The script demonstrates several common project roles.

### Sponsor

The sponsor normally provides organizational authority, strategic support, and executive-level decision support.

### Project manager

The project manager coordinates project work, manages delivery, facilitates decisions, monitors performance, and manages project-level risks and issues.

### Business owner

The business owner represents the business outcome and helps define requirements, acceptance, and expected value.

### Project team

The project team performs the work required to create project deliverables.

### Customer

The customer receives or uses the result.

### Governance body

A steering committee or other governance authority may provide oversight and make decisions beyond delegated project authority.

### Subject matter expert

A subject matter expert contributes specialized knowledge.

Role names and decision rights vary by organization.

## RACI

RACI is a responsibility-assignment model.

The letters commonly represent:

- R = Responsible
- A = Accountable
- C = Consulted
- I = Informed

Responsible describes who performs the work.

Accountable describes who owns the result or decision.

Consulted parties provide input.

Informed parties receive relevant information.

A common mistake is assigning multiple people as accountable for a single decision without clearly defining who has final authority.

## Feasibility analysis

Feasibility analysis determines whether a proposed project is practical enough to justify further investment.

The script evaluates:

- Technical feasibility
- Financial feasibility
- Operational feasibility
- Legal feasibility
- Schedule feasibility
- Organizational feasibility

The model produces an illustrative score.

A high score does not guarantee success. Feasibility analysis is a decision aid, not a prediction of the future.

### Technical feasibility

Questions include:

- Can the required technology support the proposed result?
- Can required systems integrate?
- Are required skills available?
- Are architectural constraints manageable?

### Financial feasibility

Questions include:

- Is funding available?
- Are expected benefits credible?
- Is the investment proportionate to value?
- Are recurring operating costs understood?

### Operational feasibility

Questions include:

- Can the organization operate the resulting solution?
- Are processes ready to change?
- Are support capabilities available?
- Can users adopt the new way of working?

### Legal and regulatory feasibility

Questions include:

- Are applicable laws understood?
- Are contractual requirements manageable?
- Are privacy or security obligations relevant?
- Are regulatory approvals required?

### Schedule feasibility

A technically feasible project may still be infeasible if it cannot meet a critical deadline.

### Organizational feasibility

A project can fail because the organization cannot support the required change even when the technology works.

## Business case

A business case explains why the organization should invest in a project.

A business case may include:

- Problem or opportunity
- Strategic alignment
- Alternatives
- Expected benefits
- Costs
- Risks
- Financial analysis
- Non-financial considerations
- Assumptions
- Constraints
- Implementation considerations

Not every project requires the same level of business-case detail.

## Return on investment

The script implements a simple ROI calculation.

The general structure is:

ROI = (Total Net Benefit - Investment) / Investment

A percentage can be obtained by multiplying the result by 100.

Simple ROI is useful for comparison, but it has limitations.

It may not adequately account for:

- Timing of cash flows
- Risk
- Inflation
- Opportunity cost
- Capital structure
- Tax effects
- Different project lifetimes

## Payback period

Payback period estimates how long it takes for cumulative net benefits to recover the initial investment.

The simplified model is:

Payback Period = Initial Investment / Annual Net Benefit

If annual net benefit is zero or negative, simple payback cannot be achieved using this model.

Payback is easy to understand but ignores benefits received after the payback point and does not fully account for the time value of money.

## Net present value

The script also demonstrates NPV.

NPV discounts future cash flows to their present value.

A simplified representation is:

NPV = -Initial Investment + Σ [Cash Flow at Period t / (1 + Discount Rate)^t]

A positive NPV generally indicates that the expected discounted benefits exceed the investment under the assumptions used.

NPV is more financially informative than simple ROI for many multi-period investment decisions.

## Benefit-cost ratio

The benefit-cost ratio is:

Benefit-Cost Ratio = Total Benefits / Total Costs

A ratio above 1 indicates that benefits exceed costs under the model's assumptions.

This should not automatically be treated as an approval rule because strategic, regulatory, risk, safety, and other non-financial factors may be important.

## Estimation

Early project estimates are uncertain.

The script demonstrates three-point estimation:

- Optimistic
- Most likely
- Pessimistic

It uses the PERT-style expected value:

Expected Estimate = (Optimistic + 4 × Most Likely + Pessimistic) / 6

Three-point estimation can communicate uncertainty better than presenting a single early number as if it were exact.

## False precision

A project estimated at exactly 5.73 months during early initiation may communicate a level of confidence that the evidence does not support.

Early estimates should often be represented as:

- Ranges
- Scenarios
- Confidence levels
- Explicit assumptions
- Three-point estimates

The estimate should become more refined as the project acquires information.

## Assumptions

An assumption is a condition considered true for planning purposes even though it may not yet be confirmed.

Example:

> Business users will be available for requirements workshops.

If the assumption proves false, cost, schedule, scope, or quality may be affected.

Assumptions should therefore be visible rather than silently embedded in plans.

## Constraints

A constraint restricts the project.

Examples include:

- Budget limit
- Regulatory deadline
- Fixed launch date
- Resource limitation
- Technology standard
- Contractual requirement

The script models a budget limit and a target implementation duration as constraints.

## Dependencies

A dependency exists when one activity, project, team, supplier, or external condition affects another.

Example:

> Security review must be completed before production deployment.

Dependencies can create schedule risk and should be identified during initiation when they can materially influence feasibility.

## Risk

A risk is an uncertain event or condition that, if it occurs, can affect project objectives.

The script represents risk using:

- Probability
- Impact
- Response
- Owner

A simple quantitative risk exposure calculation is:

Risk Exposure = Probability × Impact

For example:

Probability = 0.50

Impact = 8

Risk Exposure = 4

This is an analytical simplification. Real risk models may use financial impact, schedule impact, quality impact, probability distributions, or other measures.

## Risk severity

The script also provides a qualitative risk matrix.

Probability and impact are rated from 1 to 5 and multiplied to produce a score.

The example categorizes scores into:

- Low
- Medium
- High
- Critical

Organizations should calibrate thresholds according to their own context.

A 5 × 5 matrix is useful for communication but should not create false mathematical certainty.

## Risk responses

The script demonstrates four common responses to threats.

### Avoid

Change the project approach so the threat no longer applies or is substantially eliminated.

### Mitigate

Reduce probability or impact.

### Transfer

Shift ownership of some consequences to another party, often through contractual or insurance mechanisms.

### Accept

Recognize the risk and decide not to take additional action beyond appropriate monitoring or contingency planning.

The correct response depends on the nature and economics of the risk.

## Opportunities

Uncertainty can also create positive outcomes.

An opportunity may have:

- Probability of occurring
- Potential benefit

The script calculates expected opportunity value as:

Expected Value = Probability × Benefit

Opportunities can be actively pursued, enhanced, shared, accepted, or otherwise managed depending on the organizational context.

## Communication planning

Initiation should identify major communication needs.

The script demonstrates a communication plan containing:

- Audience
- Information
- Frequency
- Channel
- Owner

Examples include:

- Executive status reporting
- Project-team coordination
- User communication
- Governance reviews

Communication frequency should reflect decision needs rather than becoming a ritual with no useful information.

## Success criteria

Success criteria describe how the organization will determine whether the project achieved its objectives.

Examples include:

- Average resolution time <= 2.4 days
- System availability >= 99.5%
- User adoption >= 90%
- Cost within approved tolerance

Success criteria should be measurable whenever possible.

## Acceptance criteria

Acceptance criteria are conditions that a specific deliverable must satisfy before it is accepted.

For example:

> Users can create, assign, update, and close service requests.

Acceptance criteria are generally more specific than broad project success criteria.

A project can have:

- Project-level success criteria
- Deliverable-level acceptance criteria
- Business-level benefit measures

These should not be treated as identical.

## Project charter

The project charter is one of the most important initiation artifacts.

The script's charter model includes:

- Project name
- Business need
- Objective
- Sponsor
- Project manager
- High-level scope
- Major deliverables
- Major stakeholders
- Assumptions
- Constraints
- Major risks
- Estimated budget
- Estimated duration
- Success criteria
- Authorization status

A charter should provide enough information to authorize and guide the project without attempting to replace the detailed project management plan.

## Project authorization

A project should have a clear authorization decision.

The script models four possible decisions:

- Approve
- Reject
- Defer
- Revise

A project may be deferred because:

- Funding is unavailable
- Strategic priorities have changed
- Dependencies are unresolved
- Feasibility evidence is insufficient
- A better investment opportunity exists

A project may be revised when the underlying idea is sound but its scope, cost, timing, or approach needs modification.

## Initiation gate

The script implements an initiation readiness gate using several conditions:

- Business case ready
- Sponsor identified
- Objective defined
- Feasibility assessed
- Major risks identified
- Scope boundary defined

This produces a readiness score and a recommended decision.

A real organization may use more complex approval criteria.

## Project prioritization

Organizations often have more potential projects than available resources.

A scoring model can help compare candidate projects.

The example considers:

- Strategic alignment
- Financial value
- Urgency
- Feasibility
- Risk

Risk is inverted in the calculation so that higher risk reduces the overall score.

A weighted score is useful for structuring discussion, but it should not replace management judgment.

## Weighted scoring

The general structure is:

Weighted Score = Σ (Criterion Score × Criterion Weight)

Weights should normally sum to 1.

For example:

- Strategic alignment: 30%
- Financial value: 25%
- Urgency: 15%
- Feasibility: 20%
- Risk: 10%

The selected criteria and weights should reflect organizational strategy.

## Trade-offs

Project decisions frequently involve trade-offs.

Examples include:

- Build versus buy
- Speed versus cost
- Scope versus schedule
- Customization versus standardization
- Short-term benefit versus long-term capability
- Innovation versus certainty

The script compares alternative approaches using a simple weighted model.

A model is useful only when its assumptions are transparent.

## Predictive project initiation

A predictive approach generally places greater emphasis on establishing high-level scope, constraints, governance, and planning assumptions before execution.

It can be useful when:

- Requirements are relatively stable
- Regulatory expectations are well defined
- Physical construction is involved
- Changes are expensive
- Sequencing is strongly constrained

Initiation still does not mean every execution detail must be known before authorization.

## Agile project initiation

Agile environments often emphasize:

- Product vision
- Customer problem
- Desired outcomes
- Product goals
- Initial backlog
- Value hypothesis
- Incremental delivery
- Learning and feedback

Detailed requirements can evolve during delivery.

This does not mean Agile projects do not need initiation. They require clarity about purpose, value, ownership, constraints, and direction even when detailed scope is intentionally uncertain.

## Hybrid initiation

Hybrid projects combine predictive and iterative practices.

For example:

- Governance and funding may follow a predictive structure.
- Product development may occur through iterative increments.
- Regulatory controls may be fixed.
- User-facing features may evolve through feedback.

Hybrid initiation is useful when different parts of the project have different levels of uncertainty.

## Minimum viable product

The script demonstrates an MVP model.

An MVP contains the smallest set of capabilities needed to test or deliver the intended value.

For a customer-service platform, initial capabilities might include:

- Request creation
- Assignment
- Status tracking
- Basic reporting

Advanced predictive analytics might deliberately be excluded from the first release.

MVP does not mean low quality. It means deliberately limiting initial scope so that useful value or learning can be achieved without unnecessary features.

## High-level requirements

Initiation should establish enough requirements to understand feasibility, value, scope, and major risks.

The script demonstrates requirements with:

- Requirement identifier
- Description
- Priority
- Source

Early requirements may be intentionally less detailed than final specifications.

## Initiation versus planning

This distinction is important.

| Area | Initiation | Planning |
|---|---|---|
| Business need | Establish | Refine |
| Objective | Define | Baseline and manage |
| Scope | High-level boundaries | Detailed scope |
| Schedule | High-level duration | Detailed schedule |
| Cost | Initial estimate | Detailed cost baseline |
| Risks | Major risks | Detailed risk responses |
| Stakeholders | Identify major stakeholders | Detailed engagement |
| Resources | High-level needs | Detailed allocation |
| Governance | Establish | Operate and refine |

The initiation phase answers:

> Should and can we undertake this project?

Planning answers:

> How exactly will we execute and control it?

## Governance

Governance establishes who has decision authority.

The script models decisions such as:

- Charter approval
- Major scope-change approval
- Technical approval
- Final deliverable acceptance

Clear decision rights reduce ambiguity and prevent decisions from becoming unnecessarily slow.

## RAID

RAID is commonly used as a convenient grouping for:

- Risks
- Assumptions
- Issues
- Dependencies

The exact meaning and use of RAID varies between organizations.

The important principle is to make important project conditions visible, assigned, and actionable.

## Change control

Once a project is authorized, new requests can arise.

The script models a change request containing:

- Change description
- Cost impact
- Schedule impact
- Scope impact
- Reason
- Status

A project manager may have delegated authority to approve small changes. Larger changes may require escalation.

Real thresholds should be defined by project governance rather than assumed.

## Project initiation documents

Common initiation artifacts include:

- Project idea
- Business case
- Feasibility assessment
- Project charter
- Stakeholder register
- High-level requirements
- Initial risk register
- Assumptions and constraints
- High-level scope statement
- Governance model

Not every organization uses all of these as separate documents.

Some organizations combine several elements into a single business case or charter.

## Initiation checklist

The script contains a reusable readiness checklist covering:

- Business need
- Business value
- Sponsor
- Business owner
- Project manager
- Objective
- Scope
- Stakeholders
- Feasibility
- Cost
- Duration
- Risks
- Assumptions
- Constraints
- Dependencies
- Success criteria
- Governance
- Authorization

The checklist provides a practical control against starting execution with major unanswered questions.

## Decision confidence

Initiation decisions are made under uncertainty.

The script models confidence in areas such as:

- Business need
- Expected benefits
- Technical feasibility
- Cost estimate
- Schedule estimate
- Risk profile

Confidence should not be confused with certainty.

A decision can be reasonable even when uncertainty remains, provided that:

- Important uncertainty is visible.
- Assumptions are explicit.
- Risks are understood.
- The decision is appropriate to the available evidence.
- Further discovery is planned where necessary.

## Sensitivity analysis

Business cases should be tested against changing assumptions.

The script evaluates different benefit scenarios.

For example:

- Benefits 30% lower than expected
- Benefits 15% lower
- Expected benefits
- Benefits 15% higher
- Benefits 30% higher

Sensitivity analysis helps reveal whether a business case depends on highly optimistic assumptions.

A project whose justification disappears after a small unfavorable change may require deeper investigation.

## Break-even analysis

Break-even analysis determines how much activity is required to recover an investment.

The script uses:

Break-even Units = Fixed Cost / Contribution per Unit

Contribution per unit is:

Benefit per Unit - Variable Cost per Unit

This approach can be useful for:

- Product launches
- Subscription businesses
- Transaction systems
- Automation investments
- Capacity expansion

## Resource capacity

A project may be financially attractive but still infeasible because the organization lacks available people or skills.

The script models:

- Monthly capacity
- Allocated hours
- Remaining capacity

Resource analysis should consider:

- Availability
- Skills
- Competing projects
- Organizational dependencies
- Hiring lead time
- Vendor availability
- Critical specialist bottlenecks

## Project complexity

Project complexity can arise from:

- Number of stakeholders
- Number of integrations
- Geographic distribution
- Regulatory requirements
- Uncertainty
- Organizational change
- Technical novelty

The script provides an illustrative complexity score.

Such a score should be calibrated using organizational experience rather than treated as a universal standard.

## Security considerations

Security should be considered during initiation.

Important questions include:

- Does the project handle sensitive information?
- What data will be created, accessed, transferred, or transformed?
- Who owns the data?
- What authentication is required?
- What authorization model is required?
- Are third parties involved?
- Are security reviews required?
- Are privacy requirements relevant?
- What security controls affect cost and schedule?

Discovering a major security requirement immediately before production can create substantial rework.

## Data and privacy considerations

Projects involving data should consider:

- Data ownership
- Data classification
- Storage location
- Retention requirements
- Access controls
- Data quality
- Data transfer
- Third-party processing
- Cross-border movement
- Regulatory requirements

Data requirements can materially affect architecture, cost, schedule, and feasibility.

## Production and implementation considerations

Initiation should consider the future operational environment.

Important questions include:

- Who will operate the solution?
- Who provides support?
- What training is required?
- How will deployment occur?
- What happens if deployment fails?
- What monitoring is needed?
- What performance is expected?
- What are the maintenance costs?
- What happens to the old system?
- How will benefits be measured after launch?
- How will responsibility transfer from the project to operations?

A project is not fully successful merely because its technical deliverables have been produced.

## Performance considerations

The script emphasizes several practical principles:

- Use realistic estimates.
- Represent uncertainty explicitly.
- Separate project costs from recurring operational costs.
- Identify resource bottlenecks early.
- Consider integration complexity.
- Use historical data where available.
- Validate important assumptions.
- Revisit estimates as knowledge improves.

Performance considerations should begin during initiation when they can materially influence architecture, cost, scope, or feasibility.

## Common initiation mistakes

### Starting with a predetermined solution

The organization selects a technology before clearly defining the problem.

### Defining vague objectives

Statements such as "improve efficiency" are difficult to measure.

### Starting without a sponsor

A project without clear authority may struggle with funding, prioritization, and escalation.

### Leaving scope boundaries unclear

Unclear scope creates conflicting expectations.

### Treating estimates as guarantees

Early estimates contain uncertainty.

### Ignoring stakeholders

Affected users and business functions may expose feasibility and adoption problems that are invisible to the project team.

### Ignoring operational ownership

The organization must know who will run and support the result after project closure.

### Ignoring security

Security and privacy requirements can affect the entire solution.

### Using optimism as the primary forecast

A project business case should consider downside scenarios.

### Measuring success only by delivery

Completing the planned outputs does not necessarily produce the intended business outcome.

### Overplanning before authorization

Detailed planning may consume substantial effort before the organization has decided whether the project should proceed.

### Under-investigating major projects

Large investments require sufficient evidence to support the decision.

## Limitations of scoring models

The script uses several numerical models for learning purposes.

These models have limitations.

A weighted project score can create an appearance of objectivity even when the underlying ratings are subjective.

Risk exposure based on probability multiplied by impact is useful for prioritization but does not represent every dimension of uncertainty.

Simple ROI does not fully represent time value of money.

Feasibility scores depend on the quality of the underlying assessment.

Complexity scores are organizational models rather than universal measurements.

These tools should support structured decision-making rather than replace professional judgment.

## Edge cases

Not every project fits a standard financial model.

### Compliance projects

A regulatory project may have negative direct ROI but still be mandatory.

### Safety projects

Safety improvement may be difficult to express as conventional revenue.

### Strategic capability projects

A project may create future capabilities whose value cannot be accurately estimated at initiation.

### Research and innovation

The objective may be to reduce uncertainty rather than produce a predetermined solution.

### Emergency projects

A crisis may require rapid initiation with limited information.

### Highly uncertain projects

The appropriate response may be discovery, experimentation, or staged funding rather than immediate full-scale commitment.

## Staged authorization

For uncertain projects, organizations can divide authorization into stages.

For example:

1. Initial investigation
2. Proof of concept
3. Detailed feasibility
4. Full implementation

This approach can reduce exposure by making larger investment conditional on evidence from earlier stages.

## Practical project initiation workflow

The script models the following sequence:

1. Identify a business problem, opportunity, requirement, or strategic need.
2. Describe the current state and business impact.
3. Investigate the problem without prematurely committing to a solution.
4. Define the desired outcome and measurable objective.
5. Identify the sponsor and business owner.
6. Identify major stakeholders.
7. Explore solution alternatives.
8. Perform high-level feasibility analysis.
9. Develop a business case where appropriate.
10. Define high-level scope and boundaries.
11. Identify assumptions, constraints, dependencies, and major risks.
12. Estimate cost, duration, and resource needs.
13. Define success and acceptance criteria.
14. Establish governance and decision rights.
15. Prepare the charter or equivalent authorization document.
16. Review the initiation package.
17. Approve, reject, defer, or request revision.
18. Move into detailed planning or iterative discovery after authorization.

## Real-world case structure

The script includes a financial-services example involving digital customer onboarding.

The initial problem is a slow manual onboarding process.

The case identifies:

- Current performance
- Business impact
- Desired outcome
- Potential solution
- Sponsor
- Business owner
- Target
- Major risks
- Success measures

This demonstrates how a vague idea can be converted into a structured project proposition.

## Integrated initiation model

The final integrated model combines:

- Project charter
- Feasibility assessment
- Business case
- Stakeholders
- Risks
- Dependencies
- Requirements

This represents the major information that decision-makers may need before authorizing a significant project.

The script also validates the model through executable assertions.

## Python implementation concepts used

The script is also designed to demonstrate useful Python concepts while studying project initiation.

### Classes

Classes represent project-management entities such as:

- Projects
- Stakeholders
- Risks
- Requirements
- Business cases
- Charters
- Dependencies

### Dataclasses

Python dataclasses provide concise structures for records containing related fields.

Examples include:

- `ProjectIdea`
- `ProjectProposal`
- `Stakeholder`
- `Risk`
- `ProjectCharter`
- `BusinessCase`

### Enumerations

Enums represent controlled categories such as:

- Project drivers
- Risk responses
- Authorization decisions
- Delivery approaches
- Stakeholder influence

### Functions

Functions implement calculations and reusable logic such as:

- ROI
- NPV
- Benefit-cost ratio
- PERT estimation
- Risk exposure
- Break-even analysis
- Project scoring
- Complexity assessment

### Validation

The script explicitly rejects invalid conditions such as:

- Probability outside 0 to 1
- Invalid risk ratings
- Negative investment
- Zero or negative cost where a ratio requires positive cost
- Invalid estimate ordering
- Invalid scoring weights

### Assertions

The validation section uses assertions to verify that major calculations and models behave as expected.

This provides a basic form of executable testing.

## Implementation considerations

A production project-initiation system would normally require stronger controls than the educational models in this script.

Possible production concerns include:

- Persistent storage
- Authentication
- Authorization
- Audit trails
- Version control
- Approval workflows
- Role-based access control
- Document management
- Data validation
- Financial-system integration
- Portfolio integration
- Notification mechanisms
- Reporting
- Change history
- Regulatory record retention

The script intentionally remains self-contained and uses standard Python functionality rather than external infrastructure.

## Real-world relevance

Project initiation is important because decisions made before execution influence the conditions under which the project will operate.

Weak initiation can result in:

- Unclear objectives
- Uncontrolled scope
- Inadequate funding
- Unidentified dependencies
- Unmanaged stakeholder expectations
- Unrealistic schedules
- Missing security requirements
- Weak governance
- Poor benefit measurement

Strong initiation does not guarantee project success. It improves the quality of the decision to undertake the project and establishes a clearer foundation for subsequent planning and delivery.

## Key project initiation principles

### Start with the need

Understand the problem or opportunity before committing to a solution.

### Define value

Connect project outputs to outcomes and measurable business benefits.

### Establish authority

A project should have identifiable sponsorship and decision authority.

### Be honest about uncertainty

Early cost, duration, benefit, and risk estimates are rarely perfectly precise.

### Define boundaries

State what the project includes and what it does not include.

### Identify stakeholders early

People affected by the project can influence feasibility, adoption, governance, and benefits.

### Surface uncertainty

Make risks, assumptions, dependencies, and constraints visible.

### Consider security early

Security and privacy can influence scope, architecture, cost, schedule, and feasibility.

### Define success

A project should have measurable criteria for determining whether it achieved its intended objectives.

### Match governance to complexity

Projects involving substantial investment, uncertainty, regulation, or organizational impact generally require appropriate oversight.

### Distinguish initiation from planning

Initiation establishes the reason, direction, boundaries, feasibility, and authorization of the project. Detailed planning determines how the authorized work will be executed and controlled.
