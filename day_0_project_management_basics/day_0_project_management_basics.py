# ============================================================
# DAY 00: PROJECT FUNDAMENTALS
# ============================================================

print("DAY 01 - PROJECT FUNDAMENTALS")


# ============================================================
# 1. WHAT IS A PROJECT?
# ============================================================

print("\n1. WHAT IS A PROJECT?")

print("A project is a temporary effort undertaken to")
print("create a unique product, service, or result.")

project = {
    "name": "Website Development",
    "duration": "12 weeks",
    "objective": "Launch a new business website",
    "status": "Planning"
}

for key, value in project.items():
    print(key, "->", value)


# ============================================================
# 2. PROJECT VS OPERATIONS
# ============================================================

print("\n2. PROJECT VS OPERATIONS")

comparison = {
    "Project": "Temporary and has a defined objective",
    "Operations": "Continuous and repetitive"
}

for category, meaning in comparison.items():
    print(category, "->", meaning)


# ============================================================
# 3. PROJECT OBJECTIVES
# ============================================================

print("\n3. PROJECT OBJECTIVES")

objectives = [
    "Define what the project should achieve",
    "Provide measurable outcomes",
    "Align the team with the project goal",
    "Provide a basis for evaluating success"
]

for objective in objectives:
    print("-", objective)


# ============================================================
# 4. PROJECT SUCCESS
# ============================================================

print("\n4. PROJECT SUCCESS")

success_factors = [
    "Scope",
    "Time",
    "Cost",
    "Quality",
    "Customer Satisfaction"
]

for factor in success_factors:
    print("-", factor)


# ============================================================
# 5. STAKEHOLDERS
# ============================================================

print("\n5. PROJECT STAKEHOLDERS")

stakeholders = [
    "Project Sponsor",
    "Project Manager",
    "Project Team",
    "Customer",
    "Users",
    "Management",
    "Vendors"
]

for stakeholder in stakeholders:
    print("-", stakeholder)


# ============================================================
# 6. REQUIREMENTS
# ============================================================

print("\n6. PROJECT REQUIREMENTS")

requirements = [
    "User Registration",
    "User Login",
    "Dashboard",
    "Payment System",
    "Email Notifications"
]

for number, requirement in enumerate(requirements, start=1):
    print(number, "->", requirement)


# ============================================================
# 7. SCOPE
# ============================================================

print("\n7. PROJECT SCOPE")

scope = {
    "In Scope": [
        "Website development",
        "User authentication",
        "Payment integration"
    ],
    "Out of Scope": [
        "Mobile application",
        "International payments",
        "Advanced analytics"
    ]
}

for category, items in scope.items():

    print("\n" + category)

    for item in items:
        print("-", item)


# ============================================================
# 8. DELIVERABLES
# ============================================================

print("\n8. PROJECT DELIVERABLES")

deliverables = [
    "Requirements Document",
    "UI Design",
    "Developed Website",
    "Test Report",
    "Production Release"
]

for deliverable in deliverables:
    print("-", deliverable)


# ============================================================
# 9. WORK BREAKDOWN STRUCTURE
# ============================================================

print("\n9. WORK BREAKDOWN STRUCTURE")

wbs = {
    "Planning": [
        "Requirements",
        "Stakeholder Analysis"
    ],
    "Design": [
        "UI Design",
        "Architecture"
    ],
    "Development": [
        "Frontend",
        "Backend"
    ],
    "Testing": [
        "Functional Testing",
        "Security Testing"
    ],
    "Deployment": [
        "Production Setup",
        "Release"
    ]
}

for phase, tasks in wbs.items():

    print("\n" + phase)

    for task in tasks:
        print("-", task)


# ============================================================
# 10. PROJECT PHASES
# ============================================================

print("\n10. PROJECT PHASES")

phases = [
    "Initiation",
    "Planning",
    "Execution",
    "Monitoring and Control",
    "Closure"
]

for number, phase in enumerate(phases, start=1):
    print(number, "->", phase)


# ============================================================
# 11. MILESTONES
# ============================================================

print("\n11. MILESTONES")

milestones = {
    "Week 2": "Requirements Completed",
    "Week 4": "Design Completed",
    "Week 8": "Development Completed",
    "Week 10": "Testing Completed",
    "Week 12": "Launch"
}

for date, milestone in milestones.items():
    print(date, "->", milestone)


# ============================================================
# 12. PROJECT SCHEDULE
# ============================================================

print("\n12. PROJECT SCHEDULE")

schedule = [
    ("Planning", 2),
    ("Design", 2),
    ("Development", 4),
    ("Testing", 2),
    ("Deployment", 2)
]

total_weeks = 0

for activity, weeks in schedule:

    print(activity, "->", weeks, "weeks")
    total_weeks += weeks

print("Total Duration:", total_weeks, "weeks")


# ============================================================
# 13. RESOURCES
# ============================================================

print("\n13. PROJECT RESOURCES")

resources = {
    "People": [
        "Project Manager",
        "Developer",
        "Designer",
        "Tester"
    ],
    "Technology": [
        "Development Environment",
        "Cloud Infrastructure",
        "Project Management Software"
    ],
    "Financial": [
        "Development Budget",
        "Infrastructure Budget"
    ]
}

for resource_type, items in resources.items():

    print("\n" + resource_type)

    for item in items:
        print("-", item)


# ============================================================
# 14. PROJECT BUDGET
# ============================================================

print("\n14. PROJECT BUDGET")

budget = {
    "Development": 300000,
    "Design": 75000,
    "Testing": 50000,
    "Infrastructure": 75000
}

total_budget = sum(budget.values())

for category, amount in budget.items():
    print(category, "-> ₹", amount)

print("Total Budget -> ₹", total_budget)


# ============================================================
# 15. RISKS
# ============================================================

print("\n15. PROJECT RISKS")

risks = [
    "Requirement changes",
    "Resource unavailability",
    "Technical problems",
    "Budget increase",
    "Schedule delay",
    "Security issues"
]

for risk in risks:
    print("-", risk)


# ============================================================
# 16. RISK REGISTER
# ============================================================

print("\n16. RISK REGISTER")

risk_register = [
    {
        "risk": "Schedule Delay",
        "probability": "Medium",
        "impact": "High",
        "response": "Maintain schedule buffer"
    },
    {
        "risk": "Resource Unavailability",
        "probability": "Low",
        "impact": "High",
        "response": "Cross-train team members"
    }
]

for risk in risk_register:

    print("\nRisk:", risk["risk"])
    print("Probability:", risk["probability"])
    print("Impact:", risk["impact"])
    print("Response:", risk["response"])


# ============================================================
# 17. ISSUES
# ============================================================

print("\n17. PROJECT ISSUES")

issue = {
    "id": 101,
    "description": "Payment integration is failing",
    "priority": "High",
    "status": "Open",
    "owner": "Backend Team"
}

for key, value in issue.items():
    print(key, "->", value)


# ============================================================
# 18. RISK VS ISSUE
# ============================================================

print("\n18. RISK VS ISSUE")

print("Risk   -> Something that may happen in the future.")
print("Issue  -> A problem that has already occurred.")


# ============================================================
# 19. DEPENDENCIES
# ============================================================

print("\n19. PROJECT DEPENDENCIES")

dependencies = [
    "Design must be completed before development",
    "Development must be completed before testing",
    "Testing must be completed before production release"
]

for dependency in dependencies:
    print("-", dependency)


# ============================================================
# 20. PROJECT COMMUNICATION
# ============================================================

print("\n20. PROJECT COMMUNICATION")

communication = {
    "Daily": "Team stand-up",
    "Weekly": "Project status meeting",
    "Milestone": "Stakeholder review",
    "Monthly": "Management report"
}

for frequency, activity in communication.items():
    print(frequency, "->", activity)


# ============================================================
# 21. PROJECT QUALITY
# ============================================================

print("\n21. PROJECT QUALITY")

quality_activities = [
    "Define quality standards",
    "Review requirements",
    "Test deliverables",
    "Track defects",
    "Validate final output"
]

for activity in quality_activities:
    print("-", activity)


# ============================================================
# 22. CHANGE MANAGEMENT
# ============================================================

print("\n22. CHANGE MANAGEMENT")

change_request = {
    "change": "Add multi-language support",
    "reason": "New customer requirement",
    "impact": "Additional development effort",
    "status": "Under Review"
}

for key, value in change_request.items():
    print(key, "->", value)


# ============================================================
# 23. PRIORITIZATION
# ============================================================

print("\n23. PRIORITIZATION")

tasks = [
    ("Fix payment failure", "Critical"),
    ("Build dashboard", "High"),
    ("Improve button design", "Low"),
    ("Update documentation", "Medium")
]

priority_order = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4
}

tasks_sorted = sorted(
    tasks,
    key=lambda task: priority_order[task[1]]
)

for task, priority in tasks_sorted:
    print(priority, "->", task)


# ============================================================
# 24. PROJECT STATUS
# ============================================================

print("\n24. PROJECT STATUS")

project_status = {
    "Scope": "On Track",
    "Schedule": "At Risk",
    "Budget": "On Track",
    "Quality": "On Track",
    "Risks": "Under Monitoring"
}

for area, status in project_status.items():
    print(area, "->", status)


# ============================================================
# 25. PROJECT CLOSURE
# ============================================================

print("\n25. PROJECT CLOSURE")

closure_steps = [
    "Complete deliverables",
    "Obtain customer acceptance",
    "Close contracts",
    "Document lessons learned",
    "Release project resources",
    "Archive project documentation"
]

for step_number, step in enumerate(closure_steps, start=1):
    print(step_number, "->", step)


# ============================================================
# 26. PROJECT MANAGEMENT WORKFLOW
# ============================================================

print("\n26. PROJECT MANAGEMENT WORKFLOW")

print("""
Project Idea
     ↓
Initiation
     ↓
Requirements
     ↓
Scope Definition
     ↓
Planning
     ↓
Execution
     ↓
Monitoring & Control
     ↓
Testing / Validation
     ↓
Delivery
     ↓
Closure
     ↓
Lessons Learned
""")


# ============================================================
# 27. COMMON PROJECT MANAGEMENT AREAS
# ============================================================

print("\n27. COMMON PROJECT MANAGEMENT AREAS")

areas = [
    "Scope Management",
    "Schedule Management",
    "Cost Management",
    "Quality Management",
    "Resource Management",
    "Risk Management",
    "Communication Management",
    "Stakeholder Management",
    "Procurement Management",
    "Change Management"
]

for area in areas:
    print("-", area)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. Projects
2. Projects vs Operations
3. Project Objectives
4. Project Success
5. Stakeholders
6. Requirements
7. Scope
8. Deliverables
9. Work Breakdown Structure
10. Project Phases
11. Milestones
12. Project Schedule
13. Resources
14. Budget
15. Risks
16. Risk Register
17. Issues
18. Risk vs Issue
19. Dependencies
20. Communication
21. Quality
22. Change Management
23. Prioritization
24. Project Status
25. Project Closure
26. Project Management Workflow
27. Project Management Areas
""")


# ============================================================
# DAY 01: PROJECT MANAGEMENT FUNDAMENTALS
# ============================================================

print("DAY 01 - PROJECT MANAGEMENT FUNDAMENTALS")


# ============================================================
# 1. WHAT IS PROJECT MANAGEMENT?
# ============================================================

print("\n1. WHAT IS PROJECT MANAGEMENT?")

print(
    "Project management is the application of knowledge, "
    "skills, tools, and techniques to plan and manage "
    "project work and achieve defined objectives."
)


# ============================================================
# 2. PROJECT MANAGER
# ============================================================

print("\n2. PROJECT MANAGER")

responsibilities = [
    "Planning",
    "Scheduling",
    "Resource Coordination",
    "Risk Management",
    "Stakeholder Management",
    "Communication",
    "Budget Monitoring",
    "Quality Management",
    "Issue Resolution",
    "Project Delivery"
]

for responsibility in responsibilities:
    print("-", responsibility)


# ============================================================
# 3. PROJECT MANAGEMENT CONSTRAINTS
# ============================================================

print("\n3. PROJECT MANAGEMENT CONSTRAINTS")

constraints = {
    "Scope": "What needs to be delivered",
    "Time": "When it needs to be delivered",
    "Cost": "How much it will cost",
    "Quality": "How well it must perform",
    "Resources": "People and assets required",
    "Risk": "Uncertainty that may affect the project"
}

for constraint, meaning in constraints.items():
    print(constraint, "->", meaning)


# ============================================================
# 4. PROJECT MANAGEMENT LIFE CYCLE
# ============================================================

print("\n4. PROJECT MANAGEMENT LIFE CYCLE")

lifecycle = [
    "Initiating",
    "Planning",
    "Executing",
    "Monitoring and Controlling",
    "Closing"
]

for number, phase in enumerate(lifecycle, start=1):
    print(number, "->", phase)


# ============================================================
# 5. PROJECT CHARTER
# ============================================================

print("\n5. PROJECT CHARTER")

project_charter = {
    "Project": "Customer Analytics Platform",
    "Objective": "Build a centralized analytics platform",
    "Sponsor": "Business Leadership",
    "Project Manager": "Project Manager",
    "Duration": "6 months",
    "Priority": "High"
}

for key, value in project_charter.items():
    print(key, "->", value)


# ============================================================
# 6. STAKEHOLDER MANAGEMENT
# ============================================================

print("\n6. STAKEHOLDER MANAGEMENT")

stakeholders = [
    ("Project Sponsor", "High", "High"),
    ("Customer", "High", "High"),
    ("Development Team", "High", "Medium"),
    ("Finance Team", "Medium", "Medium"),
    ("End Users", "Medium", "High"),
    ("Vendor", "Medium", "Low")
]

print("Stakeholder -> Power -> Interest")

for stakeholder, power, interest in stakeholders:
    print(stakeholder, "->", power, "->", interest)


# ============================================================
# 7. REQUIREMENTS MANAGEMENT
# ============================================================

print("\n7. REQUIREMENTS MANAGEMENT")

requirements = [
    {
        "id": "REQ-001",
        "requirement": "User Login",
        "priority": "High",
        "status": "Approved"
    },
    {
        "id": "REQ-002",
        "requirement": "Analytics Dashboard",
        "priority": "High",
        "status": "Approved"
    },
    {
        "id": "REQ-003",
        "requirement": "Export Reports",
        "priority": "Medium",
        "status": "Pending"
    }
]

for requirement in requirements:
    print(
        requirement["id"],
        "->",
        requirement["requirement"],
        "->",
        requirement["priority"],
        "->",
        requirement["status"]
    )


# ============================================================
# 8. WORK BREAKDOWN STRUCTURE
# ============================================================

print("\n8. WORK BREAKDOWN STRUCTURE")

wbs = {
    "Project Management": [
        "Planning",
        "Status Reporting"
    ],
    "Product Design": [
        "Requirements",
        "UI Design"
    ],
    "Development": [
        "Frontend",
        "Backend",
        "Database"
    ],
    "Testing": [
        "Functional Testing",
        "Security Testing"
    ],
    "Deployment": [
        "Production Setup",
        "Release"
    ]
}

for work_package, tasks in wbs.items():

    print("\n" + work_package)

    for task in tasks:
        print("  -", task)


# ============================================================
# 9. ESTIMATION
# ============================================================

print("\n9. PROJECT ESTIMATION")

tasks = {
    "Requirements": 20,
    "Design": 30,
    "Development": 120,
    "Testing": 50,
    "Deployment": 20
}

total_effort = sum(tasks.values())

for task, hours in tasks.items():
    print(task, "->", hours, "hours")

print("Total Estimated Effort:", total_effort, "hours")


# ============================================================
# 10. SCHEDULING
# ============================================================

print("\n10. PROJECT SCHEDULING")

schedule = [
    ("Requirements", 1, 2),
    ("Design", 3, 4),
    ("Development", 5, 10),
    ("Testing", 11, 13),
    ("Deployment", 14, 14)
]

print("Task -> Start Week -> End Week")

for task, start, end in schedule:
    print(task, "->", start, "->", end)


# ============================================================
# 11. DEPENDENCIES
# ============================================================

print("\n11. PROJECT DEPENDENCIES")

dependencies = [
    ("Requirements", "Design"),
    ("Design", "Development"),
    ("Development", "Testing"),
    ("Testing", "Deployment")
]

for predecessor, successor in dependencies:
    print(predecessor, "->", successor)


# ============================================================
# 12. CRITICAL PATH CONCEPT
# ============================================================

print("\n12. CRITICAL PATH")

critical_path = [
    "Requirements",
    "Design",
    "Development",
    "Testing",
    "Deployment"
]

print("Critical Path:")

for step in critical_path:
    print("->", step)

print(
    "\nThe critical path represents the sequence of "
    "activities that determines the minimum project duration."
)


# ============================================================
# 13. RISK MANAGEMENT
# ============================================================

print("\n13. RISK MANAGEMENT")

risks = [
    {
        "risk": "Resource shortage",
        "probability": "Medium",
        "impact": "High",
        "response": "Cross-training"
    },
    {
        "risk": "Technical failure",
        "probability": "Low",
        "impact": "High",
        "response": "Backup solution"
    },
    {
        "risk": "Requirement changes",
        "probability": "High",
        "impact": "Medium",
        "response": "Change control"
    }
]

for risk in risks:
    print("\nRisk:", risk["risk"])
    print("Probability:", risk["probability"])
    print("Impact:", risk["impact"])
    print("Response:", risk["response"])


# ============================================================
# 14. RISK SCORE
# ============================================================

print("\n14. RISK SCORE")

probability = 4
impact = 5

risk_score = probability * impact

print("Probability:", probability)
print("Impact:", impact)
print("Risk Score:", risk_score)


# ============================================================
# 15. ISSUE MANAGEMENT
# ============================================================

print("\n15. ISSUE MANAGEMENT")

issue = {
    "ID": "ISS-001",
    "Description": "Payment API is unavailable",
    "Priority": "Critical",
    "Owner": "Backend Team",
    "Status": "Open"
}

for key, value in issue.items():
    print(key, "->", value)


# ============================================================
# 16. CHANGE MANAGEMENT
# ============================================================

print("\n16. CHANGE MANAGEMENT")

change_request = {
    "ID": "CR-001",
    "Change": "Add advanced reporting",
    "Reason": "Customer requirement",
    "Impact": "2 additional weeks",
    "Status": "Under Review"
}

for key, value in change_request.items():
    print(key, "->", value)


# ============================================================
# 17. BUDGET MANAGEMENT
# ============================================================

print("\n17. BUDGET MANAGEMENT")

budget = {
    "People": 600000,
    "Technology": 150000,
    "Infrastructure": 100000,
    "Testing": 75000
}

planned_budget = sum(budget.values())

for category, amount in budget.items():
    print(category, "-> ₹", amount)

print("Planned Budget: ₹", planned_budget)


# ============================================================
# 18. ACTUAL VS PLANNED COST
# ============================================================

print("\n18. ACTUAL VS PLANNED COST")

planned_cost = 925000
actual_cost = 890000

variance = planned_cost - actual_cost

print("Planned Cost:", planned_cost)
print("Actual Cost:", actual_cost)
print("Cost Variance:", variance)


# ============================================================
# 19. QUALITY MANAGEMENT
# ============================================================

print("\n19. QUALITY MANAGEMENT")

quality_activities = [
    "Define quality standards",
    "Review requirements",
    "Conduct testing",
    "Track defects",
    "Perform quality reviews",
    "Validate deliverables"
]

for activity in quality_activities:
    print("-", activity)


# ============================================================
# 20. COMMUNICATION MANAGEMENT
# ============================================================

print("\n20. COMMUNICATION MANAGEMENT")

communication_plan = {
    "Daily": "Team coordination",
    "Weekly": "Project status",
    "Biweekly": "Stakeholder review",
    "Monthly": "Management reporting"
}

for frequency, purpose in communication_plan.items():
    print(frequency, "->", purpose)


# ============================================================
# 21. AGILE
# ============================================================

print("\n21. AGILE")

print(
    "Agile is an approach that emphasizes iterative delivery, "
    "customer feedback, collaboration, and adaptation."
)

agile_principles = [
    "Iterative Delivery",
    "Customer Collaboration",
    "Continuous Feedback",
    "Adaptability",
    "Frequent Delivery"
]

for principle in agile_principles:
    print("-", principle)


# ============================================================
# 22. SCRUM
# ============================================================

print("\n22. SCRUM")

scrum_roles = [
    "Product Owner",
    "Scrum Master",
    "Developers"
]

scrum_events = [
    "Sprint",
    "Sprint Planning",
    "Daily Scrum",
    "Sprint Review",
    "Sprint Retrospective"
]

print("Scrum Roles:")

for role in scrum_roles:
    print("-", role)

print("\nScrum Events:")

for event in scrum_events:
    print("-", event)


# ============================================================
# 23. KANBAN
# ============================================================

print("\n23. KANBAN")

kanban_board = {
    "To Do": [
        "Design dashboard",
        "Create API specification"
    ],
    "In Progress": [
        "Develop authentication"
    ],
    "Done": [
        "Requirements gathering"
    ]
}

for column, tasks in kanban_board.items():

    print("\n" + column)

    for task in tasks:
        print("-", task)


# ============================================================
# 24. PROJECT KPIs
# ============================================================

print("\n24. PROJECT KPIs")

kpis = {
    "Schedule Performance": "92%",
    "Budget Utilization": "88%",
    "Requirements Completed": "80%",
    "Defect Rate": "3%",
    "Milestones Completed": "7/8"
}

for kpi, value in kpis.items():
    print(kpi, "->", value)


# ============================================================
# 25. PROJECT STATUS
# ============================================================

print("\n25. PROJECT STATUS")

status = {
    "Scope": "On Track",
    "Schedule": "At Risk",
    "Budget": "On Track",
    "Quality": "On Track",
    "Risk": "Under Control"
}

for area, current_status in status.items():
    print(area, "->", current_status)


# ============================================================
# 26. PROJECT GOVERNANCE
# ============================================================

print("\n26. PROJECT GOVERNANCE")

governance = [
    "Decision Making",
    "Roles and Responsibilities",
    "Approvals",
    "Reporting",
    "Escalation",
    "Compliance",
    "Accountability"
]

for item in governance:
    print("-", item)


# ============================================================
# 27. PMO
# ============================================================

print("\n27. PROJECT MANAGEMENT OFFICE")

print("A PMO can provide standards, governance,")
print("templates, reporting, support, and oversight")
print("across projects or programs.")

pmo_functions = [
    "Standards",
    "Templates",
    "Reporting",
    "Governance",
    "Project Support",
    "Portfolio Visibility"
]

for function in pmo_functions:
    print("-", function)


# ============================================================
# 28. LESSONS LEARNED
# ============================================================

print("\n28. LESSONS LEARNED")

lessons = [
    "What went well?",
    "What went wrong?",
    "What should be improved?",
    "What should be repeated?",
    "What should be avoided?"
]

for question in lessons:
    print("-", question)


# ============================================================
# 29. PROJECT CLOSURE
# ============================================================

print("\n29. PROJECT CLOSURE")

closure = [
    "Complete deliverables",
    "Obtain acceptance",
    "Close outstanding issues",
    "Complete documentation",
    "Release resources",
    "Close contracts",
    "Capture lessons learned"
]

for step_number, step in enumerate(closure, start=1):
    print(step_number, "->", step)


# ============================================================
# 30. PROJECT MANAGEMENT FLOW
# ============================================================

print("\n30. PROJECT MANAGEMENT FLOW")

print("""
Business Need
      ↓
Project Initiation
      ↓
Requirements
      ↓
Scope Definition
      ↓
Planning
      ↓
Estimation
      ↓
Scheduling
      ↓
Execution
      ↓
Monitoring & Control
      ↓
Risk / Issue / Change Management
      ↓
Quality Validation
      ↓
Delivery
      ↓
Closure
      ↓
Lessons Learned
""")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. Project Management
2. Project Manager
3. Project Constraints
4. Project Management Life Cycle
5. Project Charter
6. Stakeholder Management
7. Requirements Management
8. Work Breakdown Structure
9. Estimation
10. Scheduling
11. Dependencies
12. Critical Path
13. Risk Management
14. Risk Scoring
15. Issue Management
16. Change Management
17. Budget Management
18. Cost Variance
19. Quality Management
20. Communication Management
21. Agile
22. Scrum
23. Kanban
24. Project KPIs
25. Project Status
26. Project Governance
27. PMO
28. Lessons Learned
29. Project Closure
30. Project Management Workflow
""")
