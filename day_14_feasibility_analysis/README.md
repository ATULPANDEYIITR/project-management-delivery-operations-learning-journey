# Feasibility analysis: checking whether a project is practical

## Introduction

Feasibility analysis is the systematic process of determining whether a proposed project can realistically be delivered and whether the expected value justifies the required resources, cost, time, and risk.

A feasibility study does not simply ask whether something is technically possible. A project can be technically achievable while being too expensive, too slow, legally restricted, operationally difficult, poorly supported by market demand, or excessively risky.

A practical feasibility analysis therefore examines several dimensions together:

- Technical feasibility
- Operational feasibility
- Economic and financial feasibility
- Schedule feasibility
- Resource feasibility
- Market feasibility
- Legal and regulatory feasibility
- Risk feasibility

The Python script accompanying this README demonstrates these dimensions through executable calculations, data structures, simulations, validation routines, decision models, and an integrated feasibility assessment.

## Purpose of feasibility analysis

The central purpose of a feasibility study is to improve the quality of a project decision before substantial resources are committed.

Typical decisions include:

- Proceed with the project.
- Proceed conditionally after resolving specific issues.
- Conduct a prototype or pilot before making a larger investment.
- Redesign the proposed solution.
- Delay the project until assumptions become clearer.
- Stop the project because one or more constraints cannot be satisfied.

A feasibility study is therefore a decision-support process rather than a guarantee of project success.

## Feasibility, viability, and desirability

These concepts are related but should not be treated as synonyms.

### Feasibility

Feasibility asks:

> Can the project realistically be delivered under the stated constraints?

Examples include technology availability, team capacity, legal requirements, schedule, and infrastructure.

### Viability

Viability asks:

> Can the project generate sufficient economic, financial, strategic, or organizational value?

A system may be technically feasible but financially unattractive.

### Desirability

Desirability asks:

> Do customers, users, employees, or other stakeholders actually want the proposed outcome?

A product can be feasible and potentially profitable but fail because users do not adopt it.

A strong business case normally requires all three dimensions to be considered.

## Requirements, assumptions, and constraints

A feasibility study should distinguish facts about the proposed project from assumptions and constraints.

### Requirements

Requirements describe what the project must provide.

Functional requirements specify behavior or capabilities. Examples include account creation, application submission, payment processing, or reporting.

Non-functional requirements specify qualities or constraints such as:

- Performance
- Reliability
- Security
- Scalability
- Availability
- Privacy
- Maintainability

The script represents functional and non-functional requirements separately to demonstrate this distinction.

### Assumptions

An assumption is something accepted as true for planning purposes even though it has not been fully established.

Examples include:

- Expected number of customers
- Availability of engineers
- Estimated cloud costs
- Expected adoption rate
- Development productivity

Assumptions are important because feasibility conclusions are conditional on them.

Each important assumption should ideally have:

- A clearly defined value
- A rationale
- An owner
- Evidence
- An indication of uncertainty
- A plan for validation

### Constraints

Constraints limit what solutions are possible.

Common constraints include:

- Budget
- Deadline
- Staffing
- Technology
- Regulatory requirements
- Contractual obligations
- Physical capacity
- Geographic restrictions

Hard constraints require special treatment. If a project cannot satisfy a mandatory legal requirement or contractual obligation, a high average score should not automatically make the project feasible.

## Technical feasibility

Technical feasibility determines whether the required technology, architecture, engineering capability, infrastructure, integrations, performance, reliability, and security requirements can realistically be achieved.

The script implements a simple capability-coverage calculation. Required capabilities are compared with capabilities already available.

The calculation is conceptually:

Technical coverage = available required capabilities / total required capabilities × 100

This is useful for teaching but should not be interpreted as a complete engineering feasibility assessment.

A production technical feasibility study should investigate:

- Technology maturity
- Architecture
- Integration complexity
- Data volume
- Traffic volume
- Performance
- Availability
- Scalability
- Reliability
- Security
- Maintainability
- Infrastructure
- Vendor dependencies
- Technical debt
- Specialist skills
- Prototype results

A missing technical capability does not automatically make a project infeasible. It indicates an uncertainty or capability gap that may require hiring, procurement, outsourcing, architectural changes, or experimentation.

## Operational feasibility

Operational feasibility examines whether the organization can successfully operate and adopt the proposed solution.

Important questions include:

- Will users accept the new process?
- Can employees be trained?
- Can customer support handle the expected demand?
- Who owns the solution after implementation?
- Can operational procedures be changed?
- Is maintenance capacity available?
- Can governance and reporting requirements be supported?
- Is the organization ready for the required change?

The script calculates an operational readiness score from:

- Process fit
- User acceptance
- Support capacity
- Change readiness

An operationally feasible project needs more than a functioning technical system. People, processes, responsibilities, support, and governance must also be workable.

## Financial and economic feasibility

Financial feasibility evaluates whether the expected economic consequences justify the required investment.

The script demonstrates several important financial measures.

### Return on investment

A simple ROI calculation is:

ROI = (Benefits − Costs) / Costs × 100

For example, if a project costs ₹4 million and generates ₹6.5 million in benefits:

ROI = (₹6.5 million − ₹4 million) / ₹4 million × 100

ROI is easy to understand, but it does not fully account for timing or uncertainty.

### Benefit-cost ratio

The benefit-cost ratio is:

Benefit-cost ratio = Total benefits / Total costs

A value greater than 1 means modeled benefits exceed modeled costs under the assumptions used.

### Payback period

Payback period estimates how long it takes for cumulative cash flows to recover the initial investment.

The script supports fractional periods when recovery occurs during a period rather than exactly at its end.

Payback is intuitive but ignores cash flows after the payback point and does not inherently account for the time value of money.

### Net present value

Net present value discounts future cash flows to their present value.

The formula is:

NPV = Σ [Cash flow at period t / (1 + r)^t]

where:

- `r` is the discount rate
- `t` is the period number

A positive NPV indicates that the modeled discounted benefits exceed the modeled discounted costs at the selected discount rate.

NPV is generally more informative than simple ROI when the timing of cash flows matters.

### Internal rate of return

Internal rate of return is the discount rate that makes NPV equal to zero.

The script implements a bisection-based IRR calculation. This approach is transparent and avoids external packages.

IRR requires care because some cash-flow patterns can have:

- No real IRR
- Multiple IRRs
- Extremely unstable results

Consequently, IRR should not be interpreted independently of the underlying cash-flow pattern.

## Break-even analysis

Break-even analysis determines the activity level at which total contribution covers fixed costs.

For a simple unit model:

Break-even units = Fixed costs / (Selling price per unit − Variable cost per unit)

The denominator is the contribution margin per unit.

If selling price equals variable cost, the contribution margin is zero and no finite break-even quantity exists.

If variable cost exceeds selling price, every additional unit increases the loss, so the conventional break-even formula does not produce a meaningful positive operating volume.

The script explicitly raises an error for this situation.

## Schedule feasibility

Schedule feasibility determines whether the project can be completed within the required time.

The script includes a critical-path calculation.

A project consists of tasks with:

- Duration
- Dependencies

The critical path is the longest dependency path through the project. Delaying a critical-path task generally delays the project completion date unless schedule changes are introduced.

The example includes requirements, architecture, backend work, frontend work, integration, testing, and deployment.

Schedule feasibility should consider more than the sum of task estimates. Important factors include:

- Dependencies
- Parallel work
- Resource conflicts
- Approval delays
- Procurement
- Testing
- Rework
- Holidays and leave
- External dependencies
- Regulatory approvals
- Contingency

A schedule that exactly equals the deadline may still be operationally weak because it has little or no buffer.

## Resource feasibility

Resource feasibility examines whether the necessary people, facilities, technology, equipment, infrastructure, and budget are available.

The script demonstrates a basic utilization calculation:

Resource utilization = Required capacity / Available capacity × 100

A result below 100% indicates that modeled capacity is sufficient in pure numerical terms.

That does not mean the team can operate continuously at full utilization. Real projects require capacity for:

- Meetings
- Support
- Defect resolution
- Training
- Documentation
- Coordination
- Leave
- Unexpected work

Resource feasibility should therefore incorporate realistic availability rather than assuming that nominal working hours are fully productive.

## Market feasibility

Market feasibility evaluates whether there is sufficient demand for the proposed product or service.

Important questions include:

- Who is the customer?
- What problem is being solved?
- How severe is the problem?
- How many potential customers exist?
- What alternatives already exist?
- How much are customers willing to pay?
- What adoption rate is realistic?
- How difficult is customer acquisition?
- What is the expected retention?
- How strong is the competition?
- Are there regulatory or distribution barriers?

The script demonstrates a simple revenue estimate based on target population, adoption rate, and annual revenue per customer.

This type of calculation is useful as an initial model but is highly sensitive to adoption assumptions.

A large theoretical population does not automatically represent a realistic addressable market.

## Legal and regulatory feasibility

Legal feasibility evaluates whether the project can comply with applicable laws, regulations, contracts, licenses, policies, standards, and other mandatory obligations.

Examples include:

- Privacy requirements
- Security obligations
- Licensing
- Contractual restrictions
- Industry regulations
- Intellectual property
- Consumer protection
- Data retention
- Employment requirements

The script uses a hard compliance gate.

This is important because mandatory legal conditions should not normally be averaged away. A project with excellent economics may still be infeasible if it cannot legally operate.

## Weighted feasibility scoring

A weighted scoring model combines several criteria according to their relative importance.

The general formula is:

Weighted score = Σ(score × weight) / Σ(weight)

The script represents each criterion with:

- Name
- Score
- Weight
- Rationale

Scores are normalized to a 0 to 100 scale.

An example might assign greater weights to economic and technical feasibility than to less critical dimensions.

Weighted scoring is useful when multiple qualitative and quantitative considerations need to be compared.

It has an important limitation: the final number can create a false impression of precision.

A score of 78.4 does not necessarily mean that a project is exactly 8.4 points more feasible than another project with a score of 70.

The quality of the result depends on:

- Criterion definitions
- Evidence
- Scoring methodology
- Weight selection
- Assumption quality
- Independence of criteria

## Hard gates versus soft scores

One of the most important distinctions in feasibility analysis is between:

- Soft criteria that can be combined into a score
- Hard constraints that must be satisfied

For example:

A project might have:

- Technical score: 90
- Economic score: 92
- Market score: 88
- Legal score: 95

Yet if a mandatory license cannot be obtained, the project cannot simply be declared feasible because the average is high.

The script therefore combines weighted scores with hard gates.

This structure is more robust:

1. Check mandatory conditions.
2. Check critical minimum thresholds.
3. Evaluate weighted feasibility.
4. Investigate risks and uncertainty.
5. Make the decision conditional on documented assumptions.

## Risk analysis

Risk is the possibility that an uncertain event will affect project objectives.

A basic risk model uses:

Risk exposure = Probability × Impact

The script represents risks with:

- Name
- Probability
- Impact
- Mitigation

It also calculates expected financial loss.

For example, a risk with a 20% probability and ₹800,000 impact has an expected loss of:

0.20 × ₹800,000 = ₹160,000

Expected loss is useful for prioritization, but it does not capture every consequence.

Some risks are difficult to monetize, such as:

- Reputation damage
- Safety consequences
- Regulatory consequences
- Strategic damage
- Customer trust
- Employee impact

Risks can also be correlated. Several risks may arise from the same underlying cause, making simple independent expected-value calculations misleading.

## Evidence quality

Feasibility analysis is only as strong as the evidence behind its assumptions.

Evidence can come from:

- Existing operational data
- Prototypes
- Technical experiments
- Customer behavior
- Historical projects
- Supplier quotations
- Contracts
- Market research
- Pilot programs
- Expert judgment

The script classifies evidence as low, medium, or high quality.

This is not a statistical probability measure. It is a structured communication mechanism for distinguishing stronger evidence from weaker assumptions.

A feasibility report should clearly separate:

- Known facts
- Measured values
- Estimates
- Assumptions
- Hypotheses
- Unknowns

## Sensitivity analysis

Sensitivity analysis examines how much the result changes when one assumption changes.

The script performs one-way sensitivity analysis on:

- Number of customers
- Revenue per customer
- Variable cost
- Fixed cost

For each variable, the model tests several values relative to the baseline.

Sensitivity analysis answers:

> Which assumptions matter most to the decision?

It does not answer:

> How likely is each assumption to change?

That second question requires probability or scenario analysis.

## Scenario analysis

Scenario analysis changes multiple assumptions together to represent coherent situations.

The script uses:

- Pessimistic scenario
- Base scenario
- Optimistic scenario

Each scenario changes customers, pricing, variable cost, and fixed cost.

Scenario analysis is useful when variables move together.

For example, in a weak market:

- Customer acquisition may fall.
- Pricing pressure may increase.
- Marketing cost may rise.
- Retention may decline.

Treating those changes independently may produce unrealistic combinations.

## Monte Carlo simulation

Monte Carlo simulation repeatedly samples uncertain inputs and calculates the resulting outcome.

The script runs thousands of simulations using ranges for:

- Customers
- Price
- Variable cost
- Fixed cost

It then calculates:

- Mean profit
- Median profit
- 5th percentile
- 95th percentile
- Probability of loss

Instead of asking for one forecast, Monte Carlo analysis asks:

> What distribution of outcomes is plausible under the assumptions?

This can be useful for understanding downside risk.

The quality of a Monte Carlo model depends on its inputs. Randomly generating numbers does not make a model statistically valid.

A real model should justify:

- Probability distributions
- Distribution parameters
- Correlations
- Historical evidence
- Sampling assumptions

## Decision trees and expected value

Decision trees represent alternative decisions and uncertain outcomes.

The script compares two strategic choices:

- Build immediately
- Delay and validate

Each option has several possible outcomes with associated probabilities and values.

Expected value is calculated as:

Expected value = Σ(probability × outcome value)

Expected value is useful for comparing uncertain alternatives, but it should not be interpreted as a guaranteed result.

A decision-maker may reasonably reject an option with higher expected value if its downside is unacceptable.

This is particularly important for safety-critical, highly regulated, or financially constrained projects.

## Phased investment

Feasibility does not have to be a binary decision made at the beginning.

A project can be divided into stages such as:

1. Discovery
2. Prototype
3. Pilot
4. Full rollout

Each stage produces information that can improve the next decision.

This approach can reduce uncertainty before committing the full investment.

A prototype may test technical feasibility.

A pilot may test:

- User adoption
- Operational readiness
- Performance
- Economics
- Support requirements

Phased investment is particularly valuable when uncertainty is high but the cost of learning is relatively low.

## Dependency analysis

A dependency is an external or internal condition that must be satisfied for a project activity to proceed.

Examples include:

- Vendor approval
- API credentials
- Security review
- Production infrastructure
- App-store approval
- Procurement
- Legal review
- Data availability

Dependencies can become hidden schedule risks.

A project may have sufficient budget and staff but still miss its deadline because a critical external dependency is delayed.

Dependency analysis should identify:

- Dependency owner
- Required date
- Current status
- Failure consequence
- Alternative
- Lead time
- Contingency plan

## Feasibility matrix

A feasibility matrix presents multiple dimensions in a consistent format.

The script classifies scores into:

- Strong
- Moderate
- Weak

A matrix makes weak dimensions visible.

For example, a project may have strong technical and economic feasibility but weak schedule feasibility.

The weak schedule dimension should trigger investigation rather than being hidden by a favorable average.

## Feasibility blockers

A feasibility blocker is a condition that prevents the project from being practically acceptable unless corrected.

Typical blockers include:

- Impossible deadline
- Insufficient funding
- Missing mandatory capability
- Unavailable specialist resources
- Unacceptable regulatory exposure
- Negative economics
- Unresolvable dependency
- Security requirement that cannot be met
- Insufficient customer demand

The script identifies dimensions below a defined threshold.

A blocker should be investigated at root-cause level.

For example:

Weak schedule feasibility may result from:

- Too many dependencies
- Insufficient staff
- Unrealistic task estimates
- Late procurement
- Excessive scope
- Approval delays

Changing the schedule itself may not solve the underlying problem.

## Cost estimation and contingency

Project costs should be decomposed into meaningful categories.

The example includes:

- Engineering
- Design
- Infrastructure
- Testing
- Training
- Legal and compliance

A contingency percentage is then applied.

Contingency provides budget protection against uncertainty, but it should not replace explicit risk analysis.

There is also a risk of double counting.

If a specific risk has already been priced into the cost estimate and a contingency reserve is separately applied for the same uncertainty, the model may overstate expected costs.

## Opportunity cost

Feasibility should not be evaluated only against the question:

> Can we afford this project?

It should also ask:

> What else could we do with the same resources?

Opportunity cost is the value of the best alternative that is forgone.

For example, if two projects require the same engineering team, selecting one prevents the organization from using that capacity for the other.

A project with positive NPV may still be inferior to another feasible project with substantially greater value from the same scarce resources.

## Comparing multiple projects

The script implements multi-criteria project ranking.

Each project receives scores across several dimensions, such as:

- Technical feasibility
- Economic feasibility
- Market feasibility
- Schedule feasibility
- Risk

The projects are then ranked by weighted score.

This approach can help create a structured portfolio comparison.

It should not be the sole decision mechanism because projects can have different:

- Strategic importance
- Regulatory obligations
- Risk profiles
- Capital requirements
- Resource constraints
- Time horizons

## Structured feasibility reports

A feasibility report should make the reasoning traceable.

The script defines a `FeasibilityReport` data structure containing:

- Project name
- Objective
- Feasibility dimensions
- Risks
- Assumptions
- Constraints
- Hard-gate status
- NPV
- IRR
- Recommendation

A professional feasibility report should make it possible for a reviewer to understand not only the decision but also why the decision was reached.

Important report elements include:

- Project objective
- Scope
- Requirements
- Assumptions
- Constraints
- Evidence
- Feasibility assessment
- Cost estimates
- Benefits
- Risks
- Dependencies
- Alternatives
- Sensitivity analysis
- Decision thresholds
- Recommendation
- Conditions attached to the recommendation

## Stage-gate decision making

Stage-gate analysis introduces decision points throughout the project lifecycle.

A possible structure is:

- Concept
- Discovery
- Prototype
- Pilot
- Investment
- Scale

Each stage should answer a progressively stronger feasibility question.

For example:

### Concept gate

Is the problem important enough to investigate?

### Discovery gate

Is there enough evidence that the problem, market, technology, and constraints justify experimentation?

### Prototype gate

Have the most important technical uncertainties been tested?

### Pilot gate

Does real-world evidence support operational and market assumptions?

### Investment gate

Do the combined economics, risks, and evidence justify a larger commitment?

### Scale gate

Can the solution be operated reliably at the intended scale?

This approach limits the amount of capital exposed to early uncertainty.

## Feasibility versus certainty

A feasibility decision should not be interpreted as a prediction of exactly what will happen.

There is a fundamental difference between:

- Feasible under current assumptions
- Certain to succeed

Feasibility means the available evidence indicates that the project can reasonably be executed and justified.

Uncertainty remains because:

- Markets change
- Costs change
- Technology evolves
- Regulations change
- Competitors respond
- Customer behavior differs from forecasts
- Estimates contain errors
- Dependencies fail

The purpose of analysis is to make uncertainty explicit and manageable.

## Common analytical mistakes

### Treating estimates as facts

A forecast of 10,000 customers is not the same as 10,000 confirmed customers.

### Using only one financial metric

ROI may look attractive while NPV is weak or payback is too long.

### Averaging mandatory requirements

A regulatory failure should not disappear inside an overall score.

### Ignoring opportunity cost

A feasible project may still be a poor investment compared with alternatives.

### Ignoring dependencies

External approvals and suppliers can dominate the actual schedule.

### Assuming adoption

Survey interest is not equivalent to actual purchasing or usage behavior.

### Ignoring operational ownership

A system can launch successfully and still fail because nobody is responsible for long-term operation.

### Hiding weak dimensions

Averages can conceal critical weaknesses.

### Double-counting benefits

The same financial benefit should not be counted under multiple categories.

### Ignoring uncertainty

Single-point estimates can create false confidence.

## Bias and governance

Feasibility studies are vulnerable to cognitive and organizational bias.

The script demonstrates several important examples.

### Optimism bias

Teams may underestimate cost, complexity, and delivery time.

### Anchoring

An early estimate may continue influencing later estimates even after new evidence appears.

### Confirmation bias

Decision-makers may select evidence supporting a preferred project.

### Sunk-cost bias

A team may continue an unattractive project because significant money has already been spent.

### Planning fallacy

People often underestimate the time required for complex work.

### Availability bias

Memorable examples may be given more importance than representative evidence.

Governance mechanisms can reduce these problems.

Useful controls include:

- Document assumptions.
- Record evidence.
- Separate facts from estimates.
- Define thresholds before reviewing results.
- Assign assumption owners.
- Use independent review for major investments.
- Record changes to assumptions.
- Reassess when material conditions change.

## Security and privacy feasibility

Security and privacy should be considered during feasibility analysis rather than treated exclusively as implementation concerns.

Important questions include:

- What sensitive data will exist?
- Who can access it?
- How will access be controlled?
- What encryption is required?
- How long will data be retained?
- What third parties will process data?
- What security standards apply?
- What happens during a security incident?
- What audit requirements exist?
- What privacy obligations apply?

A technically functional design can still be infeasible if it cannot satisfy mandatory security or privacy requirements.

## Edge cases

The script intentionally demonstrates several invalid or exceptional conditions.

Examples include:

- Break-even when selling price equals variable cost
- Discount rate of -100% or below
- Adoption rates outside the 0 to 100% range
- Circular task dependencies
- Invalid negative values
- Empty datasets
- Invalid probability distributions
- No IRR within the tested interval

These cases demonstrate an important principle of feasibility modeling:

> A model should reject invalid assumptions rather than silently produce misleading results.

Validation is particularly important when feasibility calculations are later connected to user-entered data or production systems.

## IRR limitations

IRR is convenient but has mathematical limitations.

A cash-flow sequence can have more than one sign change, potentially producing multiple IRRs.

For example, a sequence that changes from negative to positive and then back to negative can produce multiple mathematical roots.

The script therefore uses a bounded bisection approach and returns no result when the chosen interval does not contain a root.

In practical analysis, NPV and the underlying cash flows should remain central even when IRR is reported.

## Monte Carlo limitations

Monte Carlo simulation can give an impression of sophistication without necessarily improving the quality of the analysis.

A simulation is only as meaningful as its model.

If the input ranges are arbitrary, the output distribution is also arbitrary.

A defensible simulation should consider:

- Empirical data
- Historical distributions
- Correlations
- Dependence between variables
- Parameter uncertainty
- Distribution selection
- Scenario structure

The script intentionally uses uniform distributions because they are simple and transparent for educational purposes.

## Model validation

A feasibility model should be tested before it is used for decisions.

The script contains built-in assertions covering:

- ROI
- Benefit-cost ratio
- Break-even
- NPV
- Weighted scoring
- Operational readiness
- Critical path
- Expected value

Testing helps identify programming errors in the calculation layer.

Model validation is broader than software testing. It also asks whether the mathematical representation appropriately reflects the real project.

A technically correct formula can still support a poor decision if the assumptions are unrealistic.

## Performance considerations

Most calculations in the script are computationally lightweight.

The Monte Carlo simulation is the most computationally intensive section because it repeatedly generates inputs and calculates project outcomes.

For a small number of simulations, standard Python is sufficient.

For very large models, performance considerations may include:

- Vectorized numerical operations
- More efficient random-number generation
- Parallel execution
- Efficient data structures
- Reduced repeated calculations
- Profiling before optimization

Performance should not be optimized at the expense of model correctness or transparency.

## Implementation considerations

A production feasibility system should generally separate:

- Input collection
- Validation
- Calculation logic
- Scenario management
- Evidence storage
- Risk management
- Reporting
- Audit history
- Decision approval

The educational script keeps these concepts in one file for portability and learning.

A production implementation would normally require stronger controls around:

- Input validation
- Authentication
- Authorization
- Data integrity
- Versioning
- Audit logs
- Access control
- Reproducibility
- Model governance

## Decision framework

A practical feasibility decision can follow this sequence:

### Define the objective

State exactly what the project is expected to accomplish.

### Define requirements

Identify what the solution must do and what quality levels it must achieve.

### Identify assumptions

Document values that are uncertain but necessary for planning.

### Identify constraints

Separate flexible preferences from mandatory limits.

### Collect evidence

Use prototypes, data, customer research, estimates, supplier information, and operational evidence.

### Evaluate feasibility dimensions

Assess technical, operational, economic, schedule, market, legal, resource, and risk considerations.

### Check hard gates

Verify mandatory conditions independently from weighted scoring.

### Quantify economics

Use appropriate financial measures and cash-flow timing.

### Analyze uncertainty

Use sensitivity, scenario, and probabilistic analysis where justified.

### Evaluate alternatives

Consider competing solutions and opportunity costs.

### Define decision conditions

Specify what must be true for a GO decision and what would trigger reassessment.

## Real-world applications

Feasibility analysis is applicable to many types of projects.

Examples include:

- Software development
- Mobile applications
- Cloud migration
- Data platforms
- Manufacturing facilities
- Infrastructure projects
- Product launches
- Digital transformation
- Business process redesign
- Automation
- Financial products
- Educational platforms
- Healthcare systems
- Construction projects
- Energy projects
- New market entry

The exact feasibility dimensions and decision thresholds should be adapted to the nature of the project.

For example, a construction project may emphasize land, engineering, permits, environmental conditions, materials, contractors, and capital requirements.

A software project may emphasize architecture, integrations, cybersecurity, engineering capacity, data, performance, release schedules, and operational support.

## Relationship between the Python script and the concepts

The Python script is organized progressively.

It begins with definitions and basic data structures, then moves into individual feasibility dimensions.

It subsequently introduces quantitative techniques:

- ROI
- Benefit-cost ratio
- Payback period
- NPV
- IRR
- Break-even
- Weighted scoring
- Risk exposure
- Sensitivity analysis
- Scenario analysis
- Monte Carlo simulation
- Expected value

The later sections integrate these methods into decision gates, project comparisons, structured feasibility reports, and a complete project feasibility model.

The final validation section demonstrates that feasibility calculations should themselves be tested for correctness.

## Important distinctions

Several distinctions are central to good feasibility analysis:

| Concept | Primary question |
|---|---|
| Technical feasibility | Can we build or implement it? |
| Operational feasibility | Can the organization operate and adopt it? |
| Economic feasibility | Is the expected economic value sufficient? |
| Schedule feasibility | Can it be delivered within the required time? |
| Resource feasibility | Do we have the required capacity and resources? |
| Market feasibility | Is there sufficient demand? |
| Legal feasibility | Can it comply with mandatory requirements? |
| Risk feasibility | Are the uncertainties and consequences acceptable? |
| Desirability | Do users actually want it? |
| Viability | Does it create sufficient sustained value? |

No single dimension is sufficient for a comprehensive project decision.

## Practical interpretation of the final decision

A `GO` decision should mean that the project satisfies the defined feasibility thresholds and mandatory conditions under the documented assumptions.

A `CONDITIONAL GO` should mean that the project may be acceptable but requires specified issues to be resolved or validated.

A `NO-GO` should mean that the project does not currently satisfy important feasibility requirements or that the expected value does not justify the identified constraints and risks.

The decision should always be interpreted in relation to the assumptions, evidence, constraints, and thresholds used by the analysis.

## Key formulas used

### ROI

ROI = (Benefits − Costs) / Costs × 100

### Benefit-cost ratio

Benefit-cost ratio = Benefits / Costs

### Break-even units

Break-even units = Fixed costs / Contribution margin per unit

### Risk exposure

Risk exposure = Probability × Impact

### Expected value

Expected value = Σ(Probability × Outcome)

### NPV

NPV = Σ[Cash flow at time t / (1 + discount rate)^t]

### Weighted feasibility score

Weighted score = Σ(Score × Weight) / Σ(Weight)

These formulas are useful because they convert selected assumptions into measurable decision indicators. Their usefulness still depends on whether the underlying assumptions and definitions are appropriate.

## Limitations of feasibility analysis

Feasibility analysis has inherent limitations.

It cannot eliminate uncertainty.

It cannot guarantee project success.

It may contain subjective scoring.

It may omit important variables.

Financial forecasts can be inaccurate.

Probabilities may be difficult to estimate.

Market behavior may change after the analysis.

Regulatory requirements may change.

Technology may evolve.

A feasibility report should therefore be treated as a decision instrument that should be updated when material assumptions change, not as a permanent statement that a project will succeed.
