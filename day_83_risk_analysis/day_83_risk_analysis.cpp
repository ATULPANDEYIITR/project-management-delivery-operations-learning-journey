#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class RiskCategory {
    Strategic,
    Financial,
    Operational,
    Technology,
    Security,
    Compliance,
    Reputational
};

enum class RiskStatus {
    Identified,
    Assessed,
    Mitigating,
    Accepted,
    Closed
};

enum class Treatment {
    Accept,
    Mitigate,
    Transfer,
    Avoid
};

enum class RiskLevel {
    Low,
    Moderate,
    High,
    Critical
};


string toString(RiskCategory category) {
    switch (category) {
        case RiskCategory::Strategic: return "Strategic";
        case RiskCategory::Financial: return "Financial";
        case RiskCategory::Operational: return "Operational";
        case RiskCategory::Technology: return "Technology";
        case RiskCategory::Security: return "Security";
        case RiskCategory::Compliance: return "Compliance";
        case RiskCategory::Reputational: return "Reputational";
    }

    throw invalid_argument("Unknown risk category.");
}

string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low: return "Low";
        case RiskLevel::Moderate: return "Moderate";
        case RiskLevel::High: return "High";
        case RiskLevel::Critical: return "Critical";
    }

    throw invalid_argument("Unknown risk level.");
}

string toString(Treatment treatment) {
    switch (treatment) {
        case Treatment::Accept: return "Accept";
        case Treatment::Mitigate: return "Mitigate";
        case Treatment::Transfer: return "Transfer";
        case Treatment::Avoid: return "Avoid";
    }

    throw invalid_argument("Unknown treatment.");
}


struct Control {
    string name;
    double probabilityReduction;
    double impactReduction;

    Control(
        string controlName,
        double probabilityEffect,
        double impactEffect
    )
        : name(std::move(controlName)),
          probabilityReduction(probabilityEffect),
          impactReduction(impactEffect) {

        if (name.empty()) {
            throw invalid_argument("Control name is required.");
        }

        if (
            probabilityReduction < 0 ||
            probabilityReduction > 1 ||
            impactReduction < 0 ||
            impactReduction > 1
        ) {
            throw invalid_argument(
                "Control effectiveness must be between 0 and 1."
            );
        }
    }
};


class Risk {
private:
    string id;
    string title;
    string owner;
    RiskCategory category;

    double probability;
    double impact;

    RiskStatus status;
    vector<Control> controls;

public:
    Risk(
        string riskId,
        string riskTitle,
        RiskCategory riskCategory,
        double likelihood,
        double financialImpact,
        string riskOwner
    )
        : id(std::move(riskId)),
          title(std::move(riskTitle)),
          owner(std::move(riskOwner)),
          category(riskCategory),
          probability(likelihood),
          impact(financialImpact),
          status(RiskStatus::Identified) {

        if (id.empty() || title.empty() || owner.empty()) {
            throw invalid_argument(
                "Risk ID, title, and owner are required."
            );
        }

        validateAssessment(probability, impact);
    }

    static void validateAssessment(
        double probability,
        double impact
    ) {
        if (
            !isfinite(probability) ||
            probability < 0 ||
            probability > 1
        ) {
            throw invalid_argument(
                "Probability must be between 0 and 1."
            );
        }

        if (!isfinite(impact) || impact < 0) {
            throw invalid_argument(
                "Impact must be non-negative and finite."
            );
        }
    }

    const string& getId() const {
        return id;
    }

    const string& getTitle() const {
        return title;
    }

    double getProbability() const {
        return probability;
    }

    double getImpact() const {
        return impact;
    }

    RiskStatus getStatus() const {
        return status;
    }

    double inherentExposure() const {
        return probability * impact;
    }

    double residualProbability() const {
        double remaining = 1.0;

        for (const auto& control : controls) {
            remaining *=
                1.0 - control.probabilityReduction;
        }

        return probability * remaining;
    }

    double residualImpact() const {
        double remaining = 1.0;

        for (const auto& control : controls) {
            remaining *=
                1.0 - control.impactReduction;
        }

        return impact * remaining;
    }

    double residualExposure() const {
        return residualProbability() * residualImpact();
    }

    double mitigationPercentage() const {
        double original = inherentExposure();

        if (original == 0) {
            return 0;
        }

        return (
            1.0 - residualExposure() / original
        ) * 100.0;
    }

    RiskLevel classify() const {
        const double exposure = residualExposure();

        if (exposure >= 100000) {
            return RiskLevel::Critical;
        }

        if (exposure >= 25000) {
            return RiskLevel::High;
        }

        if (exposure >= 5000) {
            return RiskLevel::Moderate;
        }

        return RiskLevel::Low;
    }

    void addControl(const Control& control) {
        auto duplicate = find_if(
            controls.begin(),
            controls.end(),
            [&](const Control& existing) {
                return existing.name == control.name;
            }
        );

        if (duplicate != controls.end()) {
            throw invalid_argument("Duplicate control name.");
        }

        controls.push_back(control);
        status = RiskStatus::Mitigating;
    }

    void updateAssessment(
        double newProbability,
        double newImpact
    ) {
        validateAssessment(newProbability, newImpact);

        probability = newProbability;
        impact = newImpact;
        status = RiskStatus::Assessed;
    }

    void applyTreatment(Treatment treatment) {
        if (
            treatment == Treatment::Accept &&
            residualExposure() > 100000
        ) {
            throw invalid_argument(
                "Critical risk cannot be accepted without escalation."
            );
        }

        switch (treatment) {
            case Treatment::Accept:
                status = RiskStatus::Accepted;
                break;

            case Treatment::Mitigate:
                status = RiskStatus::Mitigating;
                break;

            case Treatment::Transfer:
                status = RiskStatus::Assessed;
                break;

            case Treatment::Avoid:
                status = RiskStatus::Closed;
                break;
        }
    }

    void display() const {
        cout << left
             << setw(10) << id
             << setw(30) << title.substr(0, 28)
             << right
             << setw(12) << fixed << setprecision(2)
             << probability * 100 << "%"
             << setw(15) << inherentExposure()
             << setw(15) << residualExposure()
             << "  " << toString(classify())
             << '\n';
    }
};


struct Policy {
    double maximumAcceptableExposure;
    double maximumAcceptableProbability;

    Policy(
        double maximumExposure,
        double maximumProbability
    )
        : maximumAcceptableExposure(maximumExposure),
          maximumAcceptableProbability(maximumProbability) {

        if (
            !isfinite(maximumAcceptableExposure) ||
            maximumAcceptableExposure < 0 ||
            !isfinite(maximumAcceptableProbability) ||
            maximumAcceptableProbability < 0 ||
            maximumAcceptableProbability > 1
        ) {
            throw invalid_argument("Invalid risk policy.");
        }
    }

    Treatment evaluate(const Risk& risk) const {
        if (
            risk.residualExposure() >
                maximumAcceptableExposure ||
            risk.residualProbability() >
                maximumAcceptableProbability
        ) {
            return Treatment::Mitigate;
        }

        return Treatment::Accept;
    }
};


class RiskRegister {
private:
    map<string, Risk> risks;

public:
    void add(const Risk& risk) {
        auto result = risks.emplace(risk.getId(), risk);

        if (!result.second) {
            throw invalid_argument("Duplicate risk ID.");
        }
    }

    Risk& get(const string& id) {
        auto iterator = risks.find(id);

        if (iterator == risks.end()) {
            throw out_of_range("Risk not found.");
        }

        return iterator->second;
    }

    vector<const Risk*> prioritized() const {
        vector<const Risk*> ordered;

        for (const auto& entry : risks) {
            ordered.push_back(&entry.second);
        }

        sort(
            ordered.begin(),
            ordered.end(),
            [](const Risk* a, const Risk* b) {
                return a->residualExposure() >
                       b->residualExposure();
            }
        );

        return ordered;
    }

    double inherentPortfolioExposure() const {
        double total = 0;

        for (const auto& entry : risks) {
            total += entry.second.inherentExposure();
        }

        return total;
    }

    double residualPortfolioExposure() const {
        double total = 0;

        for (const auto& entry : risks) {
            total += entry.second.residualExposure();
        }

        return total;
    }

    map<string, int> distribution() const {
        map<string, int> result;

        for (const auto& entry : risks) {
            result[toString(entry.second.classify())]++;
        }

        return result;
    }

    vector<const Risk*> all() const {
        vector<const Risk*> result;

        for (const auto& entry : risks) {
            result.push_back(&entry.second);
        }

        return result;
    }

    size_t size() const {
        return risks.size();
    }
};


struct SimulationResult {
    double mean;
    double median;
    double percentile95;
    double percentile99;
    double maximum;
};


SimulationResult simulatePortfolio(
    const vector<const Risk*>& risks,
    int iterations,
    unsigned int seed
) {
    if (iterations <= 0) {
        throw invalid_argument(
            "Simulation iterations must be positive."
        );
    }

    mt19937 generator(seed);
    uniform_real_distribution<double> distribution(0.0, 1.0);

    vector<double> losses;
    losses.reserve(iterations);

    for (int i = 0; i < iterations; ++i) {
        double totalLoss = 0;

        for (const Risk* risk : risks) {
            if (
                distribution(generator) <
                risk->residualProbability()
            ) {
                totalLoss += risk->residualImpact();
            }
        }

        losses.push_back(totalLoss);
    }

    sort(losses.begin(), losses.end());

    double total = 0;

    for (double loss : losses) {
        total += loss;
    }

    auto percentile = [&](double p) {
        size_t index = static_cast<size_t>(
            p * static_cast<double>(losses.size() - 1)
        );

        return losses[index];
    };

    return {
        total / iterations,
        percentile(0.50),
        percentile(0.95),
        percentile(0.99),
        losses.back()
    };
}


void printPortfolio(const RiskRegister& registry) {
    cout << "\nRISK PRIORITIZATION\n";

    cout << left
         << setw(10) << "Risk ID"
         << setw(30) << "Risk"
         << right
         << setw(12) << "Probability"
         << setw(15) << "Inherent"
         << setw(15) << "Residual"
         << "  Classification\n";

    cout << string(100, '-') << '\n';

    for (const Risk* risk : registry.prioritized()) {
        risk->display();
    }

    cout << "\nPORTFOLIO EXPOSURE\n";

    cout << "Inherent exposure: "
         << registry.inherentPortfolioExposure() << '\n';

    cout << "Residual exposure: "
         << registry.residualPortfolioExposure() << '\n';

    cout << "\nRISK DISTRIBUTION\n";

    for (const auto& entry : registry.distribution()) {
        cout << entry.first << ": " << entry.second << '\n';
    }
}


void runTests() {
    Risk risk(
        "TEST01",
        "Validation Risk",
        RiskCategory::Operational,
        0.8,
        10000,
        "Testing Department"
    );

    if (abs(risk.inherentExposure() - 8000) > 0.001) {
        throw runtime_error("Exposure calculation failed.");
    }

    risk.addControl(
        Control("Test Control", 0.5, 0.4)
    );

    if (abs(risk.residualExposure() - 2400) > 0.001) {
        throw runtime_error("Residual exposure calculation failed.");
    }

    bool rejected = false;

    try {
        Risk invalid(
            "INVALID",
            "Invalid Probability",
            RiskCategory::Operational,
            1.5,
            100,
            "Owner"
        );
    } catch (const invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw runtime_error("Invalid probability was accepted.");
    }

    cout << "All C++ validation tests passed.\n";
}


int main() {
    try {
        runTests();

        RiskRegister registry;

        Risk security(
            "R001",
            "Cybersecurity Breach",
            RiskCategory::Security,
            0.70,
            500000,
            "Security Department"
        );

        security.addControl(
            Control("Multi-factor Authentication", 0.40, 0.10)
        );

        security.addControl(
            Control("Security Monitoring", 0.15, 0.25)
        );

        Risk financial(
            "R002",
            "Budget Overrun",
            RiskCategory::Financial,
            0.45,
            120000,
            "Finance Department"
        );

        financial.addControl(
            Control("Budget Reviews", 0.25, 0.20)
        );

        Risk technology(
            "R003",
            "Cloud Infrastructure Failure",
            RiskCategory::Technology,
            0.30,
            80000,
            "IT Department"
        );

        technology.addControl(
            Control("Disaster Recovery", 0.20, 0.60)
        );

        Risk compliance(
            "R004",
            "Regulatory Noncompliance",
            RiskCategory::Compliance,
            0.20,
            250000,
            "Compliance Officer"
        );

        Risk operational(
            "R005",
            "Training Delay",
            RiskCategory::Operational,
            0.10,
            5000,
            "Operations Department"
        );

        registry.add(security);
        registry.add(financial);
        registry.add(technology);
        registry.add(compliance);
        registry.add(operational);

        Policy policy(25000, 0.50);

        cout << "\nRISK POLICY EVALUATION\n";

        for (const Risk* risk : registry.all()) {
            Treatment decision = policy.evaluate(*risk);

            cout << risk->getId() << " | "
                 << risk->getTitle() << " | "
                 << toString(decision) << '\n';
        }

        printPortfolio(registry);

        cout << "\nMONTE CARLO SIMULATION\n";

        SimulationResult result = simulatePortfolio(
            registry.all(),
            10000,
            42
        );

        cout << fixed << setprecision(2);

        cout << "Mean simulated loss: "
             << result.mean << '\n';

        cout << "Median loss: "
             << result.median << '\n';

        cout << "95th percentile loss: "
             << result.percentile95 << '\n';

        cout << "99th percentile loss: "
             << result.percentile99 << '\n';

        cout << "Maximum simulated loss: "
             << result.maximum << '\n';

    } catch (const exception& error) {
        cerr << "Risk analysis error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
