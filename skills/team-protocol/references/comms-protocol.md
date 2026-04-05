# Inter-Agent Communication Protocol

## Overview

Communication flows through two channels:
1. **File-based messaging** — asynchronous, persistent, auditable
2. **Orchestrator routing** — the orchestrator reads outbox files and delivers to inboxes

Agents never write directly to another agent's inbox. All messages go through `outbox/` first,
then the orchestrator routes them.

---

## Message Format

Every message written to `outbox/` must follow this format:

```markdown
---
from: <agent-slug>
to: <agent-slug> | orchestrator | all
priority: low | normal | high | urgent
re: <ticket-id or free-form topic>
timestamp: YYYY-MM-DDTHH:MM
---

## Message

[Message content here]

## Attachments (optional)

- Link to spec: specs/my-spec.md
- Link to decision: decisions/my-decision.md
```

File naming: `outbox/<from>-<to>-<topic>-<timestamp>.md`
Example: `outbox/po-ba-architect-auth-requirements-20240115T1430.md`

---

## Priority Levels

| Priority | Meaning | Orchestrator action |
|---|---|---|
| `low` | FYI, no action needed soon | Deliver at next natural checkpoint |
| `normal` | Standard handoff | Deliver within current session |
| `high` | Blocks or enables another agent | Deliver immediately, ping agent |
| `urgent` | Critical issue, stops the team | Interrupt current work, notify all relevant agents |

---

## Broadcast Messages (`to: all`)

Used for:
- Team-wide decisions (tech stack locked, major scope change)
- Critical bugs that affect everyone
- End-of-sprint summaries

Orchestrator delivers broadcast messages to ALL agent inboxes simultaneously.

---

## Standard Handoff Patterns

### PO/BA → Architect
After requirements are defined:
```
re: T-001 requirements ready
Message: Requirements for [feature] are in specs/feature-x.md.
Please review and propose the architecture. Key constraints: [list].
```

### PO/BA → UI/UX
After user stories are written:
```
re: T-001 design brief
Message: User stories ready in specs/feature-x.md.
Please design the UI. Priority screens: [list]. User persona: [persona].
```

### Architect → Frontend + Backend
After architecture is decided:
```
to: frontend
re: Tech stack decided
Message: Stack is Next.js 14 + TypeScript. Details in decisions/tech-stack.md.
API contracts in specs/api-contracts.md. Please confirm you can start T-002.
```

### UI/UX → Frontend
After design is ready:
```
re: T-001 design handoff
Message: Design spec in specs/feature-x-design.md.
Design tokens in decisions/design-tokens.md.
Key notes: [accessibility requirements, edge states, etc.]
```

### Frontend/Backend → QA
After implementation:
```
re: T-001 ready for QA
Message: Implementation complete. PR branch: feature/T-001.
Endpoints added: POST /api/auth/login, GET /api/auth/me.
Please run full test suite and check acceptance criteria in T-001.
```

### QA → Orchestrator (bug found)
```
to: orchestrator
priority: high
re: B-001 bug in T-001
Message: Found regression in login flow. Created ticket B-001.
Affects: frontend + backend. Needs fix before T-001 can close.
```

---

## Communication Log

The orchestrator appends every routed message to `./project/logs/comms.log`:

```
[2024-01-15T14:30] po-ba → architect | normal | re: T-001 requirements ready
[2024-01-15T15:00] architect → frontend | high | re: Tech stack decided
[2024-01-15T15:01] architect → backend | high | re: Tech stack decided
[2024-01-15T16:20] frontend → qa | normal | re: T-001 ready for QA
[2024-01-15T16:45] qa → orchestrator | high | re: B-001 bug in T-001
```

---

## Orchestrator Routing Algorithm

```
1. Poll ./project/outbox/ for new .md files
2. Parse YAML frontmatter → extract `to` and `priority`
3. If `to` == "all" → append to ALL agent inboxes
4. Else → append to inbox/<to>.md
5. Log the routing event to logs/comms.log
6. If priority == "urgent" → immediately notify affected agents in their Warp tabs
7. If priority == "high" → notify target agent in their Warp tab
8. Archive the processed outbox file to logs/archive/
```
