---
name: project-workspace
version: 1.0.0
description: >
  Initializes and maintains the shared project workspace for the AI dev team.
  Creates the directory structure (inbox, outbox, decisions, specs, tickets,
  logs, docs with six domain subdirectories), seeds stub documentation files
  owned by each agent role, and writes the project README with token efficiency
  rules and workspace conventions. Run this skill before spawning any agents.
  Works standalone with no dependencies on other skills.
depends_on: []
---

# project-workspace

Manages the shared filesystem workspace that all 10 dev-team agents read and
write during a session.

---

## When to Run

Run `scripts/workspace_init.py` once per project before spawning any agents.
It is idempotent — re-running it on an existing workspace only creates missing
files and directories; it never overwrites existing content.

```bash
python3 skills/project-workspace/scripts/workspace_init.py --workspace ./project
```

Or with an explicit path:

```bash
python3 skills/project-workspace/scripts/workspace_init.py \
    --workspace /path/to/my-project/project
```

---

## Directory Structure Created

```
./project/
├── inbox/                    ← messages TO each agent  (<slug>.md)
├── outbox/                   ← messages FROM agents    (routed by orchestrator)
├── decisions/                ← finalized team decisions (immutable once signed)
├── specs/
│   └── test-plans/           ← QA test plans per feature
├── tickets/                  ← task tickets (<id>-<slug>.md)
├── logs/
│   └── archive/              ← processed outbox files moved here
├── docs/
│   ├── architecture/         ← owned by Architect
│   ├── business-logic/       ← owned by PO/BA
│   ├── api/                  ← owned by Backend
│   ├── database/             ← owned by DBA
│   ├── security/             ← owned by Security Expert
│   └── devops/               ← owned by DevOps Engineer
└── README.md                 ← workspace conventions (written on first init)

../.claude/skills/            ← each agent's personal session rules file
```

---

## Stub Documentation Files

The init script seeds these files **only if they do not already exist**:

| File | Owner agent | Initial content |
|---|---|---|
| `docs/architecture/README.md` | architect | `# Architecture Map\n\n_Populated by Architect._` |
| `docs/business-logic/README.md` | po-ba | `# Business Logic\n\n_Populated by PO/BA._` |
| `docs/api/README.md` | backend | `# API Reference\n\n_Populated by Backend._` |
| `docs/database/README.md` | dba | `# Database Schema\n\n_Populated by DBA._` |
| `docs/security/README.md` | security | `# Security Notes\n\n_Populated by Security._` |
| `docs/devops/README.md` | devops | `# DevOps & Deployment\n\n_Populated by DevOps._` |

---

## Workspace README

`./project/README.md` is written on first init with:

- Token Efficiency Rules (all agents must follow)
- Directory structure reference
- Workspace conventions (message format, ticket format, decision format)

---

## Token Efficiency Rules (ALL AGENTS MUST FOLLOW)

These are written into `./project/README.md` and must be respected by every agent:

1. Read `docs/` before exploring the codebase or asking questions
2. Update `docs/` after every significant change
3. One concern per file — keep files under ~200 lines
4. DRY: extract shared logic, never duplicate
5. KISS: simplest solution that satisfies the requirement
6. On startup: write/update your rules in `.claude/skills/<slug>-rules.md`

---

## Existing Project Analysis Support

When resuming an existing project, the orchestrator pre-populates docs before
spawning agents. The init script preserves any existing files — it only fills
gaps. Pre-population writes to:

- `docs/architecture/README.md` — detected tech stack + folder map
- `docs/api/README.md` — routes found in the codebase
- `docs/devops/README.md` — pipeline/infra files found

An `existing-project.md` briefing is written to `./project/docs/`:

```markdown
# Existing Project Briefing

## Detected Tech Stack
- Frontend: [e.g. Next.js 14 + TypeScript]
- Backend: [e.g. Node.js + Fastify]
- Database: [e.g. PostgreSQL]
- Infra: [e.g. Docker + Azure]
- CI/CD: [e.g. GitHub Actions]

## Folder Structure (top 2 levels)
[tree output]

## Prior Workspace State
[fresh | resuming — list open tickets and last known state]

## Pre-populated Docs
[list which docs/ files were pre-filled from codebase analysis]

## Open Questions for the Team
[ambiguities found during analysis]
```

---

## Script Reference

`scripts/workspace_init.py` — see that file for the full implementation.

Functions exported:
- `init_workspace(workspace: str)` — creates dirs and stubs
- `seed_po_ba_inbox(workspace: str, ado_org: str = None)` — writes initial PO/BA inbox message
