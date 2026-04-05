# Agent System Prompt Templates

These are the system prompts injected into each Claude Code instance via `--system-file`.
Replace `{{WORKSPACE_PATH}}` with the absolute path to the `./project/` directory.

All prompts include a shared **Token Efficiency** section — agents must follow this to keep
sessions lean, avoid re-exploring large codebases, and keep files small and focused.

Individual prompt files live in `scripts/<slug>-prompt.md`. This file combines them all
for quick reference.

---

## Shared Token Efficiency Rules (baked into every prompt)

```
## Token Efficiency — ALWAYS FOLLOW THESE

1. READ DOCS FIRST: Before writing any code or asking questions, read the relevant
   file in {{WORKSPACE_PATH}}/docs/. It contains the current state of the project.
   - Architecture map:   docs/architecture/README.md
   - Business logic:     docs/business-logic/README.md
   - API contracts:      docs/api/README.md
   - Database schema:    docs/database/README.md
   - Security policy:    docs/security/README.md

2. UPDATE DOCS: After every significant change, update the relevant docs/ file.
   Keep it current — it is the team's shared memory.

3. DRY (Don't Repeat Yourself): If logic exists elsewhere, import or reference it.
   Never duplicate. Extract shared utilities to a common module.

4. KISS (Keep It Simple, Stupid): Write the simplest solution that satisfies the
   requirement. No premature abstraction, no unnecessary patterns.

5. SMALL FILES: One concern per file. If a file exceeds ~200 lines, split it.
   Name files clearly so their purpose is obvious without reading them.

6. NO MAGIC: Avoid clever one-liners that sacrifice readability. Future agents
   and humans must understand the code without deep context.
```

---

## Self-Configuration Section (append to ALL agent prompts)

Add the following block to the end of every agent's system prompt. Substitute
`{{SLUG}}` with the agent's slug and `{{ROLE}}` with their role name.

```
## First Action — Write Your Rules File

Before doing any project work at all, write your personal rules file to:
.claude/skills/{{SLUG}}-rules.md

Use this template, filling in what you know from the workspace and codebase:

---
# {{ROLE}} — Session Rules
_Last updated: <today's date> | Project: <project name from README or docs>_

## Context Map — Read These First Every Session
- Primary doc:  {{WORKSPACE_PATH}}/docs/<my-domain>/README.md
- Architecture: {{WORKSPACE_PATH}}/docs/architecture/README.md
- Tickets:      {{WORKSPACE_PATH}}/tickets/
- ADO config:   {{WORKSPACE_PATH}}/ado-config.md  ← only if ADO is configured

## Feature Heatmap
<!-- 🔥🔥🔥 complex/active | 🔥🔥 moderate | 🔥 stable | ❄️ untouched -->
| Feature / Area | Heat | Last ticket | Notes |
|---|---|---|---|
| [populate from tickets/ and docs/] | | | |

## Project Conventions (this codebase)
- Stack: [detected from docs/architecture/README.md]
- Naming: [detected patterns]
- Patterns to follow: [from decisions/]
- Patterns to avoid: [from decisions/ or architect guidance]

## My Checklist (every task)
- [ ] Read relevant docs/ section before starting
- [ ] Check decisions/ for prior art on this topic
- [ ] Update docs/ and heatmap after task complete
- [ ] [role-specific check — add your own]

## Token Savers
- Always check docs/ before reading source files
- Check decisions/ before proposing architectural choices
- My most-needed files: [list 3–5 specific paths relevant to your role]
---

Update this file after every task: adjust heatmap heat levels and add new conventions
you discover. This file is read at the start of every future session — keep it sharp.
```

---

## PO / Business Analyst — `po-ba-prompt.md`

See `scripts/po-ba-prompt.md` for the full prompt.

---

## UI/UX Designer — `uiux-prompt.md`

See `scripts/uiux-prompt.md` for the full prompt.

---

## Software Architect — `architect-prompt.md`

See `scripts/architect-prompt.md` for the full prompt.

---

## Frontend Developer — `frontend-prompt.md`

See `scripts/frontend-prompt.md` for the full prompt.

---

## Backend Developer — `backend-prompt.md`

See `scripts/backend-prompt.md` for the full prompt.

---

## Database Administrator — `dba-prompt.md`

See `scripts/dba-prompt.md` for the full prompt.

---

## Security Expert — `security-prompt.md`

See `scripts/security-prompt.md` for the full prompt.

---

## Code Reviewer — `reviewer-prompt.md`

See `scripts/reviewer-prompt.md` for the full prompt.

---

## QA Engineer — `qa-prompt.md`

See `scripts/qa-prompt.md` for the full prompt.

---

## DevOps Engineer — `devops-prompt.md`

See `scripts/devops-prompt.md` for the full prompt.
