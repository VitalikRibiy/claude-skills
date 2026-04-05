# Ticket Schema & Lifecycle

## Ticket File Format

Tickets live in `./project/tickets/<id>-<slug>.md`.

```markdown
---
id: T-001
title: Implement user login screen
type: feature | bug | chore | spike
status: open | in-progress | blocked | in-review | done | cancelled
priority: critical | high | medium | low
assigned_to: po-ba | uiux | architect | frontend | backend | qa
created_by: <agent-slug>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
depends_on: [T-000]
blocks: [T-002, T-003]
sprint: 1
story_points: 3
ado_work_item_id: 42        # filled by PO/BA after creating in ADO (if ADO enabled)
ado_pr_id: 7                # filled by developer after opening PR in ADO
ado_test_plan_id: 3         # filled by QA after creating test plan in ADO
---

## Description

What needs to be done and why.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All relevant tests pass (QA sign-off required)

## Notes / Context

Design spec: specs/login-screen.md
Architecture decision: decisions/auth-strategy.md

## Activity Log

- 2024-01-15 | po-ba | Created ticket
- 2024-01-15 | architect | Added technical notes
- 2024-01-16 | frontend | Started implementation
- 2024-01-17 | qa | Tests written, all passing ✅
```

---

## Status Lifecycle

```
open → in-progress → in-review → done
         ↓                ↓
       blocked          (qa raises bug)
         ↓                ↓
       (unblocked)    → open (re-opened)
```

### Status Definitions

| Status | Meaning |
|---|---|
| `open` | Created, not yet started |
| `in-progress` | Assigned agent is actively working on it |
| `blocked` | Waiting on another ticket, decision, or clarification |
| `in-review` | Work complete, awaiting QA or peer review |
| `done` | Accepted by QA and orchestrator |
| `cancelled` | No longer needed (note reason in activity log) |

---

## Ticket Types

| Type | Description |
|---|---|
| `feature` | New user-facing functionality |
| `bug` | Something broken, discovered by QA or user |
| `chore` | Technical debt, refactor, config, infra |
| `spike` | Research/exploration with a time-box |

---

## ID Scheme

- Regular tickets: `T-001`, `T-002`, ...
- Bugs raised by QA: `B-001`, `B-002`, ...
- Spikes: `S-001`, `S-002`, ...

The orchestrator assigns IDs in sequence. Agents never self-assign IDs.

---

## Orchestrator Ticket Automation Rules

1. **Ticket created** → assign ID, write to `tickets/`, notify assigned agent's inbox
2. **Status → in-review** → notify QA inbox automatically
3. **QA raises bug** → create `B-XXX` ticket, re-open parent ticket, notify responsible agent
4. **Status → done** → update decision log if relevant, notify orchestrator summary
5. **Blocked** → escalate to orchestrator, attempt to identify blocker owner and notify them
