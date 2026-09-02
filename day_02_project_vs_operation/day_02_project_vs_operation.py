"""
PROJECT VS OPERATIONS
=====================

A detailed, self-contained learning program covering the distinction between
projects and operations from basic concepts to advanced practical cases.

The program uses only Python's standard library.

Topics covered:
- Meaning of a project
- Meaning of operations
- Temporary vs continuous work
- Unique vs repetitive work
- Objectives and success criteria
- Project and operational lifecycles
- Planning
- Scope
- Schedule
- Cost and budgeting
- Resources and capacity
- Stakeholders
- Risk and issues
- Quality
- Change management
- Governance
- Metrics and KPIs
- Roles and responsibilities
- Project closure
- Transition to operations
- Project, program, portfolio and operations
- Agile, DevOps and SRE
- IT, cybersecurity, AI/ML, banking, manufacturing, construction,
  healthcare and government examples
- Edge cases
- Classification exercises
- Interview and examination questions
- Advanced scenario analysis
"""

from dataclasses import dataclass
from typing import List, Dict


# ============================================================
# DISPLAY HELPERS
# ============================================================

WIDTH = 90


def line(char="="):
    print(char * WIDTH)


def title(text):
    print()
    line("=")
    print(text.center(WIDTH))
    line("=")


def section(number, text):
    print()
    line("-")
    print(f"{number}. {text}")
    line("-")


def subsection(text):
    print()
    print(f"\n{text}")
    print("." * len(text))


def paragraph(text):
    print()
    print(text)


def bullet(items):
    for item in items:
        print(f"  - {item}")


def table(headers, rows):
    widths = []

    for i, header in enumerate(headers):
        maximum = len(str(header))
        for row in rows:
            maximum = max(maximum, len(str(row[i])))
        widths.append(min(maximum, 32))

    def format_row(row):
        values = []
        for i, value in enumerate(row):
            value = str(value).replace("\n", " ")
            if len(value) > widths[i]:
                value = value[:widths[i] - 3] + "..."
            values.append(value.ljust(widths[i]))
        return " | ".join(values)

    print()
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))

    for row in rows:
        print(format_row(row))


def question(number, text):
    print()
    print(f"Question {number}: {text}")


def answer(text):
    print(f"Answer: {text}")


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class WorkItem:
    name: str
    purpose: str
    duration: str
    output: str
    repetition: str
    classification: str


@dataclass
class Scenario:
    name: str
    description: str
    classification: str
    reason: str


# ============================================================
# INTRODUCTION
# ============================================================

def introduction():
    title("PROJECT VS OPERATIONS")

    paragraph(
        "Project work and operational work exist in almost every organization. "
        "They can use the same employees, systems, budgets and technologies, "
        "but they are managed differently because their fundamental purposes "
        "are different."
    )

    paragraph(
        "A project is temporary work performed to create a unique product, "
        "service, result or change. Operations are ongoing activities that "
        "keep an organization, product, service or business process functioning."
    )

    paragraph(
        "The distinction becomes important when deciding how work should be "
        "planned, funded, governed, measured and completed. Many real-world "
        "situations contain characteristics of both, so classification must "
        "be based on the nature and purpose of the work rather than on job "
        "titles alone."
    )

    print()
    print("Central distinction:")
    print()
    print("PROJECTS  -> create or change something")
    print("OPERATIONS -> repeatedly run and maintain something")


# ============================================================
# BASIC DEFINITIONS
# ============================================================

def basic_definitions():
    section(1, "Basic Definitions")

    subsection("What is a project?")

    paragraph(
        "A project is a temporary endeavor undertaken to create a unique "
        "product, service, capability or result."
    )

    bullet([
        "It has a defined beginning.",
        "It has a defined end or completion condition.",
        "It has an objective or set of objectives.",
        "It creates a specific result.",
        "It consumes resources.",
        "It involves constraints.",
        "It normally involves some degree of uncertainty.",
        "It is eventually closed, cancelled or transformed into another form of work."
    ])

    subsection("Examples of projects")

    bullet([
        "Building a new hospital.",
        "Developing a banking mobile application.",
        "Migrating a company from one cloud platform to another.",
        "Implementing an ERP system.",
        "Opening a new manufacturing plant.",
        "Launching a new product.",
        "Creating a machine-learning model for a new business capability.",
        "Implementing a cybersecurity monitoring platform.",
        "Constructing a highway.",
        "Conducting a data-center relocation."
    ])

    subsection("What are operations?")

    paragraph(
        "Operations are ongoing and repetitive activities performed to "
        "produce goods, deliver services, maintain systems and keep the "
        "organization functioning."
    )

    bullet([
        "They are generally continuous.",
        "They produce recurring outputs.",
        "They maintain existing capabilities.",
        "They support business-as-usual activity.",
        "They focus strongly on stability, reliability and efficiency.",
        "They may continue indefinitely.",
        "They are normally measured through recurring performance indicators."
    ])

    subsection("Examples of operations")

    bullet([
        "Processing daily banking transactions.",
        "Running payroll every month.",
        "Monitoring production equipment.",
        "Responding to routine customer support requests.",
        "Operating a call center.",
        "Monitoring servers.",
        "Performing daily backups.",
        "Processing insurance claims.",
        "Running a warehouse.",
        "Maintaining a production application."
    ])


# ============================================================
# CORE DIFFERENCE
# ============================================================

def core_difference():
    section(2, "The Core Difference")

    rows = [
        ["Dimension", "Project", "Operations"],
        ["Nature", "Temporary", "Continuous"],
        ["Purpose", "Create/change", "Run/maintain"],
        ["Output", "Usually unique", "Usually repetitive"],
        ["End", "Defined completion", "May continue indefinitely"],
        ["Planning", "Detailed against objectives", "Recurring/capacity based"],
        ["Success", "Objectives and acceptance", "Performance and stability"],
        ["Primary concern", "Change", "Continuity"],
        ["Risk", "Project uncertainty", "Operational exposure"],
        ["Budget", "Often project-specific", "Operating budget"],
        ["Schedule", "Milestone-driven", "Recurring cycles"],
        ["Closure", "Formal closure", "Normally no project closure"],
        ["Change", "Expected", "Controlled to protect stability"],
        ["Metrics", "Schedule, cost, scope, quality", "SLA, KPI, uptime, throughput"]
    ]

    table(rows[0], rows[1:])

    paragraph(
        "The most useful mental model is not that projects are important and "
        "operations are routine. Both can be strategically important. The "
        "difference is that project work introduces or changes capability, "
        "while operational work repeatedly uses and maintains capability."
    )


# ============================================================
# TEMPORARY VS CONTINUOUS
# ============================================================

def temporary_vs_continuous():
    section(3, "Temporary vs Continuous Work")

    subsection("Temporary does not mean short")

    paragraph(
        "A project can last several hours, several months or several years. "
        "Duration alone does not determine whether work is a project."
    )

    bullet([
        "A two-day migration can be a project.",
        "A five-year infrastructure construction effort can be a project.",
        "A daily activity can be operational even if each individual task takes only minutes."
    ])

    subsection("Continuous does not mean unplanned")

    paragraph(
        "Operations can involve extensive planning. The distinction is that "
        "operational planning supports recurring service delivery rather than "
        "creating a temporary unique result."
    )

    table(
        ["Activity", "Classification", "Reason"],
        [
            ["Build a new factory", "Project", "Temporary creation of a facility"],
            ["Run the factory", "Operations", "Continuous production"],
            ["Install a new production line", "Project", "Temporary implementation"],
            ["Operate the production line", "Operations", "Recurring production"],
            ["Upgrade all servers", "Project", "Defined change"],
            ["Monitor servers every day", "Operations", "Continuous service"],
        ]
    )


# ============================================================
# UNIQUE VS REPETITIVE
# ============================================================

def unique_vs_repetitive():
    section(4, "Unique vs Repetitive Work")

    paragraph(
        "A project generally creates something distinguishable. Operations "
        "normally repeat a known process."
    )

    subsection("Unique does not mean completely unprecedented")

    paragraph(
        "An organization can execute similar projects many times. Each project "
        "may still be temporary and have a defined result."
    )

    examples = [
        WorkItem(
            "Build customer portal",
            "Create a digital portal",
            "8 months",
            "New portal",
            "Not recurring",
            "Project"
        ),
        WorkItem(
            "Process customer tickets",
            "Provide support",
            "Continuous",
            "Resolved tickets",
            "Recurring",
            "Operations"
        ),
        WorkItem(
            "Open branch office",
            "Establish new location",
            "6 months",
            "Operational branch",
            "Not recurring",
            "Project"
        ),
        WorkItem(
            "Run branch office",
            "Serve customers",
            "Continuous",
            "Banking services",
            "Recurring",
            "Operations"
        )
    ]

    table(
        ["Work", "Purpose", "Duration", "Output", "Pattern", "Type"],
        [
            [
                e.name,
                e.purpose,
                e.duration,
                e.output,
                e.repetition,
                e.classification
            ]
            for e in examples
        ]
    )


# ============================================================
# PROJECT OBJECTIVES
# ============================================================

def project_objectives():
    section(5, "Project Objectives")

    paragraph(
        "Projects are usually created because an organization wants a change "
        "or a new capability."
    )

    bullet([
        "Increase revenue.",
        "Reduce cost.",
        "Enter a new market.",
        "Improve customer experience.",
        "Meet regulatory requirements.",
        "Replace obsolete technology.",
        "Reduce cybersecurity exposure.",
        "Automate a process.",
        "Build a new physical facility.",
        "Create a new product or service."
    ])

    subsection("Project objective structure")

    table(
        ["Element", "Meaning", "Example"],
        [
            ["Goal", "Desired business outcome", "Reduce processing time"],
            ["Deliverable", "Concrete output", "Automated claims system"],
            ["Acceptance", "Conditions for acceptance", "System passes defined tests"],
            ["Deadline", "Required completion point", "30 June"],
            ["Constraints", "Limits on execution", "Budget and staffing"],
        ]
    )

    paragraph(
        "A deliverable is not automatically the same thing as a business "
        "outcome. A project may deliver a system, while the business outcome "
        "might be faster processing, lower cost or better customer service."
    )


# ============================================================
# OPERATIONAL OBJECTIVES
# ============================================================

def operational_objectives():
    section(6, "Operational Objectives")

    paragraph(
        "Operations focus on keeping an existing service or process functioning "
        "at an acceptable level while improving efficiency and reliability."
    )

    bullet([
        "Maintain availability.",
        "Meet service-level targets.",
        "Maintain quality.",
        "Control operating cost.",
        "Meet throughput requirements.",
        "Resolve incidents.",
        "Maintain compliance.",
        "Reduce recurring failures.",
        "Maintain customer satisfaction.",
        "Use resources efficiently."
    ])

    table(
        ["Operational Metric", "What it measures"],
        [
            ["Availability", "How often a service is usable"],
            ["Throughput", "Amount of work processed"],
            ["Cycle time", "Time required for recurring work"],
            ["Defect rate", "Frequency of defective output"],
            ["SLA compliance", "Performance against service commitments"],
            ["Mean time to repair", "Average recovery time"],
            ["Customer satisfaction", "Customer perception of service"],
            ["Cost per transaction", "Operational efficiency"],
        ]
    )


# ============================================================
# LIFECYCLE
# ============================================================

def lifecycle():
    section(7, "Project Lifecycle vs Operational Lifecycle")

    subsection("Typical project lifecycle")

    stages = [
        "Initiation",
        "Planning",
        "Execution",
        "Monitoring and control",
        "Transition",
        "Closure"
    ]

    for i, stage in enumerate(stages, 1):
        print(f"  {i}. {stage}")

    subsection("Operational lifecycle")

    operational_stages = [
        "Demand or request",
        "Service delivery",
        "Monitoring",
        "Incident/problem handling",
        "Performance management",
        "Continuous improvement",
        "Repeat"
    ]

    for i, stage in enumerate(operational_stages, 1):
        print(f"  {i}. {stage}")

    paragraph(
        "The word lifecycle does not mean that operations necessarily stop. "
        "Operations often form a repeating loop."
    )


# ============================================================
# SCOPE
# ============================================================

def scope_management():
    section(8, "Scope")

    subsection("Project scope")

    paragraph(
        "Project scope defines the work required to produce the agreed "
        "deliverables and the boundaries of that work."
    )

    bullet([
        "What will be delivered?",
        "What will not be delivered?",
        "Which requirements are included?",
        "Which requirements are excluded?",
        "What acceptance criteria apply?"
    ])

    subsection("Operational scope")

    paragraph(
        "Operational scope is usually defined by the service, process or "
        "business function being run."
    )

    examples = [
        ["Project", "Implement a new payroll system", "Temporary"],
        ["Operations", "Run payroll every month", "Continuous"],
        ["Project", "Migrate employee records", "Temporary"],
        ["Operations", "Maintain payroll records", "Continuous"]
    ]

    table(["Work Type", "Activity", "Nature"], examples)


# ============================================================
# SCHEDULE
# ============================================================

def schedule_management():
    section(9, "Scheduling")

    subsection("Project scheduling")

    paragraph(
        "Project schedules normally contain activities, dependencies, "
        "milestones, durations, resource assignments and a target completion date."
    )

    bullet([
        "Gantt charts",
        "Network diagrams",
        "Critical path",
        "Milestones",
        "Dependencies",
        "Baselines",
        "Schedule variance"
    ])

    subsection("Operational scheduling")

    paragraph(
        "Operational scheduling is frequently based on recurring demand, "
        "capacity and service requirements."
    )

    bullet([
        "Shift schedules",
        "Daily work queues",
        "Weekly production plans",
        "Monthly payroll cycles",
        "Support rotations",
        "Maintenance windows",
        "Capacity forecasts"
    ])

    table(
        ["Project", "Operations"],
        [
            ["Has a target completion date", "Often has recurring cycles"],
            ["Tracks milestones", "Tracks throughput"],
            ["Tracks dependencies", "Tracks capacity"],
            ["Schedule variance matters", "SLA and queue performance matter"],
            ["Schedule ends with project", "Schedule repeats"]
        ]
    )


# ============================================================
# COST AND BUDGET
# ============================================================

def cost_and_budget():
    section(10, "Cost and Budget")

    subsection("Project cost")

    bullet([
        "Project labor",
        "Contractors",
        "Equipment",
        "Software licenses",
        "Implementation costs",
        "Consulting",
        "Training",
        "Contingency"
    ])

    subsection("Operational cost")

    bullet([
        "Employee salaries",
        "Cloud infrastructure",
        "Utilities",
        "Routine maintenance",
        "Support contracts",
        "Consumables",
        "Recurring licenses",
        "Facilities",
        "Service providers"
    ])

    paragraph(
        "A project can create an asset that later generates operational costs. "
        "For example, implementing a new application may be a project, while "
        "running the application after deployment becomes operational work."
    )


# ============================================================
# RESOURCES
# ============================================================

def resource_management():
    section(11, "Resource Management")

    paragraph(
        "Projects usually assemble people and resources around a temporary "
        "objective. Operations normally require sustained capacity."
    )

    table(
        ["Resource Question", "Project", "Operations"],
        [
            ["Why is the resource needed?", "Deliver project objectives", "Maintain service"],
            ["Duration", "Temporary assignment", "Ongoing capacity"],
            ["Allocation", "Project workload", "Demand/capacity"],
            ["Main concern", "Delivery", "Availability"],
            ["Staffing change", "Team may dissolve", "Team usually continues"],
        ]
    )

    subsection("Resource conflict")

    paragraph(
        "A common organizational problem occurs when the same employee is "
        "needed for both project and operational work."
    )

    paragraph(
        "For example, a database administrator may need to maintain production "
        "systems while also supporting a database migration project."
    )

    paragraph(
        "This creates a capacity-management problem. Project schedules that "
        "ignore operational commitments often become unrealistic."
    )


# ============================================================
# STAKEHOLDERS
# ============================================================

def stakeholder_management():
    section(12, "Stakeholders")

    paragraph(
        "Both projects and operations have stakeholders, but the stakeholder "
        "structure often changes."
    )

    table(
        ["Stakeholder", "Project Role", "Operational Role"],
        [
            ["Sponsor", "Supports project direction", "May not exist in daily operations"],
            ["Project Manager", "Coordinates temporary delivery", "Not normally responsible for BAU"],
            ["Operations Manager", "May support transition", "Runs ongoing service"],
            ["Customer", "Defines needs/acceptance", "Consumes recurring service"],
            ["Functional Manager", "Provides people/resources", "Manages functional capacity"],
            ["Service Owner", "May define future service", "Owns service performance"],
            ["Team", "Creates deliverables", "Runs and maintains service"],
        ]
    )


# ============================================================
# ROLES
# ============================================================

def roles():
    section(13, "Important Roles")

    subsection("Project Manager")

    bullet([
        "Coordinates project work.",
        "Manages scope, schedule, cost, risk and stakeholders.",
        "Maintains project plans.",
        "Coordinates dependencies.",
        "Reports project status.",
        "Supports issue resolution.",
        "Coordinates closure and transition."
    ])

    subsection("Operations Manager")

    bullet([
        "Manages ongoing service delivery.",
        "Plans operational capacity.",
        "Monitors performance.",
        "Manages operational resources.",
        "Handles recurring issues.",
        "Maintains service levels.",
        "Coordinates operational improvement."
    ])

    subsection("Project Sponsor")

    paragraph(
        "The sponsor provides organizational support, strategic direction, "
        "funding authority and escalation support."
    )

    subsection("Product Owner")

    paragraph(
        "In an Agile environment, a Product Owner focuses on product value, "
        "prioritization and the product backlog. A Product Owner is not simply "
        "another name for an Operations Manager or Project Manager."
    )


# ============================================================
# RISK VS ISSUE
# ============================================================

def risk_and_issue():
    section(14, "Risk vs Issue in Projects and Operations")

    subsection("Project risk")

    paragraph(
        "A risk is an uncertain event or condition that may affect project "
        "objectives if it occurs."
    )

    examples = [
        "A key developer may leave.",
        "A vendor may miss a delivery.",
        "A regulatory requirement may change.",
        "A technology may not perform as expected."
    ]

    bullet(examples)

    subsection("Operational risk")

    paragraph(
        "Operational risk concerns possible failures in ongoing processes, "
        "people, systems or external conditions."
    )

    bullet([
        "Production system outage",
        "Fraud",
        "Data loss",
        "Supplier failure",
        "Human error",
        "Process failure",
        "Security incident"
    ])

    subsection("Issue")

    paragraph(
        "An issue is a problem that has already occurred and requires action."
    )

    table(
        ["Situation", "Classification"],
        [
            ["Vendor may delay equipment", "Risk"],
            ["Vendor has already delayed equipment", "Issue"],
            ["Production server may fail", "Risk"],
            ["Production server has failed", "Operational incident/issue"],
        ]
    )


# ============================================================
# QUALITY
# ============================================================

def quality():
    section(15, "Quality")

    subsection("Project quality")

    bullet([
        "Requirements validation",
        "Design reviews",
        "Testing",
        "Acceptance testing",
        "Defect management",
        "Quality assurance",
        "Deliverable verification"
    ])

    subsection("Operational quality")

    bullet([
        "Service reliability",
        "Defect rates",
        "Customer complaints",
        "Process accuracy",
        "SLA compliance",
        "Production monitoring",
        "Continuous quality improvement"
    ])

    paragraph(
        "A project may successfully deliver a system that still performs "
        "poorly in operations. This is one reason transition and operational "
        "readiness are important."
    )


# ============================================================
# CHANGE MANAGEMENT
# ============================================================

def change_management():
    section(16, "Change Management")

    paragraph(
        "Change is central to projects. Operations generally attempt to "
        "control change so that existing service is not unnecessarily disrupted."
    )

    table(
        ["Situation", "Typical Response"],
        [
            ["Project requirement changes", "Assess impact on scope, cost and schedule"],
            ["Production configuration change", "Follow controlled change process"],
            ["New business capability", "May require project/change initiative"],
            ["Routine process improvement", "May be operational continuous improvement"],
        ]
    )

    subsection("Change is not automatically a project")

    paragraph(
        "A small operational improvement can remain operational work. A large "
        "change that requires coordinated temporary work, significant planning "
        "and a unique deliverable may be managed as a project."
    )


# ============================================================
# GOVERNANCE
# ============================================================

def governance():
    section(17, "Governance")

    paragraph(
        "Governance establishes who makes decisions, who has authority, what "
        "must be reported and how accountability is maintained."
    )

    subsection("Project governance")

    bullet([
        "Project sponsor",
        "Steering committee",
        "Stage gates",
        "Change control",
        "Status reporting",
        "Risk escalation",
        "Budget approvals",
        "Formal acceptance"
    ])

    subsection("Operational governance")

    bullet([
        "Service reviews",
        "Operational KPIs",
        "SLA reviews",
        "Incident escalation",
        "Compliance reviews",
        "Capacity reviews",
        "Vendor performance reviews",
        "Continuous improvement"
    ])


# ============================================================
# METRICS
# ============================================================

def metrics():
    section(18, "Metrics and KPIs")

    table(
        ["Metric", "Project Context", "Operations Context"],
        [
            ["Schedule variance", "Important", "Usually less central"],
            ["Cost variance", "Important", "Operating cost matters"],
            ["Milestone completion", "Important", "Not usually primary"],
            ["Uptime", "May be a requirement", "Core operational metric"],
            ["Throughput", "May be tested", "Core operational metric"],
            ["SLA", "May be designed", "Core service metric"],
            ["Defect rate", "Deliverable quality", "Recurring quality"],
            ["Customer satisfaction", "Acceptance/value", "Continuous service"],
        ]
    )

    paragraph(
        "Metrics should match the purpose of the work. Measuring a project "
        "like a production operation can hide schedule and delivery problems. "
        "Measuring operations only through project-style milestones can hide "
        "service degradation."
    )


# ============================================================
# DEPENDENCIES
# ============================================================

def dependencies():
    section(19, "Dependencies")

    paragraph(
        "Projects often have explicit dependencies between activities. "
        "Operations have dependencies as well, but many are embedded into "
        "standard processes and service architecture."
    )

    examples = [
        "Application deployment depends on infrastructure readiness.",
        "Infrastructure migration depends on network availability.",
        "Payroll depends on employee records.",
        "Banking transactions depend on payment infrastructure.",
        "Customer support depends on the ticketing system."
    ]

    bullet(examples)

    paragraph(
        "When an operational dependency changes substantially, the resulting "
        "work may become a project if it requires a temporary coordinated change."
    )


# ============================================================
# DOCUMENTATION
# ============================================================

def documentation():
    section(20, "Documentation")

    subsection("Typical project documentation")

    bullet([
        "Business case",
        "Project charter",
        "Requirements",
        "Project plan",
        "Schedule",
        "Risk register",
        "Issue log",
        "Change log",
        "Status reports",
        "Acceptance documents",
        "Closure documents"
    ])

    subsection("Typical operational documentation")

    bullet([
        "Standard operating procedures",
        "Runbooks",
        "Service documentation",
        "Knowledge base",
        "Incident records",
        "Problem records",
        "Configuration records",
        "Service-level agreements",
        "Operational dashboards",
        "Maintenance procedures"
    ])


# ============================================================
# PROJECT CLOSURE
# ============================================================

def closure():
    section(21, "Project Closure")

    paragraph(
        "Projects normally have a closure event because the temporary effort "
        "must end."
    )

    bullet([
        "Deliverables are accepted.",
        "Outstanding work is resolved or transferred.",
        "Contracts may be closed.",
        "Resources are released.",
        "Lessons are documented.",
        "Project records are archived.",
        "Operational ownership is confirmed."
    ])

    subsection("Operations do not normally have project-style closure")

    paragraph(
        "An operational service normally continues as long as the organization "
        "needs it. A service may be retired, replaced or transformed, but this "
        "is a change in the service lifecycle rather than a normal daily closure."
    )


# ============================================================
# TRANSITION
# ============================================================

def transition():
    section(22, "Transition from Project to Operations")

    paragraph(
        "One of the most important boundaries between projects and operations "
        "occurs during transition."
    )

    subsection("Example")

    print()
    print("PROJECT")
    print("  Build a customer-support platform")
    print("          |")
    print("          v")
    print("  Test and accept")
    print("          |")
    print("          v")
    print("  Train support team")
    print("          |")
    print("          v")
    print("  Operational handover")
    print("          |")
    print("          v")
    print("OPERATIONS")
    print("  Run and maintain customer-support platform")

    subsection("Operational readiness")

    bullet([
        "Support model defined",
        "Monitoring configured",
        "Access controls established",
        "Backup procedures established",
        "Incident procedures documented",
        "Knowledge transferred",
        "Support staff trained",
        "Security controls validated",
        "Performance tested",
        "Ownership established"
    ])


# ============================================================
# PROJECT, PROGRAM, PORTFOLIO, OPERATIONS
# ============================================================

def project_program_portfolio_operations():
    section(23, "Project vs Program vs Portfolio vs Operations")

    table(
        ["Concept", "Meaning", "Primary Focus"],
        [
            [
                "Project",
                "Temporary effort creating a unique result",
                "Specific change"
            ],
            [
                "Program",
                "Related projects and other work managed together",
                "Strategic benefits"
            ],
            [
                "Portfolio",
                "Collection of investments and initiatives",
                "Strategic alignment and value"
            ],
            [
                "Operations",
                "Ongoing work delivering existing services",
                "Continuity and performance"
            ],
        ]
    )

    paragraph(
        "A company may run operations while executing multiple projects. "
        "Projects can exist inside programs, and programs can exist within "
        "portfolios."
    )

    print()
    print("PORTFOLIO")
    print("   |")
    print("   +-- Program")
    print("   |      +-- Project A")
    print("   |      +-- Project B")
    print("   |")
    print("   +-- Project C")
    print("   |")
    print("   +-- Operational investment")


# ============================================================
# IT EXAMPLES
# ============================================================

def it_examples():
    section(24, "IT Examples")

    scenarios = [
        Scenario(
            "Develop new banking application",
            "A team designs, builds, tests and launches a new application.",
            "Project",
            "Temporary work creates a new capability."
        ),
        Scenario(
            "Monitor banking application",
            "Engineers monitor availability and performance every day.",
            "Operations",
            "The service is continuously maintained."
        ),
        Scenario(
            "Migrate database",
            "A team moves data from an old database to a new platform.",
            "Project",
            "The migration has a defined start and completion."
        ),
        Scenario(
            "Perform daily database backup",
            "Backups run according to a recurring operational schedule.",
            "Operations",
            "The activity repeats continuously."
        ),
        Scenario(
            "Implement zero-trust architecture",
            "A coordinated initiative changes security architecture.",
            "Project",
            "It introduces a significant temporary change."
        ),
        Scenario(
            "Monitor security alerts",
            "Security analysts continuously monitor alerts.",
            "Operations",
            "Monitoring is continuous service activity."
        )
    ]

    table(
        ["Scenario", "Description", "Type", "Reason"],
        [
            [s.name, s.description, s.classification, s.reason]
            for s in scenarios
        ]
    )


# ============================================================
# CYBERSECURITY EXAMPLES
# ============================================================

def cybersecurity_examples():
    section(25, "Cybersecurity Examples")

    table(
        ["Activity", "Classification", "Reason"],
        [
            [
                "Deploy a new SIEM",
                "Project",
                "Implementation is a temporary change"
            ],
            [
                "Monitor SIEM alerts",
                "Operations",
                "Continuous monitoring"
            ],
            [
                "Conduct one-time enterprise security transformation",
                "Project",
                "Defined transformation initiative"
            ],
            [
                "Perform daily threat monitoring",
                "Operations",
                "Recurring security service"
            ],
            [
                "Migrate identity platform",
                "Project",
                "Temporary migration effort"
            ],
            [
                "Manage user access requests",
                "Operations",
                "Recurring business process"
            ],
            [
                "Build incident-response capability",
                "Project",
                "Capability creation"
            ],
            [
                "Respond to security incidents",
                "Operations",
                "Ongoing service activity"
            ]
        ]
    )


# ============================================================
# AI AND DATA EXAMPLES
# ============================================================

def ai_data_examples():
    section(26, "AI, ML and Data Examples")

    table(
        ["Activity", "Classification", "Reason"],
        [
            [
                "Build a new fraud-detection model",
                "Project",
                "Temporary model-development effort"
            ],
            [
                "Monitor model drift",
                "Operations",
                "Continuous production monitoring"
            ],
            [
                "Create a data warehouse",
                "Project",
                "New capability implementation"
            ],
            [
                "Run daily ETL pipelines",
                "Operations",
                "Recurring data processing"
            ],
            [
                "Migrate ML platform",
                "Project",
                "Temporary migration"
            ],
            [
                "Maintain ML production pipelines",
                "Operations",
                "Ongoing service maintenance"
            ],
            [
                "Develop a new annotation platform",
                "Project",
                "New product/capability creation"
            ],
            [
                "Process daily annotation workload",
                "Operations",
                "Recurring delivery activity"
            ]
        ]
    )


# ============================================================
# CONSTRUCTION
# ============================================================

def construction_examples():
    section(27, "Construction Examples")

    table(
        ["Activity", "Type", "Explanation"],
        [
            ["Design office building", "Project", "Temporary design effort"],
            ["Construct office building", "Project", "Temporary construction"],
            ["Operate office building", "Operations", "Continuous facility use"],
            ["Clean office daily", "Operations", "Recurring activity"],
            ["Install new elevator", "Project", "Defined implementation"],
            ["Maintain elevators", "Operations", "Recurring maintenance"],
        ]
    )


# ============================================================
# BANKING
# ============================================================

def banking_examples():
    section(28, "Banking Examples")

    table(
        ["Activity", "Type", "Reason"],
        [
            ["Launch new credit-card product", "Project", "New product launch"],
            ["Process card transactions", "Operations", "Continuous transaction processing"],
            ["Implement KYC platform", "Project", "New capability"],
            ["Perform KYC checks", "Operations", "Recurring process"],
            ["Open new branch", "Project", "Temporary setup"],
            ["Run branch", "Operations", "Continuous business activity"],
            ["Migrate core banking platform", "Project", "Major transformation"],
            ["Process daily banking transactions", "Operations", "Business-as-usual"],
        ]
    )


# ============================================================
# MANUFACTURING
# ============================================================

def manufacturing_examples():
    section(29, "Manufacturing Examples")

    table(
        ["Activity", "Type", "Reason"],
        [
            ["Build new factory", "Project", "Temporary facility creation"],
            ["Produce goods", "Operations", "Recurring production"],
            ["Install new machinery", "Project", "Implementation"],
            ["Run machinery", "Operations", "Continuous production"],
            ["Automate production line", "Project", "Transformation"],
            ["Perform routine maintenance", "Operations", "Recurring maintenance"],
        ]
    )


# ============================================================
# HEALTHCARE
# ============================================================

def healthcare_examples():
    section(30, "Healthcare Examples")

    table(
        ["Activity", "Type", "Reason"],
        [
            ["Build a new hospital wing", "Project", "Temporary construction"],
            ["Run hospital services", "Operations", "Continuous healthcare delivery"],
            ["Implement electronic health record system", "Project", "New system implementation"],
            ["Register patients", "Operations", "Recurring process"],
            ["Renovate operating theatre", "Project", "Temporary improvement"],
            ["Sterilize equipment routinely", "Operations", "Recurring activity"],
        ]
    )


# ============================================================
# GOVERNMENT
# ============================================================

def government_examples():
    section(31, "Government Examples")

    table(
        ["Activity", "Type", "Reason"],
        [
            ["Build public highway", "Project", "Temporary infrastructure creation"],
            ["Maintain highway", "Operations", "Ongoing service"],
            ["Develop citizen-service portal", "Project", "New capability"],
            ["Process citizen applications", "Operations", "Recurring service"],
            ["Implement new tax system", "Project", "Transformation"],
            ["Process tax returns", "Operations", "Continuous administrative process"],
        ]
    )


# ============================================================
# AGILE
# ============================================================

def agile():
    section(32, "Agile and the Project vs Operations Boundary")

    paragraph(
        "Agile methods can make the distinction less obvious because teams "
        "work continuously through iterations and releases."
    )

    subsection("Agile product development")

    paragraph(
        "A product team may not behave like a traditional project team with "
        "a fixed start and finish. The product can continue evolving."
    )

    paragraph(
        "This does not mean that every activity becomes operations. Individual "
        "initiatives, releases or major changes may still be treated as "
        "temporary work even when the broader product lifecycle is continuous."
    )

    table(
        ["Activity", "Likely Classification"],
        [
            ["Build a new product capability", "Project/change initiative"],
            ["Prioritize product backlog", "Product management"],
            ["Release a feature", "Change/release activity"],
            ["Monitor production service", "Operations"],
            ["Fix production incident", "Operations"],
            ["Major platform migration", "Project/change initiative"],
        ]
    )


# ============================================================
# DEVOPS
# ============================================================

def devops():
    section(33, "DevOps and the Blurred Boundary")

    paragraph(
        "DevOps connects development and operations. The goal is not to "
        "eliminate the distinction between change and operation but to improve "
        "the flow from development into reliable service delivery."
    )

    print()
    print("Traditional separation:")
    print("Development -> Handover -> Operations")

    print()
    print("DevOps-oriented flow:")
    print("Plan -> Build -> Test -> Deploy -> Operate -> Monitor -> Improve")

    paragraph(
        "A DevOps team may own both delivery and operational responsibilities. "
        "The team structure can be combined even though the nature of individual "
        "activities remains different."
    )


# ============================================================
# SRE
# ============================================================

def sre():
    section(34, "Site Reliability Engineering")

    paragraph(
        "SRE focuses heavily on reliability of production services."
    )

    bullet([
        "Availability",
        "Latency",
        "Error rates",
        "Capacity",
        "Incident response",
        "Automation",
        "Reliability engineering",
        "Service-level objectives"
    ])

    paragraph(
        "Building a new reliability platform may be project work. Running "
        "production monitoring and responding to incidents are operational "
        "activities. Automating recurring operational work can also be a "
        "project or engineering initiative when substantial temporary work "
        "is required to create the automation."
    )


# ============================================================
# CONTINUOUS IMPROVEMENT
# ============================================================

def continuous_improvement():
    section(35, "Continuous Improvement")

    paragraph(
        "Continuous improvement is often operational because it occurs as "
        "part of ongoing service management."
    )

    paragraph(
        "A larger improvement initiative can be managed as a project when "
        "it requires a defined temporary effort and produces a significant "
        "new capability."
    )

    table(
        ["Situation", "Likely Treatment"],
        [
            ["Reduce a recurring process step", "Operational improvement"],
            ["Automate a small manual task", "Operational improvement"],
            ["Replace an enterprise-wide platform", "Project"],
            ["Redesign an entire supply chain", "Project/program"],
            ["Tune daily production parameters", "Operations"],
        ]
    )


# ============================================================
# SERVICE MANAGEMENT
# ============================================================

def service_management():
    section(36, "Service Management")

    paragraph(
        "Service management is strongly connected with operations because "
        "services need to remain available, reliable and useful after "
        "implementation."
    )

    table(
        ["Concept", "Meaning"],
        [
            ["Incident", "Restore normal service after disruption"],
            ["Problem", "Identify and address underlying cause"],
            ["Change", "Modify a service or environment in a controlled way"],
            ["Service request", "Standard user/customer request"],
            ["SLA", "Agreed service performance level"],
            ["Runbook", "Documented operational procedure"],
            ["Service owner", "Person accountable for service performance"],
        ]
    )


# ============================================================
# PROJECT AND OPERATION INTERACTION
# ============================================================

def interaction():
    section(37, "How Projects and Operations Interact")

    paragraph(
        "Projects and operations are not isolated worlds. They constantly "
        "interact."
    )

    print()
    print("BUSINESS NEED")
    print("     |")
    print("     v")
    print("PROJECT / CHANGE")
    print("     |")
    print("     v")
    print("NEW CAPABILITY")
    print("     |")
    print("     v")
    print("OPERATIONS")
    print("     |")
    print("     v")
    print("FEEDBACK / IMPROVEMENT")
    print("     |")
    print("     v")
    print("NEW PROJECT / CHANGE")

    paragraph(
        "This creates a cycle in which operations identify business problems "
        "and projects introduce changes that improve or transform operations."
    )


# ============================================================
# WHEN OPERATIONS BECOME A PROJECT
# ============================================================

def operations_become_project():
    section(38, "When Operational Work Becomes a Project")

    paragraph(
        "An activity that normally belongs to operations can become a project "
        "when its purpose changes from repeating existing work to creating or "
        "implementing a significant new capability."
    )

    examples = [
        "Routine server maintenance -> operations.",
        "Replacing the entire server fleet -> project.",
        "Daily security monitoring -> operations.",
        "Implementing a new enterprise SIEM -> project.",
        "Routine employee onboarding -> operations.",
        "Implementing a new global onboarding platform -> project.",
        "Daily warehouse operations -> operations.",
        "Opening a new distribution center -> project."
    ]

    bullet(examples)


# ============================================================
# WHEN PROJECT WORK CONTAINS OPERATIONS
# ============================================================

def project_contains_operations():
    section(39, "When Projects Contain Operational Activities")

    paragraph(
        "A project may contain repetitive activities without becoming an "
        "operational function."
    )

    paragraph(
        "For example, a project team may conduct weekly testing, daily standups "
        "and recurring status meetings. These activities repeat, but their "
        "purpose is to deliver the temporary project."
    )

    paragraph(
        "Classification should therefore consider the purpose and context "
        "of the activity rather than whether one task is repeated."
    )


# ============================================================
# COMMON MISCONCEPTIONS
# ============================================================

def misconceptions():
    section(40, "Common Misconceptions")

    misconceptions_list = [
        (
            "Projects are always short.",
            "False. Projects can last years."
        ),
        (
            "Operations are unimportant.",
            "False. Operations often represent the core business."
        ),
        (
            "Anything involving technology is a project.",
            "False. Running technology systems is often operations."
        ),
        (
            "A project must be innovative.",
            "False. It can use existing technologies to create a unique result."
        ),
        (
            "Operations never change.",
            "False. Operations continuously improve and respond to change."
        ),
        (
            "Every change is a project.",
            "False. Small controlled changes can remain operational."
        ),
        (
            "Agile eliminates projects.",
            "False. Agile changes the way many initiatives are managed."
        ),
        (
            "A project manager runs operations.",
            "Usually false. Project managers focus on temporary delivery."
        ),
        (
            "Operations have no deadlines.",
            "False. Operations have recurring deadlines and SLAs."
        ),
        (
            "Project closure means the product stops working.",
            "False. The project can close while the resulting product enters operations."
        ),
    ]

    table(
        ["Statement", "Correction"],
        misconceptions_list
    )


# ============================================================
# EDGE CASES
# ============================================================

def edge_cases():
    section(41, "Advanced Edge Cases")

    cases = [
        (
            "Annual audit",
            "Can be operational if it is part of a recurring compliance process."
        ),
        (
            "Annual system upgrade",
            "May be treated as a project if each upgrade is a defined temporary initiative."
        ),
        (
            "Software release",
            "May be a release/change activity rather than a full project."
        ),
        (
            "Continuous product development",
            "Can use an ongoing product model rather than traditional projects."
        ),
        (
            "Incident response",
            "Normally operational, even though the incident itself may be unusual."
        ),
        (
            "Major disaster recovery rebuild",
            "May become a project because substantial temporary reconstruction is required."
        ),
        (
            "Research",
            "Can be project work if temporary and aimed at a defined result."
        ),
        (
            "Routine research laboratory operation",
            "Can be operations if continuously performed."
        ),
        (
            "Customer implementation",
            "Often project work when each customer requires a defined implementation."
        ),
        (
            "Managed customer support",
            "Usually operations because service continues."
        ),
    ]

    table(["Edge Case", "Interpretation"], cases)


# ============================================================
# DECISION FRAMEWORK
# ============================================================

def decision_framework():
    section(42, "Practical Classification Framework")

    paragraph(
        "Use the following questions when deciding whether work is a project "
        "or operations."
    )

    questions = [
        "Does the work have a defined beginning?",
        "Does the work have a defined end?",
        "Is it intended to create or change something?",
        "Is the result distinguishable from normal recurring output?",
        "Does the work require temporary coordination?",
        "Is there a defined acceptance condition?",
        "Will the team or work structure change after completion?",
        "Is the activity repeated indefinitely?",
        "Is the main purpose to maintain an existing service?",
        "Are performance levels measured continuously?"
    ]

    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")

    paragraph(
        "The first group of questions points toward project work. The second "
        "group points toward operations. A mixed result indicates that the "
        "work may involve both."
    )


# ============================================================
# CLASSIFICATION ALGORITHM
# ============================================================

def classify_work(
    temporary=False,
    unique_result=False,
    creates_change=False,
    recurring=False,
    maintains_service=False
):
    project_score = 0
    operation_score = 0

    if temporary:
        project_score += 2

    if unique_result:
        project_score += 2

    if creates_change:
        project_score += 2

    if recurring:
        operation_score += 2

    if maintains_service:
        operation_score += 2

    if project_score > operation_score:
        return "PROJECT"

    if operation_score > project_score:
        return "OPERATIONS"

    return "MIXED / REQUIRES CONTEXT"


def classification_examples():
    section(43, "Classification Examples Using a Simple Decision Model")

    examples = [
        {
            "name": "Build a new mobile application",
            "temporary": True,
            "unique_result": True,
            "creates_change": True,
            "recurring": False,
            "maintains_service": False
        },
        {
            "name": "Monitor production servers",
            "temporary": False,
            "unique_result": False,
            "creates_change": False,
            "recurring": True,
            "maintains_service": True
        },
        {
            "name": "Replace enterprise network",
            "temporary": True,
            "unique_result": True,
            "creates_change": True,
            "recurring": False,
            "maintains_service": False
        },
        {
            "name": "Process daily customer requests",
            "temporary": False,
            "unique_result": False,
            "creates_change": False,
            "recurring": True,
            "maintains_service": True
        },
    ]

    for item in examples:
        result = classify_work(
            temporary=item["temporary"],
            unique_result=item["unique_result"],
            creates_change=item["creates_change"],
            recurring=item["recurring"],
            maintains_service=item["maintains_service"]
        )

        print()
        print(f"Work: {item['name']}")
        print(f"Classification: {result}")


# ============================================================
# PROJECT VS OPERATIONS IN MANAGEMENT
# ============================================================

def management_difference():
    section(44, "Management Difference")

    table(
        ["Management Area", "Project Manager", "Operations Manager"],
        [
            [
                "Primary objective",
                "Deliver temporary objectives",
                "Maintain ongoing service"
            ],
            [
                "Time horizon",
                "Temporary",
                "Continuous"
            ],
            [
                "Scope",
                "Defined project scope",
                "Service/process scope"
            ],
            [
                "Resources",
                "Temporary allocation",
                "Sustained capacity"
            ],
            [
                "Risk",
                "Project uncertainty",
                "Operational exposure"
            ],
            [
                "Performance",
                "Delivery objectives",
                "Service KPIs"
            ],
            [
                "Change",
                "Expected",
                "Controlled"
            ],
            [
                "Closure",
                "Formal",
                "Not normally applicable"
            ]
        ]
    )


# ============================================================
# PROJECT SUCCESS
# ============================================================

def project_success():
    section(45, "Project Success")

    paragraph(
        "Project success can be evaluated at several levels."
    )

    bullet([
        "Was the agreed deliverable produced?",
        "Was the scope acceptable?",
        "Was the schedule acceptable?",
        "Was the budget acceptable?",
        "Did the deliverable meet quality requirements?",
        "Were stakeholders satisfied?",
        "Did the project create the intended business value?"
    ])

    paragraph(
        "A project can meet its delivery targets and still fail to create "
        "expected business value. This is why delivery performance and business "
        "outcomes should be considered separately."
    )


# ============================================================
# OPERATIONAL SUCCESS
# ============================================================

def operational_success():
    section(46, "Operational Success")

    paragraph(
        "Operational success is usually measured by the sustained performance "
        "of a service or process."
    )

    bullet([
        "Availability",
        "Reliability",
        "Throughput",
        "Quality",
        "Cost efficiency",
        "Customer satisfaction",
        "SLA performance",
        "Compliance",
        "Incident frequency",
        "Recovery performance"
    ])

    paragraph(
        "An operational team is successful when the service continues to "
        "perform predictably and efficiently under expected demand."
    )


# ============================================================
# PROJECT FAILURE MODES
# ============================================================

def project_failure_modes():
    section(47, "Project Failure Modes")

    bullet([
        "Unclear objectives",
        "Uncontrolled scope expansion",
        "Poor estimation",
        "Insufficient resources",
        "Weak stakeholder alignment",
        "Poor risk management",
        "Unmanaged dependencies",
        "Weak governance",
        "Poor quality control",
        "Inadequate testing",
        "Weak transition planning",
        "Lack of operational readiness"
    ])


# ============================================================
# OPERATIONAL FAILURE MODES
# ============================================================

def operational_failure_modes():
    section(48, "Operational Failure Modes")

    bullet([
        "Insufficient capacity",
        "Poor process design",
        "Frequent incidents",
        "Weak monitoring",
        "Poor documentation",
        "High employee dependency",
        "Poor change control",
        "Weak vendor management",
        "Low automation",
        "Security weaknesses",
        "High defect rates",
        "Inadequate disaster recovery"
    ])


# ============================================================
# TRANSITION FAILURE
# ============================================================

def transition_failure():
    section(49, "Why Projects Fail at the Operations Boundary")

    paragraph(
        "A technically successful project can create operational problems "
        "if the receiving organization cannot run the resulting solution."
    )

    examples = [
        "No support team was trained.",
        "Monitoring was not configured.",
        "No runbook exists.",
        "Production capacity was underestimated.",
        "Access permissions were not prepared.",
        "Backup procedures were not tested.",
        "Security controls were incomplete.",
        "Operational ownership was unclear.",
        "Support costs were not considered.",
        "Service-level commitments were undefined."
    ]

    bullet(examples)


# ============================================================
# HYBRID WORK
# ============================================================

def hybrid_work():
    section(50, "Hybrid Project and Operations Work")

    paragraph(
        "Many real organizations operate in a hybrid environment. A team may "
        "run a service while simultaneously delivering changes to that service."
    )

    table(
        ["Activity", "Nature"],
        [
            ["Daily production support", "Operations"],
            ["Emergency incident response", "Operations"],
            ["Major system replacement", "Project"],
            ["Routine patching", "Operations"],
            ["Enterprise platform migration", "Project"],
            ["Monitoring", "Operations"],
            ["Creating new monitoring platform", "Project"],
            ["Improving existing monitoring rule", "Operations or small change"],
        ]
    )

    paragraph(
        "The classification depends on the scale, purpose, temporary nature "
        "and governance requirements of the work."
    )


# ============================================================
# CASE STUDY 1
# ============================================================

def case_study_one():
    section(51, "Case Study: Banking Application")

    paragraph(
        "A bank decides to replace its legacy mobile banking application. "
        "The organization creates a temporary team consisting of product "
        "managers, developers, testers, security specialists, architects and "
        "operations representatives."
    )

    paragraph(
        "The team spends twelve months designing, developing, testing and "
        "deploying the replacement application."
    )

    print()
    print("Classification:")
    print("  Replacement application initiative -> PROJECT")

    paragraph(
        "After launch, production engineers monitor uptime, respond to incidents, "
        "apply routine patches, manage capacity and support customers."
    )

    print()
    print("Classification:")
    print("  Running the application -> OPERATIONS")

    paragraph(
        "If the bank later decides to replace the underlying mobile platform "
        "with a completely different architecture, that major transformation "
        "may again be managed as project work."
    )


# ============================================================
# CASE STUDY 2
# ============================================================

def case_study_two():
    section(52, "Case Study: Cybersecurity Transformation")

    paragraph(
        "An organization wants to implement enterprise-wide zero-trust security."
    )

    bullet([
        "Current-state assessment",
        "Target architecture",
        "Identity redesign",
        "Network segmentation",
        "Policy development",
        "Technology implementation",
        "Testing",
        "Training",
        "Rollout"
    ])

    paragraph(
        "This is project or program work because the organization is moving "
        "from an existing state to a new security capability."
    )

    paragraph(
        "After implementation, security teams continuously monitor alerts, "
        "review access, investigate incidents and maintain security controls."
    )

    print()
    print("Transformation -> PROJECT / PROGRAM")
    print("Security monitoring -> OPERATIONS")


# ============================================================
# CASE STUDY 3
# ============================================================

def case_study_three():
    section(53, "Case Study: AI Production System")

    paragraph(
        "A company develops a machine-learning model to detect fraudulent "
        "transactions."
    )

    print()
    print("Model development")
    print("  Data preparation")
    print("  Feature engineering")
    print("  Model development")
    print("  Evaluation")
    print("  Security testing")
    print("  Deployment")
    print("  Acceptance")
    print("  -> PROJECT")

    print()
    print("Production")
    print("  Monitor accuracy")
    print("  Monitor drift")
    print("  Monitor infrastructure")
    print("  Process predictions")
    print("  Handle incidents")
    print("  Retrain when required")
    print("  -> OPERATIONS")

    paragraph(
        "The exact governance model may differ, but the underlying distinction "
        "remains between creating/changing capability and continuously running it."
    )


# ============================================================
# CASE STUDY 4
# ============================================================

def case_study_four():
    section(54, "Case Study: Manufacturing Plant")

    paragraph(
        "A company decides to construct a new manufacturing facility."
    )

    print()
    print("Land acquisition")
    print("Design")
    print("Construction")
    print("Equipment installation")
    print("Testing")
    print("Commissioning")
    print("-> PROJECT")

    print()
    print("Production")
    print("Quality checks")
    print("Equipment monitoring")
    print("Inventory management")
    print("Maintenance")
    print("Shipping")
    print("-> OPERATIONS")


# ============================================================
# CASE STUDY 5
# ============================================================

def case_study_five():
    section(55, "Case Study: ERP Implementation")

    paragraph(
        "A company implements a new ERP system across finance, procurement, "
        "human resources and supply chain."
    )

    bullet([
        "Requirements",
        "Vendor selection",
        "Configuration",
        "Integration",
        "Data migration",
        "Testing",
        "Training",
        "Go-live"
    ])

    print()
    print("ERP implementation -> PROJECT")

    paragraph(
        "After go-live, employees use the ERP system every day, administrators "
        "maintain it, support teams handle incidents and finance processes "
        "continue through the system."
    )

    print()
    print("ERP usage and support -> OPERATIONS")


# ============================================================
# INTERVIEW QUESTIONS
# ============================================================

def interview_questions():
    section(56, "Interview Questions")

    qa = [
        (
            "What is the main difference between a project and operations?",
            "A project is temporary and creates a unique result or change; operations are ongoing and maintain recurring services or processes."
        ),
        (
            "Can operations involve change?",
            "Yes. Operational teams continuously improve processes and services. Significant temporary changes may be managed as projects."
        ),
        (
            "Can a project contain repetitive work?",
            "Yes. Repetition inside a project does not make the entire project operational."
        ),
        (
            "Can a project last several years?",
            "Yes. Temporary refers to the defined nature of the work, not a specific maximum duration."
        ),
        (
            "What happens after a project ends?",
            "The deliverable may be transferred to operations, handed to a customer, retired or otherwise transitioned according to the project objective."
        ),
        (
            "Why is transition important?",
            "Because the organization must be able to operate and support the result after the temporary project team leaves."
        ),
        (
            "What is the difference between a project manager and operations manager?",
            "A project manager coordinates temporary delivery, while an operations manager focuses on ongoing service or process performance."
        ),
        (
            "Is incident management a project?",
            "Usually no. Incident management is generally operational work focused on restoring service."
        ),
        (
            "Is implementing a new incident-management platform a project?",
            "Usually yes, because it is a temporary implementation that creates a new capability."
        ),
        (
            "Does Agile eliminate the distinction?",
            "No. Agile changes how development and delivery can be organized, but the distinction between creating change and operating a service still exists."
        ),
    ]

    for q, a in qa:
        question("", q)
        answer(a)


# ============================================================
# EXAM QUESTIONS
# ============================================================

def exam_questions():
    section(57, "Classification Exercises")

    exercises = [
        "Launching a new e-commerce website.",
        "Processing online orders every day.",
        "Migrating a company database.",
        "Monitoring the database after migration.",
        "Building a new warehouse.",
        "Operating the warehouse.",
        "Implementing a new HR platform.",
        "Running monthly payroll.",
        "Responding to customer incidents.",
        "Creating a new customer support platform.",
        "Monitoring production servers.",
        "Replacing the entire enterprise network.",
        "Performing routine network monitoring.",
        "Training employees as part of a temporary ERP implementation.",
        "Running the ERP system after implementation."
    ]

    answers = [
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project activity",
        "Operations"
    ]

    for i, exercise in enumerate(exercises, 1):
        print(f"{i}. {exercise}")

    print()
    print("Answer key:")
    for i, classification in enumerate(answers, 1):
        print(f"{i}. {classification}")


# ============================================================
# ADVANCED SCENARIOS
# ============================================================

def advanced_scenarios():
    section(58, "Advanced Scenario Analysis")

    scenarios = [
        (
            "A company performs the same software upgrade every quarter.",
            "The recurring upgrade process may be operational, while a major redesign or platform replacement may be project work."
        ),
        (
            "A security team responds to a one-time major breach.",
            "Incident response remains operational in nature even though the incident is unusual. A separate long-term security transformation resulting from the incident may be a project."
        ),
        (
            "A company builds automation for a manual operational process.",
            "The existing process is operations. Creating a substantial automation capability can be project work."
        ),
        (
            "A team continuously develops a software product.",
            "The broader product lifecycle can be continuous. Individual initiatives, releases and major changes may still have temporary characteristics."
        ),
        (
            "A data team processes millions of records every day.",
            "Recurring data processing is operations."
        ),
        (
            "The same data team builds a new enterprise data platform.",
            "Creating the new platform is project work."
        ),
        (
            "A company hires consultants for six months to improve operations.",
            "The consulting engagement can be a project if it has defined temporary objectives and deliverables, even though its goal is operational improvement."
        ),
    ]

    for scenario, explanation in scenarios:
        print()
        print(f"Scenario: {scenario}")
        print(f"Analysis: {explanation}")


# ============================================================
# ADVANCED COMPARISON
# ============================================================

def advanced_comparison():
    section(59, "Advanced Project vs Operations Comparison")

    dimensions = [
        ("Existence", "Temporary effort", "Persistent business function"),
        ("Primary purpose", "Create/change", "Run/maintain"),
        ("Output", "Unique deliverable/result", "Recurring service/output"),
        ("Time orientation", "End-oriented", "Continuous"),
        ("Planning", "Activities and dependencies", "Demand and capacity"),
        ("Funding", "Project investment", "Operating expenditure"),
        ("Team", "May be temporary", "Usually sustained"),
        ("Scope", "Defined boundaries", "Service/process boundaries"),
        ("Risk", "Uncertainty around delivery", "Exposure during service"),
        ("Change", "Expected", "Controlled"),
        ("Quality", "Acceptance and deliverable quality", "Service/process quality"),
        ("Performance", "Milestones and objectives", "KPIs and SLAs"),
        ("Governance", "Project governance", "Operational governance"),
        ("Closure", "Formal closure", "Service retirement or continuation"),
        ("Knowledge", "Project documentation", "Operational knowledge"),
        ("Customer relationship", "Requirements and acceptance", "Ongoing service"),
        ("Resource model", "Temporary allocation", "Capacity planning"),
        ("Dependencies", "Often mapped explicitly", "Often embedded in processes"),
        ("Main failure", "Failure to deliver change", "Failure to maintain service"),
        ("Transition", "Central activity", "Receives and maintains capability"),
    ]

    table(
        ["Dimension", "Project", "Operations"],
        dimensions
    )


# ============================================================
# DECISION TREE
# ============================================================

def decision_tree():
    section(60, "Decision Tree")

    print()
    print("START")
    print("  |")
    print("  v")
    print("Is the work intended to create or significantly change something?")
    print("  |")
    print("  +-- NO --> Is it recurring and ongoing?")
    print("  |             |")
    print("  |             +-- YES --> OPERATIONS")
    print("  |             |")
    print("  |             +-- NO --> Examine context")
    print("  |")
    print("  +-- YES --> Does it have temporary boundaries?")
    print("                |")
    print("                +-- YES --> PROJECT / CHANGE INITIATIVE")
    print("                |")
    print("                +-- NO --> Continuous product/change model may apply")

    paragraph(
        "This decision tree is a reasoning aid, not a rigid organizational rule. "
        "Different organizations can use different governance models for similar work."
    )


# ============================================================
# GLOSSARY
# ============================================================

def glossary():
    section(61, "Glossary")

    terms = {
        "Project": "Temporary work performed to create a unique product, service, result or change.",
        "Operations": "Ongoing work that produces recurring outputs or maintains a service.",
        "Deliverable": "A measurable output produced by project or other planned work.",
        "Outcome": "The result or effect produced by using a deliverable.",
        "Business value": "The benefit an organization receives from an investment or capability.",
        "Scope": "The boundaries of the work and what is included or excluded.",
        "Milestone": "A significant point or event in a project.",
        "Baseline": "An approved reference used to compare actual performance.",
        "Risk": "An uncertain event or condition that may affect objectives.",
        "Issue": "A problem that has already occurred.",
        "Incident": "An event that disrupts or may disrupt normal service.",
        "SLA": "Service Level Agreement defining agreed service performance.",
        "KPI": "Key Performance Indicator used to measure performance.",
        "Capacity": "The ability of resources or systems to handle demand.",
        "Transition": "Movement of a new capability from project delivery into operational ownership.",
        "Change": "A modification to an existing product, service, process or environment.",
        "Program": "A coordinated group of related projects and other work managed to achieve benefits.",
        "Portfolio": "A collection of investments, programs, projects and operational work aligned with strategy.",
        "Runbook": "Documented instructions for recurring operational tasks.",
        "Business-as-usual": "Normal ongoing operational activity."
    }

    for term, definition in terms.items():
        print(f"\n{term}:")
        print(f"  {definition}")


# ============================================================
# FINAL CASE CLASSIFICATION
# ============================================================

def final_case_classification():
    section(62, "Final Classification Set")

    cases = [
        "Designing a new airport",
        "Operating airport security every day",
        "Implementing a new baggage-handling system",
        "Monitoring baggage systems",
        "Opening a new retail store",
        "Running the retail store",
        "Creating a new mobile application",
        "Answering customer support calls",
        "Migrating a cloud environment",
        "Monitoring cloud infrastructure",
        "Building a new AI model",
        "Monitoring the deployed AI model",
        "Implementing a new cybersecurity platform",
        "Monitoring cybersecurity alerts",
        "Constructing a new manufacturing plant",
        "Running production",
        "Implementing an ERP system",
        "Processing invoices every day",
        "Building a new data warehouse",
        "Running scheduled data pipelines"
    ]

    classifications = [
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations",
        "Project",
        "Operations"
    ]

    table(
        ["Case", "Classification"],
        [
            [f"{i}. {case}", classifications[i - 1]]
            for i, case in enumerate(cases, 1)
        ]
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    introduction()

    basic_definitions()
    core_difference()
    temporary_vs_continuous()
    unique_vs_repetitive()
    project_objectives()
    operational_objectives()
    lifecycle()
    scope_management()
    schedule_management()
    cost_and_budget()
    resource_management()
    stakeholder_management()
    roles()
    risk_and_issue()
    quality()
    change_management()
    governance()
    metrics()
    dependencies()
    documentation()
    closure()
    transition()

    project_program_portfolio_operations()

    it_examples()
    cybersecurity_examples()
    ai_data_examples()
    construction_examples()
    banking_examples()
    manufacturing_examples()
    healthcare_examples()
    government_examples()

    agile()
    devops()
    sre()
    continuous_improvement()
    service_management()
    interaction()

    operations_become_project()
    project_contains_operations()
    misconceptions()
    edge_cases()

    decision_framework()
    classification_examples()
    management_difference()

    project_success()
    operational_success()

    project_failure_modes()
    operational_failure_modes()
    transition_failure()

    hybrid_work()

    case_study_one()
    case_study_two()
    case_study_three()
    case_study_four()
    case_study_five()

    interview_questions()
    exam_questions()
    advanced_scenarios()
    advanced_comparison()
    decision_tree()
    glossary()
    final_case_classification()


if __name__ == "__main__":
    main()
