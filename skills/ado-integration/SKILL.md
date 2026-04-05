---
name: ado-integration
version: 1.0.0
description: >
  Sets up and documents Azure DevOps MCP integration for the AI dev team.
  Provides an interactive setup script that checks Node.js 20+ and Azure CLI
  prerequisites, runs az login, gathers org/project/repo/wiki details, and
  writes .claude/mcp.json and project/ado-config.md. Contains the ADO addendum
  appended to every agent prompt when ADO is enabled, and a per-agent ADO
  operation reference covering work items, wiki, PRs, pipelines, and test
  plans. Run setup once per project. Depends on team-protocol.
depends_on:
  - name: team-protocol
    version: ">=1.0.0"
---

# ado-integration

Connects the dev team workspace to Azure DevOps via the local MCP server
(`@azure-devops/mcp`). Covers setup, per-agent usage, and troubleshooting.

---

## Setup

Run the interactive setup script once per project:

```bash
python3 skills/ado-integration/scripts/ado-mcp-setup.py
```

Or non-interactively:

```bash
python3 skills/ado-integration/scripts/ado-mcp-setup.py \
    --org contoso --project MyProject --repo my-repo --yes
```

The script runs these phases in order:

1. **Prerequisites** — checks Node.js 20+ and Azure CLI are installed
2. **Authentication** — runs `az login` if not already signed in
3. **Configuration** — prompts for org, project, repo, and wiki names
4. **File writes** — creates `.claude/mcp.json` and `project/ado-config.md`
5. **Verification** — confirms the MCP package is accessible via npx

### Files Written

**`.claude/mcp.json`** — auto-loaded by Claude Code, starts the MCP server:

```json
{
  "servers": {
    "azure-devops": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "<ORG>",
               "-d", "core", "work", "work-items",
               "repositories", "wiki", "pipelines", "test-plans"]
    }
  }
}
```

**`project/ado-config.md`** — read by every agent before ADO operations:
```markdown
# Azure DevOps Config
- Organization: <org>
- Project: <project>
- Repo: <repo>
- Default branch: main
- Wiki: <project>.wiki
- ADO URL: https://dev.azure.com/<org>
```

---

## ADO MCP Domain Reference

Only load the domains you need (each domain adds tools to the context):

| Domain | What it unlocks |
|---|---|
| `core` | Projects, teams, iterations — always include |
| `work` | Sprint boards, backlogs, capacity |
| `work-items` | Create/read/update/delete work items |
| `repositories` | Repos, branches, commits, pull requests |
| `wiki` | Wiki pages: create, read, update |
| `builds` | Pipelines, build definitions, queue builds |
| `test-plans` | Test plans, suites, test cases, results |

---

## ADO Agent Addendum

When ADO is enabled, `scripts/ado-addendum.md` is appended to every agent
prompt at spawn time. It tells agents:

- Where to read `ado-config.md` before any ADO operation
- Role-specific ADO responsibilities (work items, wiki pages, PRs, test plans)
- General rules (no secrets committed, feature branches only, PR naming convention)

Full content: `scripts/ado-addendum.md`

---

## Per-Agent ADO Operations

Full reference: `references/azure-devops.md`

Quick summary by role:

| Agent | ADO Responsibility |
|---|---|
| po-ba | Create/update Work Items; set iteration paths; record `ado_work_item_id` in ticket |
| uiux | Create wiki pages at `/design/<screen-name>` |
| architect | Create ADR wiki pages at `/architecture/decisions/<name>` |
| frontend | Push code, open PRs named `T-XXX: <desc>`, link PRs to work items |
| backend | Same as frontend; also update `/docs/api` wiki after endpoint changes |
| dba | Update `/docs/database` wiki after schema changes; review DB-related PRs |
| security | Update `/docs/security` wiki; post findings as PR comments |
| reviewer | Read PR diffs via ADO; post all findings as PR comments; approve/reject |
| qa | Create Test Plans, Suites, and Test Cases; record results; create Bug work items |
| devops | Queue pipeline builds; monitor deployments; update `/docs/devops` wiki |

---

## ADO Sync Table (orchestrator manages this)

| Local event | ADO action |
|---|---|
| Ticket created | Create Work Item → record ID in ticket frontmatter |
| Ticket `in-review` | Create PR linked to Work Item |
| QA test plan written | Create Test Plan + Suite in ADO |
| Ticket `done` | Close Work Item, link PR, update Wiki |
| Decision written | Mirror to ADO Wiki `/decisions/<topic>` |
| `docs/` updated | Mirror to ADO Wiki `/docs/<domain>` |
| `[DEVOPS]` ticket done | DevOps triggers ADO Pipeline run |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `az login` not found | Install Azure CLI (`winget install Microsoft.AzureCLI` / `brew install azure-cli`) |
| "Permission denied" on tool call | ADO Basic license or higher required |
| MCP server not starting | Run `npx @azure-devops/mcp <org>` manually to see errors |
| Auth token expired | Run `az login` again; tokens expire after ~1 hour |
| Organization not found | Verify org name in `ado-config.md` — no trailing slashes |
| Personal MSA account | ADO MCP requires Entra-backed org; personal MSA not supported |

---

## Reference Files

- `scripts/ado-mcp-setup.py` — interactive cross-platform setup script
- `scripts/ado-addendum.md` — ADO instructions appended to every agent prompt
- `references/azure-devops.md` — complete per-agent ADO operation reference and wiki conventions
