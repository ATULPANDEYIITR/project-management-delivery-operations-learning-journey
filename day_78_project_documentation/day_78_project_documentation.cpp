#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ============================================================
// PROJECT DOCUMENTATION AND GOVERNANCE ENGINE
// C++17
// ============================================================

using DocumentId = int;
using UserId = int;
using ProjectId = int;
using VersionNumber = int;

// ============================================================
// ENUMERATIONS
// ============================================================

enum class DocumentType {
    Requirements,
    ProjectPlan,
    TechnicalSpecification,
    Design,
    MeetingMinutes,
    ProgressReport,
    RiskRegister,
    TestReport,
    UserGuide,
    ClosureReport
};

enum class DocumentStatus {
    Draft,
    UnderReview,
    Approved,
    Rejected,
    Archived
};

enum class Role {
    Admin,
    ProjectManager,
    Author,
    Reviewer,
    Viewer
};

enum class ReviewDecision {
    Approved,
    Rejected,
    ChangesRequested
};

// ============================================================
// ENUMERATION CONVERSION
// ============================================================

string toString(DocumentStatus status) {
    switch (status) {
        case DocumentStatus::Draft: return "Draft";
        case DocumentStatus::UnderReview: return "Under Review";
        case DocumentStatus::Approved: return "Approved";
        case DocumentStatus::Rejected: return "Rejected";
        case DocumentStatus::Archived: return "Archived";
    }

    throw logic_error("Unknown document status.");
}

string toString(DocumentType type) {
    switch (type) {
        case DocumentType::Requirements: return "Requirements";
        case DocumentType::ProjectPlan: return "Project Plan";
        case DocumentType::TechnicalSpecification:
            return "Technical Specification";
        case DocumentType::Design: return "Design";
        case DocumentType::MeetingMinutes: return "Meeting Minutes";
        case DocumentType::ProgressReport: return "Progress Report";
        case DocumentType::RiskRegister: return "Risk Register";
        case DocumentType::TestReport: return "Test Report";
        case DocumentType::UserGuide: return "User Guide";
        case DocumentType::ClosureReport: return "Closure Report";
    }

    throw logic_error("Unknown document type.");
}

// ============================================================
// DOMAIN STRUCTURES
// ============================================================

struct User {
    UserId id;
    string name;
    string email;
    Role role;
    bool active = true;
};

struct Project {
    ProjectId id;
    string name;
};

struct DocumentVersion {
    VersionNumber number;
    string content;
    string checksum;
    UserId authorId;
    string changeDescription;
    chrono::system_clock::time_point createdAt;
};

struct Review {
    int id;
    UserId reviewerId;
    VersionNumber version;
    ReviewDecision decision;
    string comments;
};

struct ProjectDocument {
    DocumentId id;
    ProjectId projectId;
    string title;
    DocumentType type;
    UserId ownerId;

    DocumentStatus status = DocumentStatus::Draft;

    VersionNumber currentVersion = 1;

    vector<DocumentVersion> versions;
    vector<Review> reviews;

    set<string> tags;

    chrono::system_clock::time_point updatedAt;
};

struct AuditEvent {
    int id;
    DocumentId documentId;
    UserId actorId;
    string action;
    string details;
};

// ============================================================
// EXCEPTIONS
// ============================================================

class DocumentationException : public runtime_error {
public:
    explicit DocumentationException(const string& message)
        : runtime_error(message) {}
};

class AuthorizationException : public DocumentationException {
public:
    explicit AuthorizationException(const string& message)
        : DocumentationException(message) {}
};

class ValidationException : public DocumentationException {
public:
    explicit ValidationException(const string& message)
        : DocumentationException(message) {}
};

class StateException : public DocumentationException {
public:
    explicit StateException(const string& message)
        : DocumentationException(message) {}
};

class VersionConflictException : public DocumentationException {
public:
    explicit VersionConflictException(const string& message)
        : DocumentationException(message) {}
};

// ============================================================
// VALIDATION UTILITIES
// ============================================================

string trim(const string& value) {
    const auto first = value.find_first_not_of(" \t\n\r");

    if (first == string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(" \t\n\r");

    return value.substr(first, last - first + 1);
}

void validateText(
    const string& value,
    const string& field,
    size_t maximumLength
) {
    if (trim(value).empty()) {
        throw ValidationException(field + " cannot be empty.");
    }

    if (value.size() > maximumLength) {
        throw ValidationException(field + " exceeds its size limit.");
    }
}

bool validEmail(const string& email) {
    const auto at = email.find('@');

    if (at == string::npos || at == 0) {
        return false;
    }

    const auto dot = email.find('.', at + 2);

    return dot != string::npos &&
           dot + 1 < email.size() &&
           email.find(' ') == string::npos;
}

// ============================================================
// CONTENT CHECKSUM
// FNV-1a is used here as a lightweight change-detection
// demonstration. Production integrity requires a
// cryptographic hash such as SHA-256.
// ============================================================

string checksum(const string& content) {
    unsigned long long hash = 14695981039346656037ULL;

    for (unsigned char character : content) {
        hash ^= character;
        hash *= 1099511628211ULL;
    }

    stringstream output;

    output << hex << hash;

    return output.str();
}

// ============================================================
// DOCUMENTATION ENGINE
// ============================================================

class DocumentationEngine {

private:

    unordered_map<UserId, User> users;

    unordered_map<ProjectId, Project> projects;

    unordered_map<DocumentId, ProjectDocument> documents;

    vector<AuditEvent> auditLog;

    UserId nextUserId = 1;
    ProjectId nextProjectId = 1;
    DocumentId nextDocumentId = 1;
    int nextReviewId = 1;
    int nextAuditId = 1;

    // --------------------------------------------------------
    // USER VALIDATION
    // --------------------------------------------------------

    const User& getUser(UserId id) const {

        auto iterator = users.find(id);

        if (iterator == users.end()) {
            throw AuthorizationException("Unknown user.");
        }

        if (!iterator->second.active) {
            throw AuthorizationException("Inactive user.");
        }

        return iterator->second;
    }

    const User& authorize(
        UserId id,
        const set<Role>& allowedRoles
    ) const {

        const User& user = getUser(id);

        if (allowedRoles.find(user.role) == allowedRoles.end()) {
            throw AuthorizationException(
                "User role does not permit this operation."
            );
        }

        return user;
    }

    // --------------------------------------------------------
    // DOCUMENT LOOKUP
    // --------------------------------------------------------

    ProjectDocument& getDocument(DocumentId id) {

        auto iterator = documents.find(id);

        if (iterator == documents.end()) {
            throw DocumentationException("Document not found.");
        }

        return iterator->second;
    }

    const ProjectDocument& getDocument(DocumentId id) const {

        auto iterator = documents.find(id);

        if (iterator == documents.end()) {
            throw DocumentationException("Document not found.");
        }

        return iterator->second;
    }

    // --------------------------------------------------------
    // AUDIT
    // --------------------------------------------------------

    void recordAudit(
        DocumentId documentId,
        UserId actorId,
        const string& action,
        const string& details
    ) {
        auditLog.push_back({
            nextAuditId++,
            documentId,
            actorId,
            action,
            details
        });
    }

    // --------------------------------------------------------
    // STATE MACHINE
    // --------------------------------------------------------

    bool canTransition(
        DocumentStatus current,
        DocumentStatus next
    ) const {

        switch (current) {

            case DocumentStatus::Draft:
                return next == DocumentStatus::UnderReview ||
                       next == DocumentStatus::Archived;

            case DocumentStatus::UnderReview:
                return next == DocumentStatus::Draft ||
                       next == DocumentStatus::Approved ||
                       next == DocumentStatus::Rejected;

            case DocumentStatus::Approved:
                return next == DocumentStatus::Draft ||
                       next == DocumentStatus::Archived;

            case DocumentStatus::Rejected:
                return next == DocumentStatus::Draft ||
                       next == DocumentStatus::Archived;

            case DocumentStatus::Archived:
                return false;
        }

        return false;
    }

    void transition(
        ProjectDocument& document,
        DocumentStatus next
    ) {
        if (!canTransition(document.status, next)) {
            throw StateException(
                "Invalid transition from " +
                toString(document.status) +
                " to " +
                toString(next)
            );
        }

        document.status = next;
        document.updatedAt = chrono::system_clock::now();
    }

public:

    // --------------------------------------------------------
    // USER REGISTRATION
    // --------------------------------------------------------

    UserId registerUser(
        const string& name,
        const string& email,
        Role role
    ) {
        validateText(name, "User name", 200);

        if (!validEmail(email)) {
            throw ValidationException("Invalid email address.");
        }

        for (const auto& entry : users) {
            if (entry.second.email == email) {
                throw ValidationException("Duplicate email.");
            }
        }

        const UserId id = nextUserId++;

        users.emplace(
            id,
            User{id, trim(name), email, role, true}
        );

        return id;
    }

    // --------------------------------------------------------
    // PROJECT CREATION
    // --------------------------------------------------------

    ProjectId createProject(
        UserId actorId,
        const string& name
    ) {
        authorize(
            actorId,
            {Role::Admin, Role::ProjectManager}
        );

        validateText(name, "Project name", 200);

        const ProjectId id = nextProjectId++;

        projects.emplace(id, Project{id, trim(name)});

        return id;
    }

    // --------------------------------------------------------
    // DOCUMENT CREATION
    // --------------------------------------------------------

    DocumentId createDocument(
        UserId actorId,
        ProjectId projectId,
        const string& title,
        DocumentType type,
        const string& content,
        const set<string>& tags = {}
    ) {
        authorize(
            actorId,
            {
                Role::Admin,
                Role::ProjectManager,
                Role::Author
            }
        );

        if (projects.find(projectId) == projects.end()) {
            throw ValidationException("Project does not exist.");
        }

        validateText(title, "Document title", 200);
        validateText(content, "Document content", 5000000);

        for (const auto& tag : tags) {
            validateText(tag, "Tag", 100);
        }

        const DocumentId id = nextDocumentId++;

        DocumentVersion initialVersion{
            1,
            content,
            checksum(content),
            actorId,
            "Initial document creation",
            chrono::system_clock::now()
        };

        ProjectDocument document{
            id,
            projectId,
            trim(title),
            type,
            actorId,
            DocumentStatus::Draft,
            1,
            {initialVersion},
            {},
            tags,
            chrono::system_clock::now()
        };

        documents.emplace(id, move(document));

        recordAudit(
            id,
            actorId,
            "DOCUMENT_CREATED",
            "Version 1"
        );

        return id;
    }

    // --------------------------------------------------------
    // DOCUMENT VERSIONING
    // --------------------------------------------------------

    VersionNumber updateDocument(
        DocumentId documentId,
        UserId actorId,
        const string& content,
        const string& changeDescription,
        VersionNumber expectedVersion
    ) {
        const User& actor = authorize(
            actorId,
            {
                Role::Admin,
                Role::ProjectManager,
                Role::Author
            }
        );

        ProjectDocument& document = getDocument(documentId);

        if (
            actor.role == Role::Author &&
            document.ownerId != actorId
        ) {
            throw AuthorizationException(
                "Author cannot modify another owner's document."
            );
        }

        if (document.status == DocumentStatus::Archived) {
            throw StateException("Archived document is immutable.");
        }

        if (document.currentVersion != expectedVersion) {
            throw VersionConflictException(
                "Document version conflict."
            );
        }

        validateText(content, "Content", 5000000);
        validateText(changeDescription, "Change description", 500);

        const VersionNumber next = document.currentVersion + 1;

        document.versions.push_back({
            next,
            content,
            checksum(content),
            actorId,
            changeDescription,
            chrono::system_clock::now()
        });

        document.currentVersion = next;

        if (
            document.status == DocumentStatus::Approved ||
            document.status == DocumentStatus::Rejected ||
            document.status == DocumentStatus::UnderReview
        ) {
            transition(document, DocumentStatus::Draft);
        }

        document.updatedAt = chrono::system_clock::now();

        recordAudit(
            documentId,
            actorId,
            "VERSION_CREATED",
            "Version " + to_string(next)
        );

        return next;
    }

    // --------------------------------------------------------
    // REVIEW SUBMISSION
    // --------------------------------------------------------

    void submitForReview(
        DocumentId documentId,
        UserId actorId
    ) {
        ProjectDocument& document = getDocument(documentId);

        const User& actor = getUser(actorId);

        if (
            actorId != document.ownerId &&
            actor.role != Role::Admin &&
            actor.role != Role::ProjectManager
        ) {
            throw AuthorizationException(
                "Not authorized to submit this document."
            );
        }

        transition(document, DocumentStatus::UnderReview);

        recordAudit(
            documentId,
            actorId,
            "SUBMITTED_FOR_REVIEW",
            "Current version submitted"
        );
    }

    // --------------------------------------------------------
    // REVIEW DECISION
    // --------------------------------------------------------

    void reviewDocument(
        DocumentId documentId,
        UserId reviewerId,
        ReviewDecision decision,
        const string& comments
    ) {
        const User& reviewer = authorize(
            reviewerId,
            {
                Role::Admin,
                Role::ProjectManager,
                Role::Reviewer
            }
        );

        ProjectDocument& document = getDocument(documentId);

        if (reviewer.id == document.ownerId) {
            throw AuthorizationException(
                "Self-approval is prohibited."
            );
        }

        if (document.status != DocumentStatus::UnderReview) {
            throw StateException(
                "Document is not under review."
            );
        }

        validateText(comments, "Review comments", 5000);

        document.reviews.push_back({
            nextReviewId++,
            reviewerId,
            document.currentVersion,
            decision,
            comments
        });

        switch (decision) {

            case ReviewDecision::Approved:
                transition(document, DocumentStatus::Approved);
                break;

            case ReviewDecision::Rejected:
                transition(document, DocumentStatus::Rejected);
                break;

            case ReviewDecision::ChangesRequested:
                transition(document, DocumentStatus::Draft);
                break;
        }

        recordAudit(
            documentId,
            reviewerId,
            "DOCUMENT_REVIEWED",
            "Version " + to_string(document.currentVersion)
        );
    }

    // --------------------------------------------------------
    // ARCHIVING
    // --------------------------------------------------------

    void archiveDocument(
        DocumentId documentId,
        UserId actorId
    ) {
        authorize(
            actorId,
            {Role::Admin, Role::ProjectManager}
        );

        ProjectDocument& document = getDocument(documentId);

        transition(document, DocumentStatus::Archived);

        recordAudit(
            documentId,
            actorId,
            "DOCUMENT_ARCHIVED",
            "Archived"
        );
    }

    // --------------------------------------------------------
    // SEARCH
    // --------------------------------------------------------

    vector<DocumentId> searchDocuments(
        ProjectId projectId,
        UserId actorId,
        const string& keyword
    ) const {

        getUser(actorId);

        validateText(keyword, "Search keyword", 200);

        string query = keyword;

        transform(
            query.begin(),
            query.end(),
            query.begin(),
            [](unsigned char c) {
                return static_cast<char>(tolower(c));
            }
        );

        vector<DocumentId> results;

        for (const auto& entry : documents) {

            const ProjectDocument& document = entry.second;

            if (document.projectId != projectId) {
                continue;
            }

            string searchable = document.title + " ";

            searchable += document.versions.back().content;

            for (const auto& tag : document.tags) {
                searchable += " " + tag;
            }

            transform(
                searchable.begin(),
                searchable.end(),
                searchable.begin(),
                [](unsigned char c) {
                    return static_cast<char>(tolower(c));
                }
            );

            if (searchable.find(query) != string::npos) {
                results.push_back(document.id);
            }
        }

        sort(results.begin(), results.end());

        return results;
    }

    // --------------------------------------------------------
    // VERSION INTEGRITY
    // --------------------------------------------------------

    bool verifyIntegrity(
        DocumentId documentId,
        UserId actorId
    ) const {

        getUser(actorId);

        const ProjectDocument& document = getDocument(documentId);

        return all_of(
            document.versions.begin(),
            document.versions.end(),
            [](const DocumentVersion& version) {
                return checksum(version.content) == version.checksum;
            }
        );
    }

    // --------------------------------------------------------
    // DOCUMENT RETRIEVAL
    // --------------------------------------------------------

    const ProjectDocument& retrieve(
        DocumentId documentId,
        UserId actorId
    ) const {

        getUser(actorId);

        return getDocument(documentId);
    }

    // --------------------------------------------------------
    // PROJECT REPORTING
    // --------------------------------------------------------

    void printProjectReport(
        ProjectId projectId,
        UserId actorId
    ) const {

        getUser(actorId);

        if (projects.find(projectId) == projects.end()) {
            throw ValidationException("Project not found.");
        }

        map<DocumentStatus, int> statusCounts;

        map<DocumentType, int> typeCounts;

        int totalDocuments = 0;
        int totalVersions = 0;

        for (const auto& entry : documents) {

            const auto& document = entry.second;

            if (document.projectId != projectId) {
                continue;
            }

            ++totalDocuments;

            ++statusCounts[document.status];

            ++typeCounts[document.type];

            totalVersions +=
                static_cast<int>(document.versions.size());
        }

        cout << "\nPROJECT DOCUMENTATION REPORT\n";

        cout << "Project: "
             << projects.at(projectId).name << '\n';

        cout << "Total documents: "
             << totalDocuments << '\n';

        cout << "Total versions: "
             << totalVersions << '\n';

        cout << "\nSTATUS DISTRIBUTION\n";

        for (const auto& entry : statusCounts) {
            cout << toString(entry.first)
                 << ": "
                 << entry.second
                 << '\n';
        }

        cout << "\nDOCUMENT TYPE DISTRIBUTION\n";

        for (const auto& entry : typeCounts) {
            cout << toString(entry.first)
                 << ": "
                 << entry.second
                 << '\n';
        }
    }

    // --------------------------------------------------------
    // AUDIT REPORTING
    // --------------------------------------------------------

    void printAuditHistory(
        DocumentId documentId,
        UserId actorId
    ) const {

        authorize(
            actorId,
            {Role::Admin, Role::ProjectManager}
        );

        getDocument(documentId);

        cout << "\nDOCUMENT AUDIT HISTORY\n";

        for (const auto& event : auditLog) {

            if (event.documentId != documentId) {
                continue;
            }

            cout << event.id
                 << " | "
                 << event.action
                 << " | User "
                 << event.actorId
                 << " | "
                 << event.details
                 << '\n';
        }
    }
};

// ============================================================
// EXECUTABLE SCENARIO
// ============================================================

int main() {

    try {

        DocumentationEngine engine;

        const UserId admin = engine.registerUser(
            "Administrator",
            "admin@example.com",
            Role::Admin
        );

        const UserId author = engine.registerUser(
            "Technical Author",
            "author@example.com",
            Role::Author
        );

        const UserId reviewer = engine.registerUser(
            "Document Reviewer",
            "reviewer@example.com",
            Role::Reviewer
        );

        const ProjectId project = engine.createProject(
            admin,
            "Enterprise Documentation Project"
        );

        const DocumentId document = engine.createDocument(
            author,
            project,
            "System Requirements",
            DocumentType::Requirements,
            "The system must provide secure document storage.",
            {"requirements", "security"}
        );

        cout << "Created document: " << document << '\n';

        const VersionNumber version = engine.updateDocument(
            document,
            author,
            "The system must provide secure storage, " 
            "version history and approval workflows.",
            "Added document governance requirements.",
            1
        );

        cout << "Created version: " << version << '\n';

        engine.submitForReview(document, author);

        engine.reviewDocument(
            document,
            reviewer,
            ReviewDecision::Approved,
            "Requirements reviewed and approved."
        );

        const auto& approved = engine.retrieve(
            document,
            author
        );

        cout << "\nCURRENT DOCUMENT STATE\n";

        cout << "Title: " << approved.title << '\n';

        cout << "Version: " << approved.currentVersion << '\n';

        cout << "Status: " << toString(approved.status) << '\n';

        cout << "Integrity: "
             << (engine.verifyIntegrity(document, author)
                 ? "VALID"
                 : "INVALID")
             << '\n';

        const auto results = engine.searchDocuments(
            project,
            author,
            "secure storage"
        );

        cout << "\nSEARCH MATCHES: "
             << results.size() << '\n';

        engine.printProjectReport(project, admin);

        engine.printAuditHistory(document, admin);

        // Stale version test.
        try {

            engine.updateDocument(
                document,
                author,
                "Outdated content.",
                "Conflict test.",
                1
            );

        } catch (const VersionConflictException& error) {

            cout << "\nEXPECTED VERSION CONFLICT: "
                 << error.what() << '\n';
        }

        // Self-approval test.
        const DocumentId second = engine.createDocument(
            author,
            project,
            "Architecture Design",
            DocumentType::Design,
            "The system uses a modular architecture."
        );

        engine.submitForReview(second, author);

        try {

            engine.reviewDocument(
                second,
                author,
                ReviewDecision::Approved,
                "Attempted self-approval."
            );

        } catch (const AuthorizationException& error) {

            cout << "\nEXPECTED ACCESS DENIAL: "
                 << error.what() << '\n';
        }

        cout << "\nAll C++17 demonstrations completed.\n";

    } catch (const exception& error) {

        cerr << "APPLICATION ERROR: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
