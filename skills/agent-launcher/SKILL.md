---
name: agent-launcher
version: 1.0.0
description: >
  Launches Claude Code agent instances in terminal windows for the AI dev
  team. Writes agent system prompts from role templates (substituting workspace
  path, injecting cross-project lessons, and optionally appending ADO addendum),
  opens terminal windows cross-platform (Windows via Windows Terminal or
  PowerShell, macOS via AppleScript, Linux via gnome-terminal/xterm/konsole).
  If automation fails on any platform, prints the exact manual command — no
  work is lost. Depends on agent-roles for prompt templates and
  project-workspace for the workspace directory structure.
depends_on:
  - name: agent-roles
    version: ">=1.0.0"
  - name: project-workspace
    version: ">=1.0.0"
---

# agent-launcher

Handles the mechanics of opening terminal windows and starting Claude Code
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

# With Azure DevOps integration (prompts are set by the user — no hardcoded values)
python3 skills/agent-launcher/scripts/launch_team.py \
    --agents po-ba --workspace ./project \
    --ado-org <your-org> --ado-project <your-project> --ado-repo <your-repo>

# Skip lessons injection
python3 skills/agent-launcher/scripts/launch_team.py --all \
    --workspace ./project --no-lessons
```

The `--templates-dir` flag overrides where prompt files are loaded from
(default: the `scripts/` directory of the agent-roles skill).

---

## Platform Behaviour

| OS | Method | Requirement |
|---|---|---|
| **Windows** | Windows Terminal (`wt`) or `Start-Process powershell` | Windows Terminal recommended |
| **macOS** | AppleScript via `osascript` | Terminal or iTerm2 |
| **Linux** | gnome-terminal, xterm, konsole, or xfce4-terminal (tried in order) | Any one installed |

If automation fails on any platform, the script prints the exact `claude`
command to run manually — the prompt file is always written regardless.

---

## What Happens When an Agent Is Spawned

1. The prompt template for the agent's role is read from `agent-roles/scripts/`
2. `{{WORKSPACE_PATH}}` is substituted with the absolute workspace path
3. The self-configuration block is appended (instructs agent to write rules file)
4. Cross-project lessons from `~/.claude/lessons.md` are injected (unless `--no-lessons`)
5. If ADO is configured, `ado-integration/scripts/ado-addendum.md` is appended
6. The merged prompt is saved to `./project/logs/<slug>-prompt.md`
7. A new terminal window is opened and `claude --system-prompt-file <prompt-path>` is run
8. If po-ba is being spawned, the initial planning task is written to `inbox/po-ba.md`

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
- `write_agent_prompt(agent, workspace, templates_dir, ado_org, ado_project, ado_repo, inject_lessons)` — builds and saves the merged prompt
- `open_terminal_window(agent, workspace, delay)` — dispatches to the platform-specific opener
- `build_lessons_block()` — reads `~/.claude/lessons.md` and formats the injection block
- `spawn_agent(agent, workspace, templates_dir, ...)` — writes prompt then opens terminal
- `seed_po_ba_inbox(workspace, ado_org)` — writes the initial PO/BA task (delegated to project-workspace)
