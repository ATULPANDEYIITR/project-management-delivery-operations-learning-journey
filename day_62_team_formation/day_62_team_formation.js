'use strict';

const { EventEmitter } = require('node:events');

const Role = Object.freeze({
    PRODUCT_MANAGER: 'Product Manager',
    TECH_LEAD: 'Technical Lead',
    BACKEND: 'Backend Engineer',
    FRONTEND: 'Frontend Engineer',
    QA: 'QA Engineer',
    DEVOPS: 'DevOps Engineer',
    DATA: 'Data Engineer',
    SECURITY: 'Security Engineer',
    UX: 'UX Designer'
});

const Availability = Object.freeze({
    AVAILABLE: 'available',
    PARTIAL: 'partial',
    UNAVAILABLE: 'unavailable'
});

class FormationError extends Error {}

class Candidate {
    constructor({ id, name, skills, roles, experience, availability }) {
        if (!id || !name) throw new FormationError('Candidate requires an id and name.');
        if (!Number.isFinite(experience) || experience < 0) {
            throw new FormationError(`Invalid experience for ${id}.`);
        }

        this.id = id;
        this.name = name;
        this.skills = new Set(skills);
        this.roles = new Set(roles);
        this.experience = experience;
        this.availability = availability;
    }
}

class Project {
    constructor({
        id,
        name,
        requiredSkills,
        requiredRoles,
        minTeamSize,
        maxTeamSize,
        risk = 'medium'
    }) {
        if (minTeamSize < 1 || maxTeamSize < minTeamSize) {
            throw new FormationError('Invalid team-size policy.');
        }

        this.id = id;
        this.name = name;
        this.requiredSkills = new Set(requiredSkills);
        this.requiredRoles = new Set(requiredRoles);
        this.minTeamSize = minTeamSize;
        this.maxTeamSize = maxTeamSize;
        this.risk = risk;
    }
}

class TeamFormationEngine extends EventEmitter {
    constructor(candidates) {
        super();

        const ids = new Set();
        for (const candidate of candidates) {
            if (ids.has(candidate.id)) {
                throw new FormationError(`Duplicate candidate: ${candidate.id}`);
            }
            ids.add(candidate.id);
        }

        this.candidates = candidates;
    }

    score(candidate, project) {
        const skillMatches = [...candidate.skills]
            .filter(skill => project.requiredSkills.has(skill)).length;

        const roleMatches = [...candidate.roles]
            .filter(role => project.requiredRoles.has(role)).length;

        const availabilityScore = {
            [Availability.AVAILABLE]: 3,
            [Availability.PARTIAL]: 1,
            [Availability.UNAVAILABLE]: -100
        }[candidate.availability];

        return skillMatches * 4 +
            roleMatches * 6 +
            Math.min(candidate.experience, 10) * 0.25 +
            availabilityScore;
    }

    rank(project) {
        return this.candidates
            .filter(candidate => candidate.availability !== Availability.UNAVAILABLE)
            .toSorted((a, b) => this.score(b, project) - this.score(a, project));
    }

    missingRoles(team, project) {
        const roles = new Set(team.flatMap(candidate => [...candidate.roles]));
        return [...project.requiredRoles].filter(role => !roles.has(role));
    }

    missingSkills(team, project) {
        const skills = new Set(team.flatMap(candidate => [...candidate.skills]));
        return [...project.requiredSkills].filter(skill => !skills.has(skill));
    }

    async formTeam(project) {
        const team = [];
        const selected = new Set();
        const ranked = this.rank(project);

        const selectCandidate = candidate => {
            if (!candidate || selected.has(candidate.id)) return false;
            team.push(candidate);
            selected.add(candidate.id);

            this.emit('memberSelected', {
                project: project.name,
                candidate: candidate.name
            });
            return true;
        };

        // Required roles are handled before general capacity filling.
        for (const role of project.requiredRoles) {
            const candidate = ranked.find(
                person => person.roles.has(role) && !selected.has(person.id)
            );

            if (!candidate) {
                throw new FormationError(`No eligible candidate for ${role}.`);
            }

            selectCandidate(candidate);
            await Promise.resolve();
        }

        while (team.length < project.minTeamSize) {
            const missingSkills = new Set(this.missingSkills(team, project));

            const candidates = ranked.filter(person => !selected.has(person.id));
            if (!candidates.length) {
                throw new FormationError('Insufficient candidates for minimum team size.');
            }

            const best = candidates.toSorted((a, b) => {
                const score = person =>
                    [...person.skills].filter(skill => missingSkills.has(skill)).length * 5 +
                    [...person.roles].filter(role => project.requiredRoles.has(role)).length * 2 +
                    person.experience;

                return score(b) - score(a);
            })[0];

            selectCandidate(best);
            await Promise.resolve();
        }

        // Optional capacity is used only when it adds uncovered project skills.
        while (team.length < project.maxTeamSize) {
            const before = this.missingSkills(team, project).length;
            const candidate = ranked
                .filter(person => !selected.has(person.id))
                .find(person =>
                    [...person.skills].some(skill => project.requiredSkills.has(skill))
                );

            if (!candidate) break;

            selectCandidate(candidate);

            const after = this.missingSkills(team, project).length;
            if (after >= before) {
                team.pop();
                selected.delete(candidate.id);
                break;
            }
        }

        const validation = this.validate(team, project);

        if (!validation.valid) {
            throw new FormationError(validation.errors.join('; '));
        }

        this.emit('teamFormed', {
            project: project.name,
            members: team.length
        });

        return team;
    }

    validate(team, project) {
        const errors = [];
        const ids = new Set();

        for (const member of team) {
            if (ids.has(member.id)) errors.push(`Duplicate member ${member.id}.`);
            ids.add(member.id);
        }

        if (team.length < project.minTeamSize) {
            errors.push('Team is below the minimum size.');
        }

        if (team.length > project.maxTeamSize) {
            errors.push('Team exceeds the maximum size.');
        }

        const missingRoles = this.missingRoles(team, project);
        const missingSkills = this.missingSkills(team, project);

        if (missingRoles.length) {
            errors.push(`Missing roles: ${missingRoles.join(', ')}`);
        }

        if (missingSkills.length) {
            errors.push(`Missing skills: ${missingSkills.join(', ')}`);
        }

        return {
            valid: errors.length === 0,
            errors,
            missingRoles,
            missingSkills
        };
    }
}

async function main() {
    const candidates = [
        new Candidate({
            id: 'C001',
            name: 'Aarav',
            skills: ['roadmapping', 'stakeholder-management', 'analytics'],
            roles: [Role.PRODUCT_MANAGER],
            experience: 7,
            availability: Availability.AVAILABLE
        }),
        new Candidate({
            id: 'C002',
            name: 'Meera',
            skills: ['architecture', 'python', 'postgresql', 'security'],
            roles: [Role.TECH_LEAD, Role.BACKEND],
            experience: 9,
            availability: Availability.AVAILABLE
        }),
        new Candidate({
            id: 'C003',
            name: 'Kabir',
            skills: ['python', 'fastapi', 'postgresql', 'testing'],
            roles: [Role.BACKEND],
            experience: 5,
            availability: Availability.AVAILABLE
        }),
        new Candidate({
            id: 'C004',
            name: 'Diya',
            skills: ['javascript', 'react', 'accessibility', 'css'],
            roles: [Role.FRONTEND, Role.UX],
            experience: 4,
            availability: Availability.AVAILABLE
        }),
        new Candidate({
            id: 'C005',
            name: 'Rohan',
            skills: ['pytest', 'automation', 'testing', 'quality'],
            roles: [Role.QA],
            experience: 6,
            availability: Availability.AVAILABLE
        }),
        new Candidate({
            id: 'C006',
            name: 'Ishita',
            skills: ['docker', 'kubernetes', 'ci-cd', 'linux'],
            roles: [Role.DEVOPS],
            experience: 6,
            availability: Availability.PARTIAL
        }),
        new Candidate({
            id: 'C008',
            name: 'Nisha',
            skills: ['threat-modeling', 'security', 'iam', 'python'],
            roles: [Role.SECURITY],
            experience: 7,
            availability: Availability.AVAILABLE
        })
    ];

    const project = new Project({
        id: 'P001',
        name: 'Secure Operations Analytics Platform',
        requiredSkills: [
            'roadmapping',
            'architecture',
            'python',
            'postgresql',
            'javascript',
            'testing',
            'docker',
            'security'
        ],
        requiredRoles: [
            Role.PRODUCT_MANAGER,
            Role.TECH_LEAD,
            Role.BACKEND,
            Role.FRONTEND,
            Role.QA,
            Role.DEVOPS,
            Role.SECURITY
        ],
        minTeamSize: 7,
        maxTeamSize: 8,
        risk: 'high'
    });

    const engine = new TeamFormationEngine(candidates);

    engine.on('memberSelected', event => {
        console.log(`Selected ${event.candidate} for ${event.project}`);
    });

    engine.on('teamFormed', event => {
        console.log(`Team formed for ${event.project}: ${event.members} members`);
    });

    const team = await engine.formTeam(project);
    const validation = engine.validate(team, project);

    console.log('\nFinal team:');
    console.table(team.map(member => ({
        ID: member.id,
        Name: member.name,
        Roles: [...member.roles].join(', '),
        Availability: member.availability
    })));

    console.log('\nValidation:');
    console.log(JSON.stringify(validation, null, 2));
}

main().catch(error => {
    console.error(`Team formation failed: ${error.message}`);
    process.exitCode = 1;
});
