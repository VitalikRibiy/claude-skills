---
name: agent-roles
version: 1.0.0
description: >
  Contains system prompt templates for all 10 AI dev team agents: Product
  Owner/BA, UI/UX Designer, Software Architect, Frontend Developer, Backend
  Developer, DBA, Security Expert, Code Reviewer, QA Engineer, and DevOps
  Engineer. Each prompt defines the agent's expertise, workspace paths, primary
  documentation responsibilities, role-specific review checklists, and token
  efficiency rules. Includes the self-configuration template agents use to
  write their session rules file on startup. Depends on team-protocol.
depends_on:
  - name: team-protocol
    version: ">=1.0.0"
---

# agent-roles

System prompt templates for every agent in the dev team. The launcher reads
these files, substitutes `{{WORKSPACE_PATH}}`, and passes them to
`claude --system-file`.

---

## Team Roster

| Slug | Role | Prompt file | Spawn when... |
|---|---|---|---|
| `po-ba` | Product Owner / BA | `scripts/po-ba-prompt.md` | Project starts; requirements needed; stories to write |
| `uiux` | UI/UX Designer | `scripts/uiux-prompt.md` | UI design, wireframes, or design tokens needed |
| `architect` | Software Architect | `scripts/architect-prompt.md` | Tech decisions, system design, new service |
| `frontend` | Frontend Developer | `scripts/frontend-prompt.md` | Frontend tickets ready to implement |
| `backend` | Backend Developer | `scripts/backend-prompt.md` | Backend / API tickets ready |
| `dba` | Database Administrator | `scripts/dba-prompt.md` | Schema design, migrations, DB query review |
| `security` | Security Expert | `scripts/security-prompt.md` | Auth/API features; security review gate |
| `reviewer` | Code Reviewer | `scripts/reviewer-prompt.md` | Any code ticket reaches `in-review` |
| `qa` | QA Engineer | `scripts/qa-prompt.md` | Feature implementation complete, tests needed |
| `devops` | DevOps Engineer | `scripts/devops-prompt.md` | Pipelines, deployments, infrastructure tickets |

---

## Agent Self-Configuration

Every agent writes a personal rules file **before any project work**. The
launcher appends this instruction to every prompt automatically:

```
## First Action — Write Your Rules File

Before any project work, write your personal session rules to:
.claude/skills/{slug}-rules.md

Structure:
---
# {role} — Session Rules
_Last updated: <today> | Project: <name>_

## Context Map — Read These First Every Session
- Primary:      {workspace}/docs/<my-domain>/README.md
- Architecture: {workspace}/docs/architecture/README.md

## Feature Heatmap
| Feature / Area | Heat | Last ticket | Notes |
|---|---|---|---|
| [populate from tickets/ and codebase] | 🔥 | | |

## Project Conventions
- Stack: [from docs/architecture/README.md]
- Patterns to follow: [from decisions/]
- Anti-patterns: [from decisions/ or team guidance]

## My Checklist (every task)
- [ ] Read relevant docs/ before starting
- [ ] Check decisions/ for prior art
- [ ] Update docs/ and heatmap after finishing

## Token Savers
- Always check docs/ before reading source files
- My most-needed files: [list 3-5 specific paths]
---
Update this file after every task — keep the heatmap current.
```

### Role-Specific Heatmap Focus

| Agent | Heatmap tracks... |
|---|---|
| po-ba | Epics and features by business value / risk |
| architect | Modules/services by complexity and coupling |
| frontend | UI areas by component count and change frequency |
| backend | API domains by endpoint count and business criticality |
| dba | Tables by row count estimate and query complexity |
| security | Surface areas by exposure risk |
| reviewer | Files by violation frequency and complexity |
| qa | Features by test coverage (🔥 = low coverage = highest priority) |
| devops | Environments and pipelines by fragility and change frequency |
| uiux | Screens/flows by design debt and user impact |

---

## Reference Files

- `references/agent-prompts.md` — all 10 prompts combined in one reference document
- `scripts/` — individual prompt files, one per agent (used by the launcher)
