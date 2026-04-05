---
name: agent-launcher
version: 1.0.0
description: >
  Launches Claude Code agent instances in Warp terminal tabs for the AI dev
  team. Writes agent system prompts from role templates (substituting workspace
  path and appending ADO addendum if configured), opens Warp tabs
  cross-platform (Windows via PowerShell SendKeys, macOS via AppleScript,
  Linux via xdotool with Wayland fallback), and seeds the PO/BA inbox. If tab
  automation fails on any platform, prints the exact manual command — no work
  is lost. Depends on agent-roles for prompt templates and project-workspace
  for the workspace directory structure.
depends_on:
  - name: agent-roles
    version: ">=1.0.0"
  - name: project-workspace
    version: ">=1.0.0"
---

# agent-launcher

Handles the mechanics of opening Warp terminal tabs and starting Claude Code
agent instances. Called by the orchestrator whenever a new agent needs to be
spawned.

---

## Usage

```bash
# Spawn a single agent
python3 skills/agent-launcher/scripts/launch_team.py --agents po-ba \
    --workspace ./project

# Spawn multiple agents
python3 skills/agent-launcher/scripts/launch_team.py \
    --agents architect frontend --workspace ./project

# Spawn all 10 agents
python3 skills/agent-launcher/scripts/launch_team.py --all \
    --workspace ./project

# With ADO integration
python3 skills/agent-launcher/scripts/launch_team.py \
    --agents po-ba --workspace ./project \
    --ado-org contoso --ado-project MyProject --ado-repo my-repo
```

The `--templates-dir` flag overrides where prompt files are loaded from
(default: the `scripts/` directory of the agent-roles skill).

---

## Platform Behaviour

| OS | Method | Requirement |
|---|---|---|
| **Windows** | PowerShell `SendKeys` to Warp | Warp must be the active window |
| **macOS** | AppleScript via `osascript` | Accessibility permission granted to Warp |
| **Linux (X11)** | `xdotool` key/type | `sudo apt install xdotool` |
| **Linux (Wayland)** | Manual fallback | User runs the printed command in a new tab |

If automation fails on any platform, the script prints the exact `claude`
command to run manually — the prompt file is always written regardless.

---

## What Happens When an Agent Is Spawned

1. The prompt template for the agent's role is read from `agent-roles/scripts/`
2. `{{WORKSPACE_PATH}}` is substituted with the absolute workspace path
3. The self-configuration block is appended (instructs agent to write rules file)
4. If ADO is configured, `ado-integration/scripts/ado-addendum.md` is appended
5. The merged prompt is saved to `./project/logs/<slug>-prompt.md`
6. A new Warp tab is opened and `claude --system-file <prompt-path>` is run
7. If po-ba is being spawned, the initial planning task is written to `inbox/po-ba.md`

---

## Typical Spawn Sequence (new project)

```
1. po-ba     → always first (planning)
2. architect → after requirements are clear
3. uiux      → when UI work is scoped
4. dba       → when data model is needed
5. backend   → when API work starts
6. devops    → when CI/CD or deployment is needed
7. frontend  → when UI tickets are ready
8. security  → auth/API tickets hit in-review [SECURITY]
9. reviewer  → any code ticket hits in-review
10. qa       → features are implementation-complete
```

---

## Script Reference

`scripts/launch_team.py` — cross-platform launcher.

Key functions:
- `write_agent_prompt(agent, workspace, templates_dir, ado_org, ado_project, ado_repo)` — builds and saves the merged prompt
- `open_warp_tab(agent, workspace, delay)` — dispatches to the platform-specific opener
- `spawn_agent(agent, workspace, templates_dir, ...)` — writes prompt then opens tab
- `seed_po_ba_inbox(workspace, ado_org)` — writes the initial PO/BA task (delegated to project-workspace)
