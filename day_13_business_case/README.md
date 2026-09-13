# Business case: understanding why a project should be undertaken

## Topic introduction

A business case is a structured argument for undertaking a project, program, investment, or change initiative. Its purpose is not simply to describe a proposed solution. Its central purpose is to establish whether the organization has a sufficiently strong reason to invest resources in the proposed change.

A sound business case connects a business problem or opportunity to measurable objectives, alternative courses of action, expected benefits, costs, risks, strategic priorities, implementation feasibility, and an investment recommendation.

The Python script accompanying this README presents these concepts progressively. It begins with basic terminology and develops into financial analysis, risk analysis, option scoring, scenario analysis, sensitivity analysis, feasibility assessment, governance, benefit realization, and structured decision-making.

## Why a business case is required

Organizations have limited money, people, time, technology capacity, and management attention. Approving one project can prevent another project from receiving those resources. A business case provides evidence for deciding whether a particular investment deserves priority.

The central questions are:

- What problem exists?
- How significant is the problem?
- What opportunity is available?
- What happens if the organization does nothing?
- What objectives should the project achieve?
- What alternatives are available?
- Why is the preferred option better than the alternatives?
- What will the project cost?
- What benefits will it generate?
- What risks could reduce those benefits?
- Does the project support organizational strategy?
- Is the organization capable of implementing it?
- What evidence is sufficient to authorize the investment?

A project should not normally be justified merely because a technology is available or because a stakeholder prefers a particular solution.

## Problem before solution

A strong business case starts with the business problem or opportunity rather than immediately selecting a solution.

For example, saying that an organization should build a new customer-support application is a solution statement. It does not establish why the investment is necessary.

A stronger business statement could identify that average support resolution time is 48 hours against a target of 12 hours and that this delay is associated with higher support costs and customer dissatisfaction.

The distinction matters because several different solutions might address the same problem. A process redesign, purchased software, automation, organizational change, or custom technology could all be alternatives.

The business case should therefore establish the need before selecting the response.

## Current state and baseline

The current state describes how the organization performs before the project is implemented.

A baseline provides the reference point for measuring improvement. Common baseline measures include:

- Revenue
- Operating cost
- Processing time
- Error rate
- Customer satisfaction
- Employee productivity
- Transaction volume
- Complaints
- Defect rate
- Capacity utilization
- Compliance incidents

The Python script represents the current state with a `CurrentState` class. It calculates annual operating cost from transaction volume and cost per transaction.

A baseline is essential because a claimed benefit has little meaning without a comparison point.

If the current processing time is 48 hours and the target is 12 hours, the project has a clearly defined improvement objective. If the current state is unknown, the credibility of the benefit forecast is weaker.

## Business objectives

Business objectives describe what the organization wants to achieve.

Good objectives should be measurable where practical. Examples include:

- Reduce average processing time from 48 hours to 12 hours.
- Reduce annual operating cost from $1.02 million to $750,000.
- Increase customer satisfaction from 68 to 85 points.
- Reduce transaction error rates by 40%.
- Increase capacity without proportionally increasing headcount.

The script uses an `Objective` class to store the baseline, target, measurement unit, and desired direction of change.

Objectives should be distinguished from project activities.

For example:

- Activity: implement a new software platform.
- Output: operational support platform.
- Outcome: employees resolve requests faster.
- Benefit: lower operating cost and improved customer experience.

The activity describes what the project does. The benefit describes why the investment matters.

## Outputs, outcomes, and benefits

These concepts are closely related but should not be treated as interchangeable.

### Output

An output is something produced by the project.

Example:

A customer-support platform.

### Outcome

An outcome is a change resulting from using the output.

Example:

Support employees resolve customer requests faster.

### Benefit

A benefit is a measurable or strategically meaningful advantage created by the outcome.

Example:

Lower support costs and higher customer satisfaction.

This distinction prevents business cases from confusing delivery with value.

Completing a project does not automatically mean that the expected benefits have been achieved.

## Strategic alignment

A project may be financially attractive but strategically inappropriate. A project may also have limited direct financial returns while being strategically necessary.

Strategic alignment examines whether the project supports organizational priorities such as:

- Revenue growth
- Customer experience
- Operational efficiency
- Market expansion
- Digital transformation
- Technology modernization
- Risk reduction
- Regulatory readiness
- Business continuity

The Python script demonstrates weighted strategic scoring. Each strategic objective receives a weight and a score. The weighted scores are combined to estimate the project's strategic alignment.

The weighting mechanism recognizes that not every strategic objective has equal importance.

## Options analysis

A business case should normally compare credible alternatives.

Typical options include:

- Do nothing
- Improve the existing process
- Purchase an existing solution
- Build a custom solution
- Outsource the capability
- Use a hybrid solution
- Implement the change in phases

The script creates several project options and records implementation cost, operating cost, expected benefit, implementation duration, risk, strategic alignment, and qualitative value.

The preferred option should be selected because it provides an appropriate balance of value, cost, risk, feasibility, and strategic fit.

The most expensive option is not automatically the best option. The option with the highest financial return is also not automatically the best option if it creates unacceptable operational or strategic risk.

## The do-nothing option

The do-nothing option establishes what happens if the proposed project is not undertaken.

This is important because inaction can have a cost.

The current state may produce:

- Increasing operating costs
- Lost revenue
- Customer attrition
- Regulatory exposure
- Technical debt
- Security vulnerabilities
- Reduced productivity
- Missed market opportunities
- Increasing maintenance costs

The Python script models the cost of continuing with the current state when annual costs increase over time.

The do-nothing case provides the counterfactual against which project alternatives can be evaluated.

## Opportunity cost

Opportunity cost is the value of the best alternative use of constrained resources.

If an organization can invest its resources in only one of two projects, selecting Project A means giving up the opportunity to obtain the return from Project B.

The script demonstrates this concept by comparing the return from a chosen project with the return from the best alternative.

Opportunity cost is particularly important in portfolio-level investment decisions.

## Benefits

Benefits are the improvements expected from a project.

The script classifies benefits into several categories.

### Financial benefits

These can be represented directly in monetary terms.

Examples include:

- Increased revenue
- Reduced labor cost
- Reduced operating expenditure
- Reduced transaction costs
- Reduced losses

### Operational benefits

These improve the way work is performed.

Examples include:

- Faster processing
- Higher productivity
- Fewer errors
- Greater capacity
- Reduced cycle time

### Customer benefits

These affect customer experience or commercial behavior.

Examples include:

- Higher satisfaction
- Lower churn
- Improved retention
- Faster response times

### Strategic benefits

These support long-term organizational direction.

Examples include:

- New market capability
- Technology modernization
- Improved scalability
- New business models

### Compliance benefits

These result from meeting legal, regulatory, contractual, or internal requirements.

### Risk-reduction benefits

These represent losses that may be avoided through the project.

### Intangible benefits

These can include reputation, trust, employee morale, organizational learning, or brand value.

Not every benefit should be converted into money when doing so would require weak or artificial assumptions.

## Benefit realization

Forecast benefits and realized benefits are different.

A business case may forecast $1 million of annual benefit. The organization will only realize that benefit if the required changes actually occur.

Benefit realization depends on factors such as:

- User adoption
- Process redesign
- Management behavior
- Data quality
- Technical reliability
- Operational capacity
- Training
- Change management
- Market conditions

The Python script models theoretical benefits, adoption rates, and realization rates.

For example, if the theoretical benefit is $1 million, adoption is 70%, and the realization rate is 90%, the realized value will be lower than the theoretical maximum.

A credible business case should identify who owns each benefit and how it will be measured.

## Costs

A project cost is broader than the initial implementation budget.

Relevant cost categories can include:

- Capital expenditure
- Software licenses
- Infrastructure
- Development
- Consulting
- Procurement
- Migration
- Integration
- Training
- Change management
- Operations
- Maintenance
- Support
- Security
- Compliance
- Vendor management
- Decommissioning

The complete economic evaluation should consider the project lifecycle rather than only the initial purchase price.

## Total cost of ownership

Total cost of ownership, or TCO, estimates the complete cost of owning and operating a solution over a defined period.

The Python script calculates TCO using:

- Initial implementation cost
- Annual operating cost
- Maintenance
- Training
- Exit or decommissioning cost
- Number of years

TCO is particularly useful when comparing alternatives with different pricing structures.

A solution with a low implementation price may have high recurring costs. A more expensive implementation may have lower long-term operating costs.

## Return on investment

Simple ROI expresses the net gain relative to the investment.

A basic formulation is:

ROI = Net gain / Investment

For example, an investment of $500,000 producing a $200,000 net benefit has a simple ROI of 40% for the period being measured.

ROI is easy to communicate but has important limitations.

It does not inherently account for:

- Timing of cash flows
- Different project durations
- Discount rates
- Risk
- Cash-flow volatility
- Benefits after the measurement period

ROI is therefore useful as one metric rather than as the complete investment decision.

## Payback period

Payback period measures how long it takes for cumulative benefits or cash flows to recover the initial investment.

The simplified formula used in the script is:

Payback period = Initial investment / Annual cash benefit

An investment of $1 million with an annual benefit of $250,000 has a simple payback period of four years.

A shorter payback can be attractive because the organization recovers its initial investment sooner.

The limitation is that simple payback ignores the value of cash flows received after the payback point and normally does not account for the time value of money.

## Net present value

Net present value, or NPV, accounts for the time value of money.

A future cash flow is worth less today because receiving money later has an economic cost.

The present value of a future cash flow is:

PV = Cash flow / (1 + r)^t

where:

- PV is present value.
- r is the discount rate.
- t is the time period.

NPV is calculated as the present value of future cash flows minus the initial investment.

A positive NPV means that the forecast future cash flows exceed the initial investment after applying the specified discount rate.

A negative NPV means that the forecast value is insufficient to recover the investment at that discount rate.

The Python script implements NPV without external financial packages.

## Internal rate of return

Internal rate of return, or IRR, is the discount rate at which the NPV becomes zero.

Conceptually:

NPV = 0

IRR is often compared with a required return or hurdle rate.

The script implements an approximate IRR calculation using the bisection method. This is useful for demonstrating the numerical logic behind IRR rather than relying on a specialized financial library.

IRR should be interpreted carefully when cash flows change signs multiple times because multiple mathematical IRRs can exist.

## Benefit-cost ratio

The benefit-cost ratio compares discounted benefits with discounted costs.

Benefit-cost ratio = Discounted benefits / Discounted costs

A ratio greater than 1 means that discounted benefits exceed discounted costs under the model assumptions.

The metric is useful for comparing projects, particularly when investment decisions involve multiple programs with different cost structures.

## Time value of money

The same nominal amount has different economic values depending on when it is received.

For example, receiving $1 million immediately is not economically equivalent to receiving $1 million five years from now.

The Python script calculates present value using different discount rates to demonstrate this effect.

A higher discount rate reduces the present value of future cash flows.

The choice of discount rate should follow the organization's financial framework and the nature of the investment rather than being selected simply to make a project appear attractive.

## Cash-flow modeling

A business case should show when costs and benefits occur.

The script uses a `CashFlowYear` class to represent:

- Benefits
- Operating costs
- Capital costs
- Net cash flow
- Cumulative cash flow

Timing matters because two projects with identical total benefits can have very different economic values if one produces benefits earlier.

## Risk

A business case should not present expected benefits as guaranteed outcomes.

Risk represents uncertainty that can affect project objectives.

Common project risks include:

- Implementation delays
- Cost overruns
- Low adoption
- Vendor dependency
- Integration failures
- Data-quality problems
- Security incidents
- Regulatory changes
- Resource shortages
- Market changes

The script represents risk using probability and impact.

Expected loss is calculated as:

Expected loss = Probability × Impact

For example, a 25% probability of a $300,000 loss produces an expected loss of $75,000.

Expected value is useful for quantitative analysis but does not remove uncertainty from the actual project.

## Probability-impact risk scoring

Organizations often use a probability-impact matrix.

The Python script demonstrates a simple five-point scoring model:

Risk score = Probability score × Impact score

A score of 5 × 5 represents a substantially higher risk level than a score of 1 × 2.

Risk scoring is useful for prioritization, but the scale should be defined consistently within the organization.

## Expected monetary value

Expected monetary value, or EMV, combines multiple possible outcomes with their probabilities.

The formula is:

EMV = Σ Probability × Outcome

The script demonstrates optimistic, most-likely, and pessimistic scenarios.

EMV is not a prediction that the expected value will necessarily occur. It represents the probability-weighted mathematical expectation across the modeled outcomes.

## Sensitivity analysis

Sensitivity analysis tests how strongly the business case depends on individual assumptions.

The Python script changes the expected benefit while holding other assumptions constant and recalculates NPV.

This helps identify assumptions that have a material effect on the investment decision.

If a small change in expected benefits changes NPV from strongly positive to strongly negative, the project has high sensitivity to that assumption.

Important sensitivity variables can include:

- Revenue
- Adoption
- Operating cost
- Implementation cost
- Benefit realization
- Project duration
- Discount rate
- Transaction volume

## Scenario analysis

Scenario analysis changes multiple assumptions together to represent different possible futures.

The script models:

- Optimistic scenario
- Base case
- Pessimistic scenario

Each scenario has different benefit and cost multipliers.

Scenario analysis is different from sensitivity analysis.

Sensitivity analysis normally changes one important assumption at a time.

Scenario analysis changes a group of assumptions to represent a coherent future state.

## Feasibility

A financially attractive project may still be impossible to implement.

Feasibility can include:

- Technical feasibility
- Operational feasibility
- Financial feasibility
- Legal feasibility
- Organizational feasibility

The script represents these dimensions using scores and checks whether each dimension meets a minimum threshold.

Feasibility should be assessed independently from financial attractiveness.

A project can have a positive NPV and still fail because the organization lacks the technical capability, implementation capacity, regulatory approval, or operational readiness required to deliver it.

## Assumptions

Business cases contain assumptions because future conditions cannot be known with certainty.

Examples include:

- Transaction volume will remain stable.
- Users will adopt the new process.
- Implementation will finish within a specified period.
- Savings can be converted into economic value.
- Market demand will remain sufficient.
- Vendor pricing will remain within expected limits.

The Python script records assumptions together with confidence levels and validation methods.

Strong business cases distinguish:

- Verified facts
- Estimates
- Assumptions
- Forecasts
- Uncertainties

This distinction improves transparency.

## Data quality

Financial calculations can be mathematically correct while still producing a poor decision if the input data is unreliable.

For example, a forecast may use an estimated productivity improvement without historical evidence or a reliable pilot.

Important data-quality questions include:

- Where did the number come from?
- Is the source reliable?
- Is the baseline current?
- Is the measurement method consistent?
- Is the value independently validated?
- What confidence should be assigned to the estimate?

The script demonstrates confidence-based data-quality checks.

## Strategic necessity

Not every project should be evaluated only through direct financial return.

Projects involving the following areas may be strategically or legally necessary:

- Regulatory compliance
- Cybersecurity
- Safety
- Business continuity
- Critical infrastructure
- Mandatory contractual obligations

A compliance project may produce little direct revenue while avoiding a potentially significant legal or operational consequence.

The business case should therefore distinguish between discretionary investments and investments required to maintain acceptable levels of risk or compliance.

## Security considerations

Security can materially affect the economics and feasibility of a project.

A business case should consider:

- New attack surfaces
- Sensitive data
- Identity and access management
- Third-party dependencies
- Security monitoring
- Incident response
- Business continuity
- Regulatory exposure
- Security implementation costs

Security should be considered during investment analysis rather than added only after a project has already been approved.

## Opportunity cost

Opportunity cost becomes important when resources are constrained.

For example, a project may require scarce engineering capacity. Assigning that team to one initiative prevents it from delivering another initiative during the same period.

A business case should therefore consider the alternatives that the organization is giving up.

## Sunk costs

Sunk costs are costs that have already been incurred and cannot be recovered.

Future investment decisions should generally focus on future incremental costs and benefits rather than allowing previous spending to dictate future decisions.

The fact that an organization has already spent a large amount on a failing initiative does not automatically justify spending more.

This is commonly associated with the sunk-cost fallacy.

## Break-even analysis

Break-even analysis determines the level of activity required for benefits or contribution to cover fixed costs.

The script uses:

Break-even units = Fixed cost / Contribution margin per unit

where:

Contribution margin per unit = Revenue per unit − Variable cost per unit

Break-even analysis is particularly useful for revenue-generating projects, products, and operational changes.

## Marginal analysis

Marginal analysis examines whether an additional increment of investment creates enough additional value.

For example, an additional feature might generate $180,000 of benefit at an additional cost of $120,000.

Its marginal net value would be:

$180,000 − $120,000 = $60,000

Marginal analysis helps prevent unnecessary scope expansion and supports prioritization of optional capabilities.

## Weighted option scoring

Some project decisions cannot be evaluated adequately through financial metrics alone.

The Python script uses weighted criteria including:

- Financial value
- Strategic alignment
- Customer value
- Implementation feasibility
- Risk profile
- Time to value

Each criterion receives a weight and each option receives a score.

The weighted score is:

Weighted score = Σ Weight × Score

This approach creates a structured comparison between alternatives.

The weights should reflect actual organizational priorities rather than being chosen merely to produce a preferred outcome.

## Real options

Traditional NPV assumes a particular path through the future. Some projects create flexibility that has additional strategic value.

Examples include:

- A pilot that creates the option to scale.
- A modular system that allows future expansion.
- A discovery phase that reduces uncertainty before major investment.
- A technology foundation that enables future products.
- A phased rollout that permits abandonment if results are poor.

This flexibility can be particularly valuable when uncertainty is high.

## Stage gates

A staged investment approach limits exposure when uncertainty is substantial.

A typical structure is:

Discovery → Pilot → Evidence review → Limited rollout → Full implementation

At each gate, decision-makers can review evidence before committing additional resources.

Evidence may include:

- Validated demand
- Technical feasibility
- User adoption
- Updated costs
- Security results
- Regulatory approval
- Benefit realization
- Risk levels

Stage gates help prevent large investments from being committed before critical assumptions are tested.

## Business case versus project plan

A business case and a project plan serve different purposes.

### Business case

Explains why the investment should be made and what value is expected.

### Project charter

Provides formal authorization and establishes high-level project boundaries.

### Project plan

Explains how the approved project will be delivered.

### Benefits realization plan

Explains how expected benefits will be measured, owned, and achieved.

Confusing these documents can result in a technically detailed project without a sufficiently strong investment rationale.

## Governance

Business case governance defines who is accountable for the investment and its results.

Typical responsibilities include:

### Executive sponsor

Provides strategic sponsorship and approves major investment decisions.

### Business owner

Owns business outcomes and benefit realization.

### Project manager

Coordinates delivery, schedule, resources, risks, and dependencies.

### Finance

Reviews financial assumptions, costs, benefits, and investment economics.

### Risk and compliance

Reviews material risks and regulatory requirements.

### Technology

Assesses technical feasibility, architecture, integration, and security.

### Users

Provide operational requirements and adoption feedback.

Clear ownership prevents the business case from becoming a document with no accountability after approval.

## Decision gates

A structured investment decision can use several gates:

1. Material business need
2. Evidence quality
3. Strategic alignment
4. Alternative analysis
5. Financial attractiveness
6. Risk acceptability
7. Technical feasibility
8. Operational feasibility
9. Organizational readiness
10. Benefit ownership
11. Governance readiness

A project should not necessarily proceed simply because it passes one dimension.

## Business case quality

A strong business case normally contains:

- A clearly defined problem or opportunity
- A credible current-state baseline
- Consequences of doing nothing
- Strategic objectives
- Measurable outcomes
- Alternative options
- A preferred option
- Complete lifecycle costs
- Quantified benefits where credible
- Benefit ownership
- Assumptions
- Constraints
- Risks
- Mitigation strategies
- Financial analysis
- Sensitivity analysis
- Scenario analysis
- Feasibility assessment
- Implementation approach
- Governance
- Decision criteria

The Python script includes a `BusinessCaseQuality` class that demonstrates a simple quality score across these dimensions.

## Common mistakes

### Starting with the solution

A preferred technology should not be treated as proof that a project is necessary.

### Ignoring the do-nothing case

Without a baseline or counterfactual, the value of the proposed project is difficult to judge.

### Overstating benefits

Forecasts should be based on credible evidence rather than optimistic assumptions.

### Underestimating total cost

Implementation cost alone is insufficient. Training, support, maintenance, migration, security, and retirement can materially change the economics.

### Ignoring adoption

A solution that is delivered but not used may generate little or no expected benefit.

### Double-counting benefits

The same economic improvement should not be counted under multiple benefit categories.

For example, labor savings and productivity gains may represent the same underlying economic effect.

### Confusing revenue with profit

Additional revenue is not the same as additional economic value. Associated costs and cash effects must be considered.

### Ignoring risk

A forecast should include uncertainty and downside scenarios.

### Using poor baselines

A weak baseline produces weak benefit measurements.

### Sunk-cost thinking

Previous spending should not automatically determine whether future spending is justified.

## Revenue, profit, and cash flow

Revenue, profit, and cash flow are different concepts.

A project may generate $2 million of additional revenue while also requiring $1.5 million of additional operating cost.

The resulting operating contribution is substantially lower than the revenue increase.

Investment analysis may also need to consider:

- Taxes
- Working capital
- Capital expenditure
- Depreciation
- Financing
- Timing
- Cash conversion

For investment decisions, the economic meaning of cash flows must be considered rather than relying solely on revenue growth.

## Financial metric comparison

### ROI

Useful for communicating simple return relative to investment.

Limitation: does not naturally account for timing and risk.

### Payback

Useful for understanding how quickly investment is recovered.

Limitation: ignores benefits after the payback point and often ignores discounting.

### NPV

Useful for evaluating value after accounting for the time value of money.

Limitation: depends strongly on cash-flow forecasts and discount-rate assumptions.

### IRR

Useful for expressing project return as a percentage.

Limitation: interpretation becomes complicated when cash flows change signs multiple times.

### Benefit-cost ratio

Useful for comparing discounted benefits against discounted costs.

Limitation: can require judgment about benefit valuation.

### TCO

Useful for understanding lifecycle cost.

Limitation: TCO alone does not establish whether the benefits justify the cost.

No single metric should automatically determine every investment decision.

## Limitations of business cases

A business case is a decision model, not a guarantee of future performance.

Its quality depends on:

- Data quality
- Forecast accuracy
- Assumptions
- Market conditions
- Execution capability
- Adoption
- Risk management
- Measurement methods

A project with a positive NPV can still fail because of poor implementation.

A project with a negative direct ROI can still be justified if it is necessary for regulatory, safety, cybersecurity, or strategic reasons.

The decision therefore requires judgment as well as calculation.

## Production and implementation considerations

Once a project is approved, the business case should remain connected to execution.

Important implementation considerations include:

- Scope clarity
- Resource availability
- Delivery dependencies
- Procurement
- Technology readiness
- Data migration
- Integration
- Security
- Training
- Change management
- Operational support
- Vendor management
- Benefits tracking

Material changes to assumptions should trigger a review of the business case.

A business case that becomes materially different during delivery should not be treated as permanently valid merely because it was approved earlier.

## End-to-end business case structure

A practical business case can be organized around the following sections:

1. Executive decision required
2. Problem or opportunity
3. Current state and baseline
4. Strategic context
5. Objectives and success measures
6. Options considered
7. Preferred option
8. Scope and assumptions
9. Benefits
10. Costs and TCO
11. Financial analysis
12. Risk analysis
13. Dependencies and constraints
14. Implementation approach
15. Governance
16. Benefit realization
17. Decision and approval criteria

The exact structure may vary by organization, but the underlying decision logic remains similar.

## Integrated decision framework

The script brings the major concepts together through the following sequence:

**Need → Evidence → Objectives → Alternatives → Value → Economics → Risk → Strategy → Feasibility → Benefits → Governance → Decision**

### Need

Is the problem or opportunity material enough to justify action?

### Evidence

Is the current state supported by credible data?

### Objectives

Are the desired outcomes measurable?

### Alternatives

Have reasonable alternatives, including doing nothing, been considered?

### Value

Do the expected benefits justify the required investment?

### Economics

Do financial metrics support the proposed investment under reasonable assumptions?

### Risk

What could prevent the expected value from being achieved?

### Strategy

Does the project support organizational priorities?

### Feasibility

Can the organization implement and operate the proposed solution?

### Benefits

Are benefits measurable and assigned to responsible owners?

### Governance

Are decision rights, review points, and investment gates clear?

### Decision

Is there enough evidence to authorize the next level of investment?

## Python implementation concepts demonstrated

The study script also demonstrates practical Python techniques relevant to business-case analysis.

It uses:

- Functions for financial calculations
- Classes for business entities
- Dataclasses for structured information
- Lists and dictionaries for analytical data
- Type annotations
- Properties for derived values
- Input validation
- Exception handling
- Assertions
- Scenario modeling
- Weighted scoring
- Numerical approximation
- Iterative calculations
- Sensitivity analysis
- Risk calculations
- Financial calculations
- Decision rules

The implementation is intentionally based on the Python standard library so that the study file can run without external dependencies.

## Edge cases handled

The script demonstrates validation for several important cases, including:

- Zero investment
- Zero annual benefit
- Negative annual benefit
- Invalid risk probability
- Invalid scenario probabilities
- Invalid discount rates
- Invalid scoring ranges
- Missing evaluation criteria
- Negative impacts
- Zero contribution margins

Handling such cases is important because business-case models can produce misleading results if invalid assumptions are silently accepted.

## Practical relevance

Business cases are used across many organizational contexts, including:

- Technology transformation
- Enterprise software implementation
- Infrastructure investment
- Product development
- Process automation
- Digital transformation
- Customer-experience programs
- Cost-reduction initiatives
- Cybersecurity programs
- Compliance programs
- Business continuity
- New market entry
- Capacity expansion
- Outsourcing decisions
- Organizational change

The underlying principle is consistent: scarce resources should be allocated using a transparent assessment of need, value, cost, risk, feasibility, and strategic importance.

## Core analytical principle

The fundamental purpose of a business case is not to prove that a predetermined project is good.

It is to provide enough structured evidence for a responsible investment decision.

A strong business case therefore remains open to several possible outcomes:

- Proceed
- Proceed with conditions
- Conduct a pilot
- Delay the investment
- Redesign the proposal
- Select an alternative
- Reject the project

The quality of the decision depends on the quality of the evidence, assumptions, alternatives, financial analysis, risk assessment, and governance surrounding the proposed investment.
