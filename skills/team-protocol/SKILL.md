---
name: team-protocol
version: 1.0.0
description: >
  Defines the inter-agent communication protocol and ticket schema for the AI
  dev team. Specifies the outbox message format (YAML frontmatter with from,
  to, priority, re, timestamp fields), priority levels, broadcast message
  handling, standard handoff patterns between roles, the orchestrator routing
  algorithm, the full ticket schema (frontmatter fields, status lifecycle,
  ticket types, ID scheme), and orchestrator ticket automation rules.
  Foundation skill with no dependencies on other skills.
depends_on: []
---

# team-protocol

Defines how agents communicate and how work is tracked. Every agent and the
orchestrator must follow these conventions — they are the shared contract that
makes async, file-based coordination reliable.

---

## Communication Protocol

Full specification: `references/comms-protocol.md`

Key rules:
- Agents **never** write directly to another agent's inbox
- All outbound messages go to `outbox/<from>-<to>-<topic>-<timestamp>.md`
- The orchestrator reads `outbox/` and routes to `inbox/<slug>.md`
- Every message must include YAML frontmatter with `from`, `to`, `priority`, `re`, `timestamp`

Priority levels: `low` | `normal` | `high` | `urgent`

Broadcast messages (`to: all`) are delivered to every agent inbox simultaneously.

---

## Ticket Schema

Full specification: `references/ticket-schema.md`

Tickets live in `./project/tickets/<id>-<slug>.md` with YAML frontmatter.

Required frontmatter fields: `id`, `title`, `type`, `status`, `priority`,
`assigned_to`, `created_by`, `created_at`, `updated_at`

Optional ADO fields (filled when ADO integration is active):
`ado_work_item_id`, `ado_pr_id`, `ado_test_plan_id`

Status lifecycle: `open → in-progress → in-review → done`
(with `blocked` and `cancelled` as side states)

ID scheme: `T-NNN` (tasks), `B-NNN` (bugs), `S-NNN` (spikes) — assigned by orchestrator only.

---

## Reference Files

- `references/comms-protocol.md` — complete message format, routing algorithm, handoff patterns
- `references/ticket-schema.md` — full ticket format, status definitions, automation rules
