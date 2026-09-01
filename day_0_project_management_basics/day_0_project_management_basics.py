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
