# Claude Skills — AI Dev Team Orchestration

Spin up a 10-role AI software development team inside Claude Code. One command assembles a Product Owner, Architect, Frontend/Backend developers, DBA, Security Expert, Code Reviewer, QA Engineer, and DevOps Engineer — each running as a separate Claude Code instance in its own terminal window, communicating through a shared workspace.

---

## Quick Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/VitalikRibiy/claude-skills/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/VitalikRibiy/claude-skills/main/install.ps1 | iex
```

Both scripts clone the repo, install Python dependencies, and install the full skill set automatically. When done, open Claude Code in any project directory and say **"Avengers assemble"**.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| [Claude Code](https://claude.ai/code) | Latest | CLI must be installed and authenticated |
| Python | 3.10+ | For skillman and build scripts |
| Git | Any | For cloning and updates |

---

## Usage

Open Claude Code in your project directory and say:

> **"Avengers assemble"**

The orchestrator runs a short intake interview, then initializes the workspace and spawns agents on demand as work progresses.

### Intake Interview

**Q1 — New or existing project?**
For existing codebases the orchestrator scans your repo, detects your tech stack, and pre-populates documentation before any agents start.

**Q2 — Azure DevOps?** *(optional)*
If you use Azure DevOps you'll be asked for your org name, project name, and repo name. The setup script handles authentication and MCP configuration automatically. Skip this if you don't use ADO.

### What Happens After Intake

```
po-ba      → writes requirements and user stories first
architect  → defines tech stack and system design
uiux       → wireframes and design specs (when UI work is scoped)
dba        → schema design and migrations (when data model is needed)
backend    → API implementation
devops     → CI/CD and infrastructure
frontend   → UI implementation
security   → reviews all [SECURITY]-tagged tickets
reviewer   → reviews every code ticket before it reaches QA
qa         → end-to-end and API tests
```

Agents communicate through a shared `./project/` workspace. The orchestrator routes messages, manages the ticket lifecycle, and enforces review gates automatically. Agents are spawned **on demand** — only when there is actual work for them.

---

## The Team

| Agent | Role | Speciality |
|---|---|---|
| `po-ba` | Product Owner / BA | Requirements, user stories, acceptance criteria |
| `architect` | Software Architect | System design, ADRs, tech stack decisions |
| `uiux` | UI/UX Designer | Wireframes, design tokens, accessibility |
| `frontend` | Frontend Developer | React/Next.js/Vue, TypeScript, components |
| `backend` | Backend Developer | APIs, auth, queues, database access |
| `dba` | Database Administrator | Schema design, migrations, query optimization |
| `security` | Security Expert | OWASP, auth flows, secrets management |
| `reviewer` | Code Reviewer | DRY, KISS, SOLID, architecture alignment |
| `qa` | QA Engineer | Playwright E2E, API tests, bug reports |
| `devops` | DevOps Engineer | CI/CD pipelines, containers, cloud infra |

### Review Gates

Every ticket goes through mandatory review before reaching QA:

| Tag | Reviewer |
|---|---|
| Any code ticket | `reviewer` (always) |
| `[DB]` | `dba` |
| `[SECURITY]` | `security` |
| `[DEVOPS]` or `[INFRA]` | `devops` |

---

## Skills

The system is composed of independently installable skills with explicit dependency management.

| Skill | Description | Depends on |
|---|---|---|
| `project-workspace` | Creates shared workspace directory structure and stub docs | — |
| `team-protocol` | Inter-agent message format and ticket schema | — |
| `agent-roles` | System prompts for all 10 agents | `team-protocol` |
| `agent-launcher` | Cross-platform terminal window launcher | `agent-roles`, `project-workspace` |
| `lessons-learned` | Persistent cross-project knowledge store | — |
| `ado-integration` | Azure DevOps MCP setup *(optional)* | `team-protocol` |
| `agent-orchestrator` | Full orchestration logic | `agent-launcher` |

Installing `agent-orchestrator` (what the one-liner does) automatically installs all required dependencies.

### Managing skills manually

```bash
cd ~/claude-skills

# Install a specific skill
python3 skillman.py install lessons-learned
python3 skillman.py install agent-roles==1.0.0

# Install the full team (same as the one-liner)
python3 skillman.py install agent-orchestrator

# List installed skills
python3 skillman.py list

# Update all installed skills to latest
python3 skillman.py update

# Show details for a skill
python3 skillman.py info agent-launcher

# Uninstall a skill
python3 skillman.py uninstall lessons-learned
```

---

## Azure DevOps Integration (Optional)

The orchestrator will ask during intake whether you want to connect to Azure DevOps. If you say yes, you will be prompted interactively for:

- **Organization name** — e.g. `my-company`
- **Project name** — e.g. `MyApp`
- **Repository name** — e.g. `myapp-backend`

The setup script runs `az login` and writes `.claude/mcp.json` automatically. No values are hardcoded — it works with any Azure DevOps organization.

**Requirements for ADO integration:**
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (`az`)
- [Node.js](https://nodejs.org/) 20+

To set up ADO integration standalone (outside the intake flow):

```bash
python3 ~/claude-skills/skills/ado-integration/scripts/ado-mcp-setup.py
```

When ADO is enabled, agents sync tickets as Work Items, open PRs linked to Work Items, write wiki pages, create Test Plans, and trigger pipeline runs — all through the Azure DevOps MCP server.

---

## Lessons Learned

The `lessons-learned` skill maintains a shared file at `~/.claude/lessons.md` that persists knowledge across all your projects. When a reviewer flags the same issue twice, agents automatically append a lesson so it never happens again.

Lessons are injected into every agent's prompt at launch.

```bash
# View all lessons
python3 ~/claude-skills/skills/lessons-learned/scripts/lessons_manager.py list

# Filter by agent role
python3 ~/claude-skills/skills/lessons-learned/scripts/lessons_manager.py list --agent frontend

# Add a lesson manually
python3 ~/claude-skills/skills/lessons-learned/scripts/lessons_manager.py add \
    --agent frontend "React key prop: mapped elements missing key → always key={item.id}"

# Clear all lessons
python3 ~/claude-skills/skills/lessons-learned/scripts/lessons_manager.py clear
```

---

## Updating

```bash
cd ~/claude-skills
git pull
python3 skillman.py update
```

---

## Project Structure

```
./
├── skills/
│   ├── project-workspace/    ← workspace init script and stub docs
│   ├── team-protocol/        ← comms protocol and ticket schema
│   ├── agent-roles/          ← all 10 agent system prompts
│   ├── agent-launcher/       ← cross-platform terminal launcher
│   ├── lessons-learned/      ← cross-project knowledge store
│   ├── ado-integration/      ← optional Azure DevOps MCP setup
│   └── agent-orchestrator/   ← full orchestration skill
├── dist/                     ← built .skill archives (auto-updated by CI)
├── registry.json             ← skill index with versions and artifact URLs
├── build.py                  ← packages skills and updates registry.json
├── skillman.py               ← CLI: install / uninstall / update / list / info
├── install.sh                ← macOS/Linux one-liner bootstrap
└── install.ps1               ← Windows one-liner bootstrap
```

---

## Developing Skills

### Creating a new skill

1. Create `skills/<your-skill-name>/`
2. Write `SKILL.md` with YAML frontmatter:

```yaml
---
name: your-skill-name
version: 1.0.0
description: >
  What it does and when Claude should trigger it. Max 1024 characters.
depends_on:
  - name: team-protocol
    version: ">=1.0.0"
---

# Your Skill

Skill content here...
```

3. Add any scripts or reference files under `scripts/` and `references/`
4. Build and validate locally:

```bash
python3 build.py your-skill-name
```

5. Open a PR — the CI workflow validates the build automatically

### Releasing a new version

1. Bump `version:` in `SKILL.md`
2. Merge to `main`
3. The release workflow rebuilds `dist/` and `registry.json` automatically

---

## Forking and Self-Hosting

If you fork this repo, update the URL in the install scripts after pushing to GitHub:

```bash
# In install.sh and install.ps1, change:
REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"

# Then rebuild dist/ so registry.json gets the correct artifact URLs:
python3 build.py
git add dist/ registry.json
git commit -m "chore: update artifact URLs for fork"
git push
```

`build.py` and `skillman.py` detect your GitHub remote URL automatically — only the install scripts need the manual update.

---

## CI / CD

GitHub Actions workflows handle everything automatically:

| Workflow | Trigger | Action |
|---|---|---|
| `ci.yml` | PRs | Validates skill builds |
| `release.yml` | Push to `main` (skills/** changed) | Rebuilds `dist/` and `registry.json`, commits back |

No external services required. Everything runs on GitHub Actions with the default `GITHUB_TOKEN`.
