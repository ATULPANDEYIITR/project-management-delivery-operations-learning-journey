#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Repository-development Activity Duration Estimation Engine
 *
 * The case study estimates the elapsed time required to complete a small
 * software delivery plan. Activities have optimistic, most-likely, and
 * pessimistic durations. The engine supports:
 *
 * - PERT expected duration
 * - uncertainty
 * - historical calibration
 * - dependency validation
 * - dependency-aware scheduling
 * - parallel branches
 * - Monte Carlo project-duration simulation
 * - estimation-error measurement
 *
 * The program intentionally separates "how long an activity may take" from
 * "when an activity can start". Dependencies affect the latter.
 */

enum class ActivityType {
    Analysis,
    Implementation,
    Testing,
    Documentation,
    Integration
};

std::string toString(ActivityType type) {
    switch (type) {
        case ActivityType::Analysis:
            return "Analysis";
        case ActivityType::Implementation:
            return "Implementation";
        case ActivityType::Testing:
            return "Testing";
        case ActivityType::Documentation:
            return "Documentation";
        case ActivityType::Integration:
            return "Integration";
    }

    return "Unknown";
}

class ThreePointEstimate {
public:
    ThreePointEstimate(double optimistic,
                       double mostLikely,
                       double pessimistic)
        : optimistic_(optimistic),
          mostLikely_(mostLikely),
          pessimistic_(pessimistic) {
        validate();
    }

    double optimistic() const {
        return optimistic_;
    }

    double mostLikely() const {
        return mostLikely_;
    }

    double pessimistic() const {
        return pessimistic_;
    }

    double expected() const {
        return (
            optimistic_ +
            4.0 * mostLikely_ +
            pessimistic_
        ) / 6.0;
    }

    double standardDeviation() const {
        return (pessimistic_ - optimistic_) / 6.0;
    }

private:
    double optimistic_;
    double mostLikely_;
    double pessimistic_;

    void validate() const {
        if (optimistic_ < 0 ||
            mostLikely_ < 0 ||
            pessimistic_ < 0) {
            throw std::invalid_argument(
                "Activity duration cannot be negative."
            );
        }

        if (!(optimistic_ <= mostLikely_ &&
              mostLikely_ <= pessimistic_)) {
            throw std::invalid_argument(
                "Expected optimistic <= mostLikely <= pessimistic."
            );
        }
    }
};

struct Activity {
    std::string name;
    ActivityType type;
    ThreePointEstimate estimate;
    std::vector<std::string> dependencies;
};

struct HistoricalObservation {
    ActivityType type;
    double estimatedHours;
    double actualHours;
};

struct ScheduledActivity {
    std::string name;
    double startHour;
    double finishHour;
};

class DurationEngine {
public:
    explicit DurationEngine(
        std::vector<HistoricalObservation> history)
        : history_(std::move(history)) {}

    double globalCalibrationFactor() const {
        double estimated = 0.0;
        double actual = 0.0;

        for (const auto& observation : history_) {
            estimated += observation.estimatedHours;
            actual += observation.actualHours;
        }

        if (estimated <= 0.0) {
            throw std::logic_error(
                "Historical estimates must contain positive total effort."
            );
        }

        return actual / estimated;
    }

    double typeCalibrationFactor(ActivityType type) const {
        double estimated = 0.0;
        double actual = 0.0;

        for (const auto& observation : history_) {
            if (observation.type == type) {
                estimated += observation.estimatedHours;
                actual += observation.actualHours;
            }
        }

        if (estimated <= 0.0) {
            return globalCalibrationFactor();
        }

        return actual / estimated;
    }

    double calibratedDuration(const Activity& activity) const {
        return activity.estimate.expected() *
               typeCalibrationFactor(activity.type);
    }

private:
    std::vector<HistoricalObservation> history_;
};

class DependencyGraph {
public:
    explicit DependencyGraph(
        const std::vector<Activity>& activities) {
        for (const auto& activity : activities) {
            if (activities_.contains(activity.name)) {
                throw std::invalid_argument(
                    "Duplicate activity name: " + activity.name
                );
            }

            activities_.emplace(activity.name, activity);
        }

        validateReferences();
    }

    std::vector<std::string> topologicalOrder() const {
        std::unordered_map<std::string, int> state;
        std::vector<std::string> order;

        for (const auto& [name, activity] : activities_) {
            visit(name, state, order);
        }

        return order;
    }

    const Activity& get(const std::string& name) const {
        return activities_.at(name);
    }

private:
    std::unordered_map<std::string, Activity> activities_;

    void validateReferences() const {
        for (const auto& [name, activity] : activities_) {
            for (const auto& dependency : activity.dependencies) {
                if (!activities_.contains(dependency)) {
                    throw std::invalid_argument(
                        "Activity '" + name +
                        "' references missing dependency '" +
                        dependency + "'."
                    );
                }
            }
        }
    }

    void visit(
        const std::string& name,
        std::unordered_map<std::string, int>& state,
        std::vector<std::string>& order) const {
        const int current = state[name];

        if (current == 1) {
            throw std::logic_error(
                "Circular dependency detected at: " + name
            );
        }

        if (current == 2) {
            return;
        }

        state[name] = 1;

        for (const auto& dependency : activities_.at(name).dependencies) {
            visit(dependency, state, order);
        }

        state[name] = 2;
        order.push_back(name);
    }
};

std::vector<ScheduledActivity> scheduleActivities(
    const std::vector<Activity>& activities,
    const DurationEngine& engine) {
    DependencyGraph graph(activities);
    const auto order = graph.topologicalOrder();

    std::unordered_map<std::string, double> finishTimes;
    std::vector<ScheduledActivity> result;

    for (const auto& name : order) {
        const Activity& activity = graph.get(name);
        double start = 0.0;

        for (const auto& dependency : activity.dependencies) {
            start = std::max(start, finishTimes.at(dependency));
        }

        const double duration = engine.calibratedDuration(activity);
        const double finish = start + duration;

        finishTimes[name] = finish;

        result.push_back({
            name,
            start,
            finish
        });
    }

    return result;
}

double projectDuration(
    const std::vector<Activity>& activities,
    std::mt19937& generator) {
    DependencyGraph graph(activities);
    const auto order = graph.topologicalOrder();

    std::unordered_map<std::string, double> finishTimes;

    for (const auto& name : order) {
        const auto& activity = graph.get(name);

        double start = 0.0;

        for (const auto& dependency : activity.dependencies) {
            start = std::max(start, finishTimes.at(dependency));
        }

        std::uniform_real_distribution<double> distribution(
            0.0,
            1.0
        );

        const double u = distribution(generator);
        const double a = activity.estimate.optimistic();
        const double b = activity.estimate.mostLikely();
        const double c = activity.estimate.pessimistic();

        double duration;

        if (a == c) {
            duration = a;
        } else {
            const double modePosition = (b - a) / (c - a);

            if (u < modePosition) {
                duration = a +
                    std::sqrt(u * (b - a) * (c - a));
            } else {
                duration = c -
                    std::sqrt((1.0 - u) * (c - b) * (c - a));
            }
        }

        finishTimes[name] = start + duration;
    }

    double projectFinish = 0.0;

    for (const auto& [name, finish] : finishTimes) {
        projectFinish = std::max(projectFinish, finish);
    }

    return projectFinish;
}

double percentile(
    std::vector<double> values,
    double percentage) {
    if (values.empty()) {
        throw std::invalid_argument(
            "Cannot calculate percentile from empty data."
        );
    }

    if (percentage < 0.0 || percentage > 100.0) {
        throw std::invalid_argument(
            "Percentile must be between 0 and 100."
        );
    }

    std::sort(values.begin(), values.end());

    const double position =
        (values.size() - 1) * percentage / 100.0;

    const std::size_t lower =
        static_cast<std::size_t>(std::floor(position));

    const std::size_t upper =
        static_cast<std::size_t>(std::ceil(position));

    if (lower == upper) {
        return values[lower];
    }

    const double fraction = position - lower;

    return values[lower] +
           (values[upper] - values[lower]) * fraction;
}

struct EstimationMetrics {
    double meanAbsoluteError;
    double meanAbsolutePercentageError;
    double signedBias;
};

EstimationMetrics calculateMetrics(
    const std::vector<double>& estimated,
    const std::vector<double>& actual) {
    if (estimated.empty() ||
        estimated.size() != actual.size()) {
        throw std::invalid_argument(
            "Estimated and actual samples must have equal non-zero size."
        );
    }

    double absoluteError = 0.0;
    double percentageError = 0.0;
    double bias = 0.0;
    std::size_t percentageSamples = 0;

    for (std::size_t i = 0; i < estimated.size(); ++i) {
        absoluteError += std::abs(actual[i] - estimated[i]);
        bias += actual[i] - estimated[i];

        if (estimated[i] > 0.0) {
            percentageError +=
                std::abs(actual[i] - estimated[i]) /
                estimated[i];
            ++percentageSamples;
        }
    }

    if (percentageSamples == 0) {
        throw std::invalid_argument(
            "At least one estimate must be positive."
        );
    }

    const double count =
        static_cast<double>(estimated.size());

    return {
        absoluteError / count,
        percentageError /
            static_cast<double>(percentageSamples) * 100.0,
        bias / count
    };
}

void printHeader(const std::string& title) {
    std::cout << "\n"
              << std::string(76, '=')
              << "\n"
              << title
              << "\n"
              << std::string(76, '=')
              << "\n";
}

int main() {
    try {
        printHeader("Repository Development Activity Duration Engine");

        std::vector<HistoricalObservation> history = {
            {ActivityType::Analysis, 6, 8},
            {ActivityType::Analysis, 10, 11},
            {ActivityType::Implementation, 14, 19},
            {ActivityType::Implementation, 20, 24},
            {ActivityType::Testing, 10, 9},
            {ActivityType::Testing, 15, 18},
            {ActivityType::Documentation, 5, 6},
            {ActivityType::Integration, 9, 13},
            {ActivityType::Integration, 12, 16}
        };

        DurationEngine engine(history);

        std::cout << std::fixed << std::setprecision(2);

        std::cout
            << "Historical global calibration factor: "
            << engine.globalCalibrationFactor()
            << "\n";

        std::vector<Activity> activities = {
            {
                "Requirements analysis",
                ActivityType::Analysis,
                ThreePointEstimate(3, 5, 9),
                {}
            },
            {
                "Backend implementation",
                ActivityType::Implementation,
                ThreePointEstimate(12, 18, 30),
                {"Requirements analysis"}
            },
            {
                "Frontend implementation",
                ActivityType::Implementation,
                ThreePointEstimate(10, 15, 26),
                {"Requirements analysis"}
            },
            {
                "Backend verification",
                ActivityType::Testing,
                ThreePointEstimate(5, 8, 15),
                {"Backend implementation"}
            },
            {
                "Frontend verification",
                ActivityType::Testing,
                ThreePointEstimate(4, 7, 13),
                {"Frontend implementation"}
            },
            {
                "System integration",
                ActivityType::Integration,
                ThreePointEstimate(6, 10, 18),
                {
                    "Backend verification",
                    "Frontend verification"
                }
            }
        };

        printHeader("Calibrated Activity Durations");

        for (const auto& activity : activities) {
            std::cout
                << std::left
                << std::setw(28)
                << activity.name
                << "PERT="
                << std::setw(7)
                << activity.estimate.expected()
                << " calibrated="
                << engine.calibratedDuration(activity)
                << " h\n";
        }

        printHeader("Dependency-Aware Schedule");

        const auto schedule =
            scheduleActivities(activities, engine);

        for (const auto& item : schedule) {
            std::cout
                << std::left
                << std::setw(28)
                << item.name
                << "start="
                << std::setw(7)
                << item.startHour
                << "finish="
                << item.finishHour
                << " h\n";
        }

        const double deterministicFinish =
            std::max_element(
                schedule.begin(),
                schedule.end(),
                [](const auto& left, const auto& right) {
                    return left.finishHour < right.finishHour;
                }
            )->finishHour;

        std::cout
            << "\nCalibrated expected project duration: "
            << deterministicFinish
            << " h\n";

        printHeader("Monte Carlo Project Duration");

        constexpr int simulations = 20000;
        std::mt19937 generator(20261005);
        std::vector<double> simulated;
        simulated.reserve(simulations);

        for (int i = 0; i < simulations; ++i) {
            simulated.push_back(
                projectDuration(activities, generator)
            );
        }

        std::cout
            << "Median: "
            << percentile(simulated, 50)
            << " h\n"
            << "80th percentile: "
            << percentile(simulated, 80)
            << " h\n"
            << "90th percentile: "
            << percentile(simulated, 90)
            << " h\n"
            << "95th percentile: "
            << percentile(simulated, 95)
            << " h\n";

        printHeader("Estimation Quality");

        const std::vector<double> estimated = {
            8, 12, 16, 10, 20, 14
        };

        const std::vector<double> actual = {
            9, 15, 13, 11, 24, 12
        };

        const auto metrics =
            calculateMetrics(estimated, actual);

        std::cout
            << "Mean absolute error: "
            << metrics.meanAbsoluteError
            << " h\n"
            << "Mean absolute percentage error: "
            << metrics.meanAbsolutePercentageError
            << "%\n"
            << "Signed bias: "
            << metrics.signedBias
            << " h\n";

        printHeader("Technical Interpretation");

        std::cout
            << "A three-point estimate describes uncertainty in one activity.\n"
            << "Historical calibration adjusts the estimate using observed "
               "duration behavior.\n"
            << "Dependencies determine when an activity may start.\n"
            << "Independent branches can reduce elapsed project duration "
               "when they execute concurrently.\n"
            << "Monte Carlo simulation exposes percentile-based schedule "
               "risk rather than relying on a single point estimate.\n"
            << "Estimation quality should be measured against completed "
               "activities so systematic bias can be detected.\n";

        printHeader("Validation Demonstration");

        try {
            ThreePointEstimate invalid(12, 8, 20);
            (void)invalid;
        } catch (const std::exception& error) {
            std::cout
                << "Rejected invalid three-point estimate: "
                << error.what()
                << "\n";
        }

        try {
            std::vector<Activity> circular = {
                {
                    "A",
                    ActivityType::Implementation,
                    ThreePointEstimate(1, 2, 4),
                    {"B"}
                },
                {
                    "B",
                    ActivityType::Testing,
                    ThreePointEstimate(1, 2, 4),
                    {"A"}
                }
            };

            DependencyGraph graph(circular);
            graph.topologicalOrder();
        } catch (const std::exception& error) {
            std::cout
                << "Rejected circular activity graph: "
                << error.what()
                << "\n";
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal estimation-engine error: "
            << error.what()
            << "\n";

        return 1;
    }
}
