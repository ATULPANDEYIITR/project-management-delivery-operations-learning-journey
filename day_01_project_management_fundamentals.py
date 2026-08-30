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
