# ============================================================
# WHAT IS A PROJECT?
# ============================================================

print("WHAT IS A PROJECT?")


# ============================================================
# 1. BASIC DEFINITION
# ============================================================

print("\n1. BASIC DEFINITION")

print("""
A project is a temporary effort undertaken to create
a unique product, service, or result.

A project has:
- A defined purpose
- A clear beginning
- A clear end
- Specific work to be completed
- Expected results or deliverables
""")


# ============================================================
# 2. EXAMPLE OF A PROJECT
# ============================================================

print("\n2. EXAMPLE OF A PROJECT")

project = {
    "name": "Business Website Development",
    "purpose": "Create a website for a business",
    "start_date": "1 September 2026",
    "end_date": "30 November 2026",
    "duration": "12 Weeks",
    "status": "Planning"
}

for key, value in project.items():
    print(key.replace("_", " ").title(), "->", value)


# ============================================================
# 3. MAIN CHARACTERISTICS OF A PROJECT
# ============================================================

print("\n3. MAIN CHARACTERISTICS OF A PROJECT")

characteristics = [
    "Temporary",
    "Unique",
    "Has a Defined Objective",
    "Has a Beginning and an End",
    "Uses Resources",
    "Produces Deliverables"
]

for number, characteristic in enumerate(characteristics, start=1):
    print(number, "->", characteristic)


# ============================================================
# 4. A PROJECT IS TEMPORARY
# ============================================================

print("\n4. A PROJECT IS TEMPORARY")

project_duration = {
    "Start": "Project begins",
    "Work Period": "Project activities are performed",
    "End": "Project objectives are completed"
}

for stage, meaning in project_duration.items():
    print(stage, "->", meaning)

print("""
A project does not continue forever.

It starts when the project work begins and ends when:
- The objectives are achieved
- The deliverables are completed
- The project is closed
""")


# ============================================================
# 5. A PROJECT CREATES SOMETHING UNIQUE
# ============================================================

print("\n5. A PROJECT CREATES SOMETHING UNIQUE")

unique_results = [
    "A new website",
    "A mobile application",
    "A software product",
    "A research report",
    "A marketing campaign",
    "A new business process"
]

for result in unique_results:
    print("-", result)

print("""
The final result of a project may be similar to something
that already exists, but the project itself has a specific
purpose, requirements, people, resources, and timeline.
""")


# ============================================================
# 6. PROJECT OBJECTIVE
# ============================================================

print("\n6. PROJECT OBJECTIVE")

objective = {
    "Project": "Develop an Online Learning Platform",
    "Objective": "Provide online courses to students",
    "Expected Result": "A working learning platform",
    "Success Measure": "Platform is launched successfully"
}

for key, value in objective.items():
    print(key, "->", value)


# ============================================================
# 7. PROJECT BEGINNING AND END
# ============================================================

print("\n7. PROJECT BEGINNING AND END")

project_lifecycle = [
    "Project Idea",
    "Project Initiation",
    "Project Planning",
    "Project Execution",
    "Project Monitoring",
    "Project Completion",
    "Project Closure"
]

for number, stage in enumerate(project_lifecycle, start=1):
    print(number, "->", stage)


# ============================================================
# 8. PROJECT RESOURCES
# ============================================================

print("\n8. PROJECT RESOURCES")

resources = {
    "People": [
        "Project Manager",
        "Developers",
        "Designers",
        "Testers"
    ],
    "Technology": [
        "Computers",
        "Software",
        "Cloud Services"
    ],
    "Financial": [
        "Development Budget",
        "Testing Budget",
        "Infrastructure Budget"
    ],
    "Time": [
        "Project Duration",
        "Working Hours",
        "Deadlines"
    ]
}

for resource_type, items in resources.items():

    print("\n" + resource_type)

    for item in items:
        print("-", item)


# ============================================================
# 9. PROJECT ACTIVITIES
# ============================================================

print("\n9. PROJECT ACTIVITIES")

activities = [
    "Collect Requirements",
    "Define Project Scope",
    "Create Project Plan",
    "Design the Solution",
    "Develop the Product",
    "Test the Product",
    "Deliver the Final Result"
]

for number, activity in enumerate(activities, start=1):
    print(number, "->", activity)


# ============================================================
# 10. PROJECT DELIVERABLES
# ============================================================

print("\n10. PROJECT DELIVERABLES")

deliverables = [
    "Project Plan",
    "Requirements Document",
    "Design Document",
    "Developed Product",
    "Testing Report",
    "Final Release"
]

for deliverable in deliverables:
    print("-", deliverable)

print("""
A deliverable is a result or output produced during
or at the end of a project.
""")


# ============================================================
# 11. EXAMPLE PROJECT
# ============================================================

print("\n11. COMPLETE PROJECT EXAMPLE")

website_project = {
    "Project Name": "E-Commerce Website Development",
    "Objective": "Build an online shopping website",
    "Duration": "6 Months",
    "Project Manager": "Assigned Project Manager",
    "Team Size": 8,
    "Budget": 500000,
    "Main Deliverable": "Working E-Commerce Website"
}

for key, value in website_project.items():

    if key == "Budget":
        print(key, "-> ₹", value)
    else:
        print(key, "->", value)


# ============================================================
# 12. PROJECT TASKS
# ============================================================

print("\n12. EXAMPLE PROJECT TASKS")

tasks = [
    {
        "task": "Requirements Collection",
        "status": "Completed"
    },
    {
        "task": "Website Design",
        "status": "In Progress"
    },
    {
        "task": "Website Development",
        "status": "Not Started"
    },
    {
        "task": "Testing",
        "status": "Not Started"
    },
    {
        "task": "Project Launch",
        "status": "Not Started"
    }
]

for task in tasks:
    print(task["task"], "->", task["status"])


# ============================================================
# 13. PROJECT VS DAILY WORK
# ============================================================

print("\n13. PROJECT VS DAILY WORK")

comparison = {
    "Project": {
        "Nature": "Temporary",
        "Purpose": "Create a specific result",
        "Duration": "Has a beginning and an end"
    },
    "Daily Work": {
        "Nature": "Continuous",
        "Purpose": "Perform regular activities",
        "Duration": "Continues regularly"
    }
}

for category, details in comparison.items():

    print("\n" + category)

    for key, value in details.items():
        print(key, "->", value)


# ============================================================
# 14. SIMPLE PROJECT FLOW
# ============================================================

print("\n14. SIMPLE PROJECT FLOW")

print("""
Project Idea
     ↓
Define Objective
     ↓
Plan the Work
     ↓
Assign Resources
     ↓
Perform Activities
     ↓
Create Deliverables
     ↓
Complete the Project
""")


# ============================================================
# 15. REAL-LIFE EXAMPLES OF PROJECTS
# ============================================================

print("\n15. REAL-LIFE EXAMPLES OF PROJECTS")

real_life_projects = [
    "Building a house",
    "Creating a website",
    "Developing a mobile application",
    "Launching a new product",
    "Organizing an event",
    "Conducting a research study",
    "Creating an online course",
    "Implementing a new software system"
]

for number, project_example in enumerate(real_life_projects, start=1):
    print(number, "->", project_example)


# ============================================================
# 16. CHECK IF AN ACTIVITY CAN BE A PROJECT
# ============================================================

print("\n16. PROJECT IDENTIFICATION EXAMPLE")

activity = {
    "name": "Develop a New Company Website",
    "temporary": True,
    "has_objective": True,
    "has_end_date": True,
    "creates_unique_result": True
}

print("Activity:", activity["name"])

if (
    activity["temporary"]
    and activity["has_objective"]
    and activity["has_end_date"]
    and activity["creates_unique_result"]
):
    print("Result -> This activity can be considered a project.")
else:
    print("Result -> This activity may not meet the basic characteristics of a project.")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("WHAT IS A PROJECT? - COMPLETED")
print("=" * 60)

print("""
A project is a temporary effort undertaken to create
a unique product, service, or result.

A project generally has:

1. A defined objective
2. A beginning
3. An end
4. A specific duration
5. Activities and tasks
6. Resources
7. Deliverables
8. People responsible for the work
9. A final result
""")
