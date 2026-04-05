# Claude Skills Library

A monorepo that hosts, versions, builds, and distributes Claude Code skills as
installable packages with dependency resolution. Hosted on Azure DevOps.

---

## What Is a Skill?

A **skill** is a folder containing a `SKILL.md` file (with YAML frontmatter
declaring its name, version, description, and dependencies) plus any scripts
and reference files the skill needs. Skills are packaged as `.skill` archives
and published to an ADO Artifact feed.

The flagship skill is **`agent-orchestrator`**, which depends on 5 other skills
that together implement the full 10-role AI dev team.

---

## Skills in This Repo

| Skill | Description | Depends on |
|---|---|---|
| `project-workspace` | Workspace init, directory structure, stub docs | — |
| `team-protocol` | Comms protocol, ticket schema | — |
| `agent-roles` | All 10 agent system prompts | team-protocol |
| `agent-launcher` | Cross-platform Warp tab launcher | agent-roles, project-workspace |
| `ado-integration` | Azure DevOps MCP setup and agent reference | team-protocol |
| `agent-orchestrator` | Orchestration logic — no bundled scripts | agent-launcher, ado-integration |

---

## Installing on a New Machine

### Windows (PowerShell)

```powershell
irm https://dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills/raw/main/install.ps1 | iex
```

Or clone and run manually:

```powershell
git clone https://VitaliiRibii@dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills
cd claude-skills
.\install.ps1
```

### macOS / Linux

```bash
bash <(curl -fsSL https://dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills/raw/main/install.sh)
```

Or clone and run manually:

```bash
git clone https://VitaliiRibii@dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills
cd claude-skills
bash install.sh
```

Both scripts install `agent-orchestrator` and all its dependencies automatically.

### Install a specific skill

```bash
python3 skillman.py install project-workspace
python3 skillman.py install agent-roles==1.0.0
```

---

## How to Use

After installing, open Claude Code in any project directory and say:

> **"Avengers assemble"**

The orchestrator will run Phase 1 (intake interview), initialize the workspace,
and spawn agents on demand.

---

## Developing a New Skill

1. Create a directory under `skills/<your-skill-name>/`
2. Write `SKILL.md` with the required frontmatter:

```yaml
---
name: your-skill-name
version: 1.0.0
description: >
  One paragraph. What it does, when to trigger it. Max 1024 characters.
depends_on:
  - name: other-skill
    version: ">=1.0.0"
---
```

3. Add your scripts and reference files as needed
4. Build and validate locally:

```bash
python3 build.py your-skill-name
```

5. Open a PR to `main` — the pipeline builds and publishes automatically

---

## Versioning and Releases

- Versions follow **SemVer**: `MAJOR.MINOR.PATCH`
- The `version` field in `SKILL.md` is the source of truth
- To release `v1.1.0` of `agent-roles`:
  1. Bump `version: 1.1.0` in `skills/agent-roles/SKILL.md`
  2. Merge to `main` — pipeline rebuilds `registry.json`
  3. Tag the commit: `git tag skills/agent-roles/v1.1.0 && git push --tags`
  4. The pipeline's `Publish` stage publishes the new version to the feed

---

## Running the Pipeline Manually

1. Go to Azure DevOps → Pipelines → `claude-skills`
2. Click **Run pipeline**
3. Select branch `main`
4. The pipeline builds all skills and publishes the `skills` artifact

---

## Adding a Dependency Between Skills

1. In the dependent skill's `SKILL.md`, add to `depends_on`:

```yaml
depends_on:
  - name: team-protocol
    version: ">=1.0.0"
```

2. In your skill's body, reference the dependency's files by their full path
   under `skills/<dep-name>/`:

```
See skills/team-protocol/references/comms-protocol.md for the message format.
```

3. `skillman.py install` will automatically resolve and install the dependency
   before your skill.

---

## Project Structure

```
./
├── skills/
│   ├── project-workspace/    ← foundation skill
│   ├── team-protocol/        ← foundation skill
│   ├── agent-roles/          ← depends on team-protocol
│   ├── agent-launcher/       ← depends on agent-roles, project-workspace
│   ├── ado-integration/      ← depends on team-protocol
│   └── agent-orchestrator/   ← depends on agent-launcher, ado-integration
├── dist/                     ← built .skill archives (gitignored)
├── registry.json             ← skill index (auto-updated by pipeline)
├── build.py                  ← builds .skill archives, updates registry.json
├── skillman.py               ← install / uninstall / update / list / info
├── azure-pipelines.yml       ← CI/CD: build → publish artifact → publish feed
├── install.ps1               ← Windows bootstrap script
└── install.sh                ← macOS/Linux bootstrap script
```
