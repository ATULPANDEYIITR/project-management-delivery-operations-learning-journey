#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class Role {
    ProductManager,
    TechLead,
    Backend,
    Frontend,
    QA,
    DevOps,
    Data,
    Security,
    UX
};

enum class Availability {
    Available,
    Partial,
    Unavailable
};

std::string roleName(Role role) {
    switch (role) {
        case Role::ProductManager: return "Product Manager";
        case Role::TechLead: return "Technical Lead";
        case Role::Backend: return "Backend Engineer";
        case Role::Frontend: return "Frontend Engineer";
        case Role::QA: return "QA Engineer";
        case Role::DevOps: return "DevOps Engineer";
        case Role::Data: return "Data Engineer";
        case Role::Security: return "Security Engineer";
        case Role::UX: return "UX Designer";
    }
    return "Unknown";
}

std::string availabilityName(Availability value) {
    switch (value) {
        case Availability::Available: return "available";
        case Availability::Partial: return "partial";
        case Availability::Unavailable: return "unavailable";
    }
    return "unknown";
}

struct Candidate {
    std::string id;
    std::string name;
    std::set<std::string> skills;
    std::set<Role> roles;
    double experience;
    Availability availability;
};

struct Project {
    std::string id;
    std::string name;
    std::set<std::string> requiredSkills;
    std::set<Role> requiredRoles;
    std::size_t minTeamSize;
    std::size_t maxTeamSize;
};

class FormationEngine {
private:
    std::vector<Candidate> candidates;

    static double availabilityScore(Availability availability) {
        switch (availability) {
            case Availability::Available: return 3.0;
            case Availability::Partial: return 1.0;
            case Availability::Unavailable: return -100.0;
        }
        return -100.0;
    }

    static double score(const Candidate& candidate, const Project& project) {
        std::size_t skillMatches = 0;
        for (const auto& skill : candidate.skills) {
            if (project.requiredSkills.count(skill)) {
                ++skillMatches;
            }
        }

        std::size_t roleMatches = 0;
        for (const auto& role : candidate.roles) {
            if (project.requiredRoles.count(role)) {
                ++roleMatches;
            }
        }

        return static_cast<double>(skillMatches) * 4.0
             + static_cast<double>(roleMatches) * 6.0
             + std::min(candidate.experience, 10.0) * 0.25
             + availabilityScore(candidate.availability);
    }

    static bool containsRole(
        const std::vector<const Candidate*>& team,
        Role role
    ) {
        return std::any_of(
            team.begin(),
            team.end(),
            [role](const Candidate* candidate) {
                return candidate->roles.count(role) > 0;
            }
        );
    }

    static std::set<std::string> coveredSkills(
        const std::vector<const Candidate*>& team
    ) {
        std::set<std::string> result;

        for (const Candidate* candidate : team) {
            result.insert(candidate->skills.begin(), candidate->skills.end());
        }

        return result;
    }

    static std::set<std::string> missingSkills(
        const std::vector<const Candidate*>& team,
        const Project& project
    ) {
        const auto covered = coveredSkills(team);
        std::set<std::string> missing;

        std::set_difference(
            project.requiredSkills.begin(),
            project.requiredSkills.end(),
            covered.begin(),
            covered.end(),
            std::inserter(missing, missing.begin())
        );

        return missing;
    }

public:
    explicit FormationEngine(std::vector<Candidate> input)
        : candidates(std::move(input)) {
        std::set<std::string> ids;

        for (const auto& candidate : candidates) {
            if (!ids.insert(candidate.id).second) {
                throw std::invalid_argument("Duplicate candidate ID: " + candidate.id);
            }

            if (candidate.experience < 0) {
                throw std::invalid_argument("Negative experience: " + candidate.id);
            }
        }
    }

    std::vector<const Candidate*> formTeam(const Project& project) const {
        if (project.minTeamSize == 0 ||
            project.maxTeamSize < project.minTeamSize) {
            throw std::invalid_argument("Invalid project team-size policy.");
        }

        std::vector<const Candidate*> ranked;

        for (const auto& candidate : candidates) {
            if (candidate.availability != Availability::Unavailable) {
                ranked.push_back(&candidate);
            }
        }

        std::sort(
            ranked.begin(),
            ranked.end(),
            [&project](const Candidate* left, const Candidate* right) {
                return score(*left, project) > score(*right, project);
            }
        );

        std::vector<const Candidate*> team;
        std::set<std::string> selected;

        // Mandatory role coverage is handled before general optimization.
        for (Role requiredRole : project.requiredRoles) {
            auto iterator = std::find_if(
                ranked.begin(),
                ranked.end(),
                [&selected, requiredRole](const Candidate* candidate) {
                    return !selected.count(candidate->id) &&
                           candidate->roles.count(requiredRole);
                }
            );

            if (iterator == ranked.end()) {
                throw std::runtime_error(
                    "No eligible candidate for role: " + roleName(requiredRole)
                );
            }

            team.push_back(*iterator);
            selected.insert((*iterator)->id);
        }

        // Fill the minimum capacity using candidates that cover missing skills.
        while (team.size() < project.minTeamSize) {
            std::vector<const Candidate*> available;

            for (const Candidate* candidate : ranked) {
                if (!selected.count(candidate->id)) {
                    available.push_back(candidate);
                }
            }

            if (available.empty()) {
                throw std::runtime_error(
                    "Insufficient candidates for minimum team size."
                );
            }

            const auto missing = missingSkills(team, project);

            auto best = std::max_element(
                available.begin(),
                available.end(),
                [&missing](const Candidate* left, const Candidate* right) {
                    auto value = [&missing](const Candidate* candidate) {
                        std::size_t coverage = 0;

                        for (const auto& skill : candidate->skills) {
                            if (missing.count(skill)) ++coverage;
                        }

                        return std::make_pair(
                            coverage,
                            candidate->experience
                        );
                    };

                    return value(*left) < value(*right);
                }
            );

            team.push_back(*best);
            selected.insert((*best)->id);
        }

        // Optional seats require measurable skill coverage improvement.
        while (team.size() < project.maxTeamSize) {
            const auto before = missingSkills(team, project).size();

            const Candidate* best = nullptr;
            std::size_t bestCoverage = 0;

            for (const Candidate* candidate : ranked) {
                if (selected.count(candidate->id)) continue;

                std::size_t coverage = 0;
                const auto missing = missingSkills(team, project);

                for (const auto& skill : candidate->skills) {
                    if (missing.count(skill)) ++coverage;
                }

                if (coverage > bestCoverage) {
                    bestCoverage = coverage;
                    best = candidate;
                }
            }

            if (!best || bestCoverage == 0) break;

            team.push_back(best);
            selected.insert(best->id);

            const auto after = missingSkills(team, project).size();

            if (after >= before) {
                selected.erase(best->id);
                team.pop_back();
                break;
            }
        }

        return team;
    }

    static void validate(
        const std::vector<const Candidate*>& team,
        const Project& project
    ) {
        if (team.size() < project.minTeamSize ||
            team.size() > project.maxTeamSize) {
            throw std::runtime_error("Team size violates project policy.");
        }

        for (Role role : project.requiredRoles) {
            if (!containsRole(team, role)) {
                throw std::runtime_error(
                    "Missing mandatory role: " + roleName(role)
                );
            }
        }

        const auto missing = missingSkills(team, project);
        if (!missing.empty()) {
            throw std::runtime_error("Required skills remain uncovered.");
        }
    }
};

int main() {
    try {
        const std::vector<Candidate> candidates = {
            {
                "C001", "Aarav",
                {"roadmapping", "stakeholder-management", "analytics"},
                {Role::ProductManager},
                7,
                Availability::Available
            },
            {
                "C002", "Meera",
                {"architecture", "python", "postgresql", "security"},
                {Role::TechLead, Role::Backend},
                9,
                Availability::Available
            },
            {
                "C003", "Kabir",
                {"python", "fastapi", "postgresql", "testing"},
                {Role::Backend},
                5,
                Availability::Available
            },
            {
                "C004", "Diya",
                {"javascript", "react", "accessibility", "css"},
                {Role::Frontend, Role::UX},
                4,
                Availability::Available
            },
            {
                "C005", "Rohan",
                {"pytest", "automation", "testing", "quality"},
                {Role::QA},
                6,
                Availability::Available
            },
            {
                "C006", "Ishita",
                {"docker", "kubernetes", "ci-cd", "linux"},
                {Role::DevOps},
                6,
                Availability::Partial
            },
            {
                "C008", "Nisha",
                {"threat-modeling", "security", "iam", "python"},
                {Role::Security},
                7,
                Availability::Available
            }
        };

        const Project project{
            "P001",
            "Secure Operations Analytics Platform",
            {
                "roadmapping", "architecture", "python", "postgresql",
                "javascript", "testing", "docker", "security"
            },
            {
                Role::ProductManager,
                Role::TechLead,
                Role::Backend,
                Role::Frontend,
                Role::QA,
                Role::DevOps,
                Role::Security
            },
            7,
            8
        };

        FormationEngine engine(candidates);
        const auto team = engine.formTeam(project);

        FormationEngine::validate(team, project);

        std::cout << "Project: " << project.name << "\n";
        std::cout << "Team size: " << team.size() << "\n\n";

        for (const Candidate* candidate : team) {
            std::cout << std::left
                      << std::setw(8) << candidate->id
                      << std::setw(10) << candidate->name
                      << std::setw(12) << availabilityName(candidate->availability)
                      << " Roles: ";

            bool first = true;
            for (Role role : candidate->roles) {
                if (!first) std::cout << ", ";
                std::cout << roleName(role);
                first = false;
            }

            std::cout << "\n";
        }

        std::cout << "\nMerge-style governance analogy for team formation:\n";
        std::cout << "Project constraints -> candidate pool -> role coverage\n";
        std::cout << "-> skill coverage -> capacity validation -> team approval\n";

        std::cout << "\nValidation: PASSED\n";
    }
    catch (const std::exception& exception) {
        std::cerr << "Team formation failed: "
                  << exception.what() << '\n';
        return 1;
    }

    return 0;
}
