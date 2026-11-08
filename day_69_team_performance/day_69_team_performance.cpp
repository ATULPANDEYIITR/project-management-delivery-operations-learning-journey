#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class PerformanceBand {
    Excellent,
    Strong,
    Satisfactory,
    NeedsImprovement,
    Critical
};

enum class EvaluationStatus {
    Pending,
    Completed,
    Failed
};

struct TeamMetrics {
    double goalAchievement;
    double productivity;
    double workQuality;
    double collaboration;
    double reliability;
    double deliveryConsistency;
};

struct EvaluationWeights {
    double goalAchievement = 0.25;
    double productivity = 0.20;
    double workQuality = 0.20;
    double collaboration = 0.15;
    double reliability = 0.10;
    double deliveryConsistency = 0.10;

    void validate() const {
        const double values[] = {
            goalAchievement,
            productivity,
            workQuality,
            collaboration,
            reliability,
            deliveryConsistency
        };

        double total = 0;

        for (double value : values) {
            if (!isfinite(value) || value < 0 || value > 1) {
                throw invalid_argument("Invalid evaluation weight.");
            }
            total += value;
        }

        if (abs(total - 1.0) > 0.000001) {
            throw invalid_argument("Weights must total 1.0.");
        }
    }
};

struct Team {
    string id;
    string name;
    string department;
    string manager;
    int members;
    string evaluationPeriod;
    TeamMetrics metrics;
};

struct EvaluationResult {
    string teamId;
    string teamName;
    double score = 0;
    PerformanceBand band = PerformanceBand::Critical;
    EvaluationStatus status = EvaluationStatus::Pending;
    vector<string> strengths;
    vector<string> improvementAreas;
    optional<double> previousScore;
    string trend;
};

string bandName(PerformanceBand band) {
    switch (band) {
        case PerformanceBand::Excellent:
            return "Excellent";
        case PerformanceBand::Strong:
            return "Strong";
        case PerformanceBand::Satisfactory:
            return "Satisfactory";
        case PerformanceBand::NeedsImprovement:
            return "Needs Improvement";
        case PerformanceBand::Critical:
            return "Critical";
    }

    throw logic_error("Unknown performance band.");
}

PerformanceBand classify(double score) {
    if (score >= 90) return PerformanceBand::Excellent;
    if (score >= 80) return PerformanceBand::Strong;
    if (score >= 70) return PerformanceBand::Satisfactory;
    if (score >= 60) return PerformanceBand::NeedsImprovement;
    return PerformanceBand::Critical;
}

class TeamValidator {
public:
    static void validate(const Team& team) {
        if (team.id.empty() || team.name.empty() ||
            team.department.empty() || team.manager.empty()) {
            throw invalid_argument("Team identity fields are required.");
        }

        if (team.members <= 0) {
            throw invalid_argument("Team must contain members.");
        }

        if (team.evaluationPeriod.empty()) {
            throw invalid_argument("Evaluation period is required.");
        }

        const double values[] = {
            team.metrics.goalAchievement,
            team.metrics.productivity,
            team.metrics.workQuality,
            team.metrics.collaboration,
            team.metrics.reliability,
            team.metrics.deliveryConsistency
        };

        for (double value : values) {
            if (!isfinite(value) || value < 0 || value > 100) {
                throw invalid_argument(
                    "Metrics must be between 0 and 100."
                );
            }
        }
    }
};

class PerformanceEngine {
private:
    EvaluationWeights weights;

    map<string, Team> teams;
    map<string, vector<double>> history;
    map<string, EvaluationResult> results;

    static double weightedScore(
        const TeamMetrics& metrics,
        const EvaluationWeights& weights
    ) {
        return
            metrics.goalAchievement * weights.goalAchievement +
            metrics.productivity * weights.productivity +
            metrics.workQuality * weights.workQuality +
            metrics.collaboration * weights.collaboration +
            metrics.reliability * weights.reliability +
            metrics.deliveryConsistency * weights.deliveryConsistency;
    }

    static void identifyAreas(
        const TeamMetrics& metrics,
        EvaluationResult& result
    ) {
        const vector<pair<string, double>> values = {
            {"Goal Achievement", metrics.goalAchievement},
            {"Productivity", metrics.productivity},
            {"Work Quality", metrics.workQuality},
            {"Collaboration", metrics.collaboration},
            {"Reliability", metrics.reliability},
            {"Delivery Consistency", metrics.deliveryConsistency}
        };

        for (const auto& [name, score] : values) {
            if (score >= 85) {
                result.strengths.push_back(name);
            }

            if (score < 70) {
                result.improvementAreas.push_back(name);
            }
        }
    }

public:
    explicit PerformanceEngine(
        const EvaluationWeights& configuredWeights = EvaluationWeights()
    ) : weights(configuredWeights) {
        weights.validate();
    }

    void registerTeam(const Team& team) {
        TeamValidator::validate(team);

        if (teams.count(team.id)) {
            throw invalid_argument("Duplicate team identifier.");
        }

        teams.emplace(team.id, team);
    }

    void updateTeamMetrics(
        const string& teamId,
        const TeamMetrics& metrics
    ) {
        auto iterator = teams.find(teamId);

        if (iterator == teams.end()) {
            throw invalid_argument("Team not found.");
        }

        Team updated = iterator->second;
        updated.metrics = metrics;

        TeamValidator::validate(updated);

        iterator->second.metrics = metrics;
    }

    void recordHistoricalScore(
        const string& teamId,
        double score
    ) {
        if (!teams.count(teamId)) {
            throw invalid_argument("Unknown team.");
        }

        if (!isfinite(score) || score < 0 || score > 100) {
            throw invalid_argument("Invalid historical score.");
        }

        history[teamId].push_back(score);
    }

    EvaluationResult evaluate(const string& teamId) {
        auto iterator = teams.find(teamId);

        if (iterator == teams.end()) {
            throw invalid_argument("Team does not exist.");
        }

        const Team& team = iterator->second;

        EvaluationResult result;
        result.teamId = team.id;
        result.teamName = team.name;

        result.score = round(
            weightedScore(team.metrics, weights) * 100.0
        ) / 100.0;

        result.band = classify(result.score);
        result.status = EvaluationStatus::Completed;

        auto historyIterator = history.find(teamId);

        if (historyIterator != history.end() &&
            !historyIterator->second.empty()) {

            double previous = historyIterator->second.back();
            result.previousScore = previous;

            if (result.score > previous) {
                result.trend = "Improving";
            } else if (result.score < previous) {
                result.trend = "Declining";
            } else {
                result.trend = "Stable";
            }
        } else {
            result.trend = "Not Available";
        }

        identifyAreas(team.metrics, result);

        results[teamId] = result;

        return result;
    }

    vector<EvaluationResult> evaluateAll() {
        vector<EvaluationResult> evaluated;

        for (const auto& [teamId, team] : teams) {
            evaluated.push_back(evaluate(teamId));
        }

        sort(
            evaluated.begin(),
            evaluated.end(),
            [](const EvaluationResult& a, const EvaluationResult& b) {
                if (a.score != b.score) {
                    return a.score > b.score;
                }

                return a.teamId < b.teamId;
            }
        );

        return evaluated;
    }

    void printReport(const vector<EvaluationResult>& evaluated) const {
        cout << "\nTEAM PERFORMANCE EVALUATION\n";
        cout << string(85, '=') << '\n';

        cout << left
             << setw(22) << "Team"
             << setw(13) << "Score"
             << setw(23) << "Performance"
             << setw(15) << "Trend"
             << '\n';

        cout << string(85, '-') << '\n';

        for (const auto& result : evaluated) {
            cout << left
                 << setw(22) << result.teamName
                 << setw(13) << fixed << setprecision(2) << result.score
                 << setw(23) << bandName(result.band)
                 << setw(15) << result.trend
                 << '\n';
        }

        cout << "\nDETAILED PERFORMANCE AREAS\n";

        for (const auto& result : evaluated) {
            cout << "\n" << result.teamName << '\n';

            cout << "Strengths: ";

            for (const auto& item : result.strengths) {
                cout << item << "; ";
            }

            if (result.strengths.empty()) {
                cout << "None identified";
            }

            cout << "\nImprovement areas: ";

            for (const auto& item : result.improvementAreas) {
                cout << item << "; ";
            }

            if (result.improvementAreas.empty()) {
                cout << "None identified";
            }

            cout << '\n';
        }

        if (!evaluated.empty()) {
            double average = accumulate(
                evaluated.begin(),
                evaluated.end(),
                0.0,
                [](double total, const EvaluationResult& result) {
                    return total + result.score;
                }
            ) / evaluated.size();

            cout << "\nOrganization average: "
                 << fixed << setprecision(2) << average << '\n';
        }
    }
};

int main() {
    try {
        PerformanceEngine engine;

        vector<Team> teams = {
            {
                "T001",
                "Engineering",
                "Technology",
                "Manager A",
                12,
                "2026-Q4",
                {92, 88, 95, 85, 90, 87}
            },
            {
                "T002",
                "Customer Support",
                "Operations",
                "Manager B",
                10,
                "2026-Q4",
                {78, 85, 82, 91, 88, 80}
            },
            {
                "T003",
                "Research",
                "R&D",
                "Manager C",
                8,
                "2026-Q4",
                {95, 72, 90, 80, 75, 78}
            },
            {
                "T004",
                "Quality Assurance",
                "Technology",
                "Manager D",
                6,
                "2026-Q4",
                {65, 68, 92, 75, 70, 62}
            }
        };

        for (const auto& team : teams) {
            engine.registerTeam(team);
        }

        engine.recordHistoricalScore("T001", 84);
        engine.recordHistoricalScore("T002", 82);
        engine.recordHistoricalScore("T003", 80);
        engine.recordHistoricalScore("T004", 70);

        auto results = engine.evaluateAll();

        engine.printReport(results);

        cout << "\nVALIDATION TEST\n";

        try {
            Team invalidTeam = {
                "T005",
                "Invalid Team",
                "Technology",
                "Manager E",
                5,
                "2026-Q4",
                {110, 80, 80, 80, 80, 80}
            };

            engine.registerTeam(invalidTeam);
        } catch (const invalid_argument& error) {
            cout << "Invalid team rejected: "
                 << error.what() << '\n';
        }

        cout << "\nAll evaluations completed.\n";

    } catch (const exception& error) {
        cerr << "Evaluation system failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
