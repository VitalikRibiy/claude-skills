---
name: lessons-learned
version: 1.1.0
description: >
  Cross-project knowledge store for agent lessons learned. All lessons from
  all agents and all projects live in one shared file: ~/.claude/lessons.md.
  Injected into every agent's system prompt at launch so past mistakes are
  never repeated. Agents append new lessons when a reviewer flags the same
  issue twice. Includes a CLI for manual management.
depends_on: []
---

# lessons-learned

A single shared file that captures recurring mistakes and proven patterns
across all projects and all agent roles. Every agent reads it at the start
of each session and appends to it when a pattern recurs.

---

## Storage

One file, fixed location:

```
~/.claude/lessons.md
```

All agents, all projects, all roles write to and read from the same file.

---

## Lesson Format

```markdown
# Lessons Learned

- [2024-03-01] [frontend] **React key prop**: mapped elements missing `key` → always `key={item.id}`
- [2024-03-05] [dba] **N+1 queries**: ORM findAll inside loop → use include or batch load
- [2024-03-10] [global] **No .env commits**: never commit .env → use .env.example with placeholders
```

Tags: `[agent-slug]` for role-specific lessons, `[global]` for cross-cutting patterns.

---

## CLI Usage

```bash
# List all lessons
python3 skills/lessons-learned/scripts/lessons_manager.py list

# List lessons for one agent
python3 skills/lessons-learned/scripts/lessons_manager.py list --agent frontend

# Add a lesson manually
python3 skills/lessons-learned/scripts/lessons_manager.py add \
    --agent frontend \
    "React key prop: mapped elements missing key → always key={item.id}"

# Add a global lesson (applies to all roles)
python3 skills/lessons-learned/scripts/lessons_manager.py add \
    --agent global \
    "Never commit .env — use .env.example with placeholder values"

# Clear all lessons
python3 skills/lessons-learned/scripts/lessons_manager.py clear
```

---

## Integration with agent-launcher

Lessons are injected automatically — no extra flags needed:

```bash
python3 skills/agent-launcher/scripts/launch_team.py --all --workspace ./project
```

To skip lessons injection:

```bash
python3 skills/agent-launcher/scripts/launch_team.py --all --workspace ./project --no-lessons
```

At launch, the full contents of `~/.claude/lessons.md` are appended to every
agent's system prompt under a `## Lessons from Past Projects` section.
The section also tells agents the file path so they can append new lessons.

---

## When Agents Write Lessons

Agents are instructed to append a new lesson when:
- A reviewer flags the **same issue** in two or more tickets in the current session
- The agent catches itself about to repeat a mistake it has seen before

The agent appends directly to `~/.claude/lessons.md` using the Write/Edit tool.
