#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * Team Motivation Assessment and Intervention Engine
 *
 * C++17 implementation.
 *
 * Models:
 * - Team members
 * - Motivation dimensions
 * - Individual motivation assessments
 * - Workload risk
 * - Recognition
 * - Team goals
 * - Intervention planning
 * - Team-level reporting
 */

enum class MotivationLevel {
    HIGH,
    MODERATE,
    LOW,
    CRITICAL
};

enum class RecognitionType {
    PUBLIC,
    PRIVATE,
    DEVELOPMENT,
    TEAM,
    FINANCIAL
};

enum class GoalStatus {
    NOT_STARTED,
    IN_PROGRESS,
    COMPLETED,
    BLOCKED
};

string toString(MotivationLevel level) {
    switch (level) {
        case MotivationLevel::HIGH:
            return "HIGH";
        case MotivationLevel::MODERATE:
            return "MODERATE";
        case MotivationLevel::LOW:
            return "LOW";
        case MotivationLevel::CRITICAL:
            return "CRITICAL";
    }

    throw logic_error("Unknown motivation level.");
}

struct TeamMember {
    int id;
    string name;
    string role;

    double autonomy;
    double competence;
    double relatedness;
    double workload;
    double psychologicalSafety;
    double engagement;
    double intrinsicMotivation;
    double extrinsicMotivation;
};

struct TeamGoal {
    int id;
    int ownerId;
    string description;
    double target;
    double progress = 0;
    GoalStatus status = GoalStatus::NOT_STARTED;
};

struct Recognition {
    int id;
    int memberId;
    RecognitionType type;
    string reason;
};

struct Assessment {
    int memberId;
    string memberName;
    double score;
    MotivationLevel level;
    vector<string> risks;
    vector<string> actions;
};

class MotivationEngine {

private:

    map<int, TeamMember> members;
    map<int, TeamGoal> goals;
    vector<Recognition> recognitions;

    static void validateScore(
        double value,
        const string& field
    ) {
        if (value < 0 || value > 100) {
            throw invalid_argument(
                field + " must be between 0 and 100."
            );
        }
    }

    const TeamMember& getMember(int id) const {
        auto it = members.find(id);

        if (it == members.end()) {
            throw out_of_range("Team member not found.");
        }

        return it->second;
    }

public:

    void addMember(const TeamMember& member) {

        if (member.id <= 0) {
            throw invalid_argument("Member ID must be positive.");
        }

        if (
            member.name.empty() ||
            member.role.empty()
        ) {
            throw invalid_argument(
                "Member name and role are required."
            );
        }

        validateScore(member.autonomy, "Autonomy");
        validateScore(member.competence, "Competence");
        validateScore(member.relatedness, "Relatedness");
        validateScore(member.workload, "Workload");

        validateScore(
            member.psychologicalSafety,
            "Psychological safety"
        );

        validateScore(member.engagement, "Engagement");

        validateScore(
            member.intrinsicMotivation,
            "Intrinsic motivation"
        );

        validateScore(
            member.extrinsicMotivation,
            "Extrinsic motivation"
        );

        auto result = members.emplace(member.id, member);

        if (!result.second) {
            throw invalid_argument(
                "Duplicate team member ID."
            );
        }
    }

    void addGoal(const TeamGoal& goal) {

        if (goal.id <= 0 || goal.target <= 0) {
            throw invalid_argument("Invalid goal identifier or target.");
        }

        getMember(goal.ownerId);

        if (goals.count(goal.id)) {
            throw invalid_argument("Duplicate goal ID.");
        }

        if (goal.progress < 0 || goal.progress > goal.target) {
            throw invalid_argument("Invalid initial goal progress.");
        }

        goals.emplace(goal.id, goal);
    }

    void updateGoal(int goalId, double progress) {

        auto it = goals.find(goalId);

        if (it == goals.end()) {
            throw out_of_range("Goal not found.");
        }

        TeamGoal& goal = it->second;

        if (progress < 0 || progress > goal.target) {
            throw invalid_argument("Invalid goal progress.");
        }

        goal.progress = progress;

        if (progress == goal.target) {
            goal.status = GoalStatus::COMPLETED;
        } else if (progress > 0) {
            goal.status = GoalStatus::IN_PROGRESS;
        } else {
            goal.status = GoalStatus::NOT_STARTED;
        }
    }

    void awardRecognition(const Recognition& recognition) {

        getMember(recognition.memberId);

        if (recognition.reason.empty()) {
            throw invalid_argument(
                "Recognition reason is required."
            );
        }

        recognitions.push_back(recognition);
    }

    double calculateMotivation(int memberId) const {

        const TeamMember& m = getMember(memberId);

        /*
         * Weighted motivation model.
         * Workload is converted into workload balance.
         */
        double score =
            m.autonomy * 0.18 +
            m.competence * 0.18 +
            m.relatedness * 0.16 +
            m.psychologicalSafety * 0.16 +
            m.engagement * 0.14 +
            m.intrinsicMotivation * 0.12 +
            (100 - m.workload) * 0.06;

        return clamp(score, 0.0, 100.0);
    }

    MotivationLevel classify(double score) const {

        if (score >= 80) {
            return MotivationLevel::HIGH;
        }

        if (score >= 65) {
            return MotivationLevel::MODERATE;
        }

        if (score >= 45) {
            return MotivationLevel::LOW;
        }

        return MotivationLevel::CRITICAL;
    }

    Assessment evaluate(int memberId) const {

        const TeamMember& m = getMember(memberId);

        Assessment result{
            m.id,
            m.name,
            calculateMotivation(memberId),
            MotivationLevel::CRITICAL,
            {},
            {}
        };

        result.level = classify(result.score);

        if (m.workload >= 85) {
            result.risks.push_back(
                "High workload and potential burnout"
            );
        }

        if (m.autonomy < 40) {
            result.risks.push_back(
                "Insufficient decision-making autonomy"
            );
        }

        if (m.competence < 40) {
            result.risks.push_back(
                "Skill development requirement"
            );
        }

        if (m.relatedness < 40) {
            result.risks.push_back(
                "Weak team relationships"
            );
        }

        if (m.psychologicalSafety < 40) {
            result.risks.push_back(
                "Low psychological safety"
            );
        }

        if (m.engagement < 40) {
            result.risks.push_back(
                "Low engagement"
            );
        }

        if (m.workload > 70) {
            result.actions.push_back(
                "Review and redistribute workload."
            );
        }

        if (m.autonomy < 60) {
            result.actions.push_back(
                "Increase ownership and decision authority."
            );
        }

        if (m.competence < 60) {
            result.actions.push_back(
                "Provide training and mentoring."
            );
        }

        if (m.relatedness < 60) {
            result.actions.push_back(
                "Improve collaboration and peer interaction."
            );
        }

        if (m.psychologicalSafety < 60) {
            result.actions.push_back(
                "Improve communication and feedback practices."
            );
        }

        if (m.engagement < 60) {
            result.actions.push_back(
                "Conduct an individual engagement discussion."
            );
        }

        if (result.actions.empty()) {
            result.actions.push_back(
                "Maintain engagement and development practices."
            );
        }

        return result;
    }

    vector<Assessment> assessTeam() const {

        if (members.empty()) {
            throw logic_error("Cannot assess an empty team.");
        }

        vector<Assessment> results;
        results.reserve(members.size());

        for (const auto& entry : members) {
            results.push_back(evaluate(entry.first));
        }

        return results;
    }

    void printReport() const {

        vector<Assessment> assessments = assessTeam();

        double total = 0;

        map<MotivationLevel, int> distribution;

        cout << fixed << setprecision(2);

        cout << "\nINDIVIDUAL MOTIVATION ASSESSMENT\n";

        for (const Assessment& a : assessments) {

            total += a.score;
            distribution[a.level]++;

            cout << "\nMember: " << a.memberName << '\n';
            cout << "Score: " << a.score << '\n';
            cout << "Level: " << toString(a.level) << '\n';

            cout << "Risks:\n";

            if (a.risks.empty()) {
                cout << "  No major identified risks.\n";
            }

            for (const string& risk : a.risks) {
                cout << "  - " << risk << '\n';
            }

            cout << "Recommended actions:\n";

            for (const string& action : a.actions) {
                cout << "  - " << action << '\n';
            }
        }

        cout << "\nTEAM REPORT\n";

        cout << "Team size: " << assessments.size() << '\n';

        cout << "Average motivation: "
             << total / assessments.size()
             << '\n';

        cout << "Motivation distribution:\n";

        for (const auto& entry : distribution) {
            cout << "  "
                 << toString(entry.first)
                 << ": "
                 << entry.second
                 << '\n';
        }

        cout << "Total goals: " << goals.size() << '\n';
        cout << "Recognition records: "
             << recognitions.size()
             << '\n';
    }
};

int main() {

    try {

        MotivationEngine engine;

        engine.addMember({
            1,
            "Ananya",
            "Software Developer",
            85, 90, 80, 55, 90, 88, 90, 65
        });

        engine.addMember({
            2,
            "Rahul",
            "Business Analyst",
            35, 55, 45, 90, 40, 38, 45, 70
        });

        engine.addMember({
            3,
            "Priya",
            "Project Manager",
            75, 80, 85, 65, 85, 78, 80, 75
        });

        engine.addGoal({
            101,
            1,
            "Complete quarterly product release",
            100
        });

        engine.updateGoal(101, 65);

        engine.awardRecognition({
            1,
            1,
            RecognitionType::PUBLIC,
            "Resolved a critical production issue."
        });

        engine.awardRecognition({
            2,
            3,
            RecognitionType::DEVELOPMENT,
            "Successfully coordinated product delivery."
        });

        engine.printReport();

        cout << "\nVALIDATION TEST\n";

        try {

            engine.addMember({
                4,
                "Test",
                "Intern",
                120, 50, 50, 50, 50, 50, 50, 50
            });

        } catch (const exception& e) {
            cout << "Expected validation error: "
                 << e.what()
                 << '\n';
        }

    } catch (const exception& e) {

        cerr << "Application error: "
             << e.what()
             << '\n';

        return 1;
    }

    return 0;
}
