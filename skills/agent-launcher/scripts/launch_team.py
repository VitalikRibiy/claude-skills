#!/usr/bin/env python3
"""
launch_team.py — Launches agent Warp tabs for the Avengers dev team.
Cross-platform: Windows, macOS, Linux.

Workspace initialization is handled by project-workspace/scripts/workspace_init.py.
This script handles prompt writing and Warp tab launching only.

Usage:
    python3 launch_team.py --agents po-ba                    # spawn one agent
    python3 launch_team.py --agents architect frontend        # spawn multiple
    python3 launch_team.py --all                             # spawn all 10
    python3 launch_team.py --ado-org contoso --agents po-ba  # with ADO
    python3 launch_team.py --all --lessons-dir ~/.claude/lessons  # with lessons

Requirements:
    - Warp terminal installed (https://warp.dev)
    - `claude` CLI installed and authenticated
    - For ADO: `az login` completed and .claude/mcp.json written
"""

import argparse
import os
import platform
import subprocess
import sys
import time

# ── Platform detection ────────────────────────────────────────────────────────

SYSTEM = platform.system()   # "Windows", "Darwin", "Linux"
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC     = SYSTEM == "Darwin"
IS_LINUX   = SYSTEM == "Linux"

# ── Team Roster ───────────────────────────────────────────────────────────────

ALL_AGENTS = [
    {"slug": "po-ba",     "name": "Product Owner / BA",    "emoji": "📋", "prompt_file": "po-ba-prompt.md",     "thinking_tokens": 10000},
    {"slug": "uiux",      "name": "UI/UX Designer",         "emoji": "🎨", "prompt_file": "uiux-prompt.md"},
    {"slug": "architect", "name": "Software Architect",     "emoji": "🏗️", "prompt_file": "architect-prompt.md", "thinking_tokens": 10000},
    {"slug": "frontend",  "name": "Frontend Developer",     "emoji": "⚛️",  "prompt_file": "frontend-prompt.md"},
    {"slug": "backend",   "name": "Backend Developer",      "emoji": "⚙️",  "prompt_file": "backend-prompt.md"},
    {"slug": "dba",       "name": "Database Administrator", "emoji": "🗄️", "prompt_file": "dba-prompt.md"},
    {"slug": "security",  "name": "Security Expert",        "emoji": "🔐", "prompt_file": "security-prompt.md"},
    {"slug": "reviewer",  "name": "Code Reviewer",          "emoji": "🔍", "prompt_file": "reviewer-prompt.md"},
    {"slug": "qa",        "name": "QA Engineer",            "emoji": "🧪", "prompt_file": "qa-prompt.md"},
    {"slug": "devops",    "name": "DevOps Engineer",        "emoji": "🚀", "prompt_file": "devops-prompt.md"},
]

AGENT_BY_SLUG = {a["slug"]: a for a in ALL_AGENTS}

LESSONS_FILE = os.path.join(os.path.expanduser("~"), ".claude", "lessons.md")

# ── Self-config block appended to every agent prompt ──────────────────────────

SELF_CONFIG_BLOCK = """
## First Action — Write Your Rules File

Before any project work, write your personal session rules to:
.claude/skills/{slug}-rules.md

Structure:
---
# {role} — Session Rules
_Last updated: <today> | Project: <name>_

## Context Map — Read These First Every Session
- Primary:      {workspace}/docs/<my-domain>/README.md
- Architecture: {workspace}/docs/architecture/README.md

## Feature Heatmap
| Feature / Area | Heat | Last ticket | Notes |
|---|---|---|---|
| [populate from tickets/ and codebase] | 🔥 | | |

## Project Conventions
- Stack: [from docs/architecture/README.md]
- Patterns to follow: [from decisions/]
- Anti-patterns: [from decisions/ or team guidance]

## My Checklist (every task)
- [ ] Read relevant docs/ before starting
- [ ] Check decisions/ for prior art
- [ ] Update docs/ and heatmap after finishing

## Token Savers
- Always check docs/ before reading source files
- My most-needed files: [list 3-5 specific paths]
---
Update this file after every task — keep the heatmap current.
"""

# ── Lessons Injection ─────────────────────────────────────────────────────────

def build_lessons_block() -> str:
    """Read the shared lessons file and return an injection block."""
    if os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            content = "_No lessons recorded yet._"
    else:
        content = "_No lessons recorded yet._"

    return f"""
## Lessons from Past Projects

{content}

---
**When to add a new lesson:** A reviewer flags the same issue twice in one session,
or you catch yourself about to repeat a known mistake.
Append to `{LESSONS_FILE}`:
`- [YYYY-MM-DD] [your-role] **Short title**: what went wrong → what to do instead`
"""


# ── Prompt Writing ─────────────────────────────────────────────────────────────

def write_agent_prompt(agent: dict, workspace: str, templates_dir: str,
                       ado_org: str = None, ado_project: str = None,
                       ado_repo: str = None, inject_lessons: bool = True) -> bool:
    """Build and save the merged agent prompt. Returns True if successful."""
    logs_dir = os.path.join(workspace, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    template_path = os.path.join(templates_dir, agent["prompt_file"])
    if not os.path.exists(template_path):
        print(f"  ⚠️  Template not found: {template_path}")
        return False

    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    content = content.replace("{{WORKSPACE_PATH}}", workspace)
    content += SELF_CONFIG_BLOCK.format(
        slug=agent["slug"], role=agent["name"], workspace=workspace)

    if inject_lessons:
        content += "\n\n---\n\n" + build_lessons_block()

    if ado_org:
        # Look for ado-addendum.md relative to this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Try same directory first, then parent skill's scripts/
        addendum_candidates = [
            os.path.join(script_dir, "ado-addendum.md"),
            os.path.join(os.path.dirname(script_dir),
                         "..", "ado-integration", "scripts", "ado-addendum.md"),
        ]
        for addendum_path in addendum_candidates:
            addendum_path = os.path.normpath(addendum_path)
            if os.path.exists(addendum_path):
                with open(addendum_path, encoding="utf-8") as f:
                    addendum = f.read().replace("{{WORKSPACE_PATH}}", workspace)
                content += "\n\n---\n\n" + addendum
                break

    with open(os.path.join(logs_dir, agent["prompt_file"]), "w", encoding="utf-8") as f:
        f.write(content)
    return True


# ── Cross-Platform Terminal Launcher ─────────────────────────────────────────

def open_terminal_window(agent: dict, workspace: str, delay: float = 1.5) -> bool:
    """Open a new terminal window and run the claude agent."""
    prompt_path = os.path.join(workspace, "logs", agent["prompt_file"])
    tab_title   = f"{agent['emoji']} {agent['name']}"
    thinking_flag = f' --thinking-budget-tokens {agent["thinking_tokens"]}' if agent.get("thinking_tokens") else ''
    claude_cmd  = f'claude{thinking_flag} --system-prompt-file "{prompt_path}"'

    if IS_MAC:
        return _open_terminal_mac(tab_title, claude_cmd, delay)
    elif IS_WINDOWS:
        return _open_terminal_windows(tab_title, claude_cmd, delay)
    else:
        return _open_terminal_linux(tab_title, claude_cmd, delay)


def _open_terminal_mac(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """macOS — new Terminal.app window via AppleScript."""
    escaped = claude_cmd.replace('"', '\\"')
    script = f"""
tell application "Terminal"
    do script "{escaped}"
    activate
end tell
"""
    result = subprocess.run(["osascript", "-e", script],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n    ⚠️  AppleScript failed: {result.stderr.strip()}")
        _print_manual_fallback(tab_title, claude_cmd)
        return False
    time.sleep(delay)
    return True


def _open_terminal_windows(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """
    Windows — tries two strategies in order:
    1. Windows Terminal (wt new-tab) if available
    2. New PowerShell window via Start-Process
    """
    # ── Strategy 1: Windows Terminal ─────────────────────────────────────────
    wt = subprocess.run(["where", "wt"], capture_output=True, text=True)
    if wt.returncode == 0:
        result = subprocess.run(
            ["wt", "new-tab", "--title", tab_title, "--suppressApplicationTitle",
             "--", "powershell", "-NoExit", "-Command", claude_cmd],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            time.sleep(delay)
            return True

    # ── Strategy 2: New PowerShell window ────────────────────────────────────
    safe_cmd = claude_cmd.replace("'", "''")
    ps_cmd = f"Start-Process powershell -ArgumentList '-NoExit', '-Command', '{safe_cmd}'"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        time.sleep(delay)
        return True

    _print_manual_fallback(tab_title, claude_cmd)
    return False


def _open_terminal_linux(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """
    Linux — tries common terminal emulators in order, falls back to manual.
    """
    terminals = [
        ["gnome-terminal", "--title", tab_title, "--", "bash", "-c",
         f'{claude_cmd}; exec bash'],
        ["xterm", "-title", tab_title, "-e", f'{claude_cmd}; bash'],
        ["konsole", "--new-tab", "-e", f'{claude_cmd}; bash'],
        ["xfce4-terminal", "--title", tab_title, "-e", f'{claude_cmd}; bash'],
    ]
    for cmd in terminals:
        if subprocess.run(["which", cmd[0]], capture_output=True).returncode == 0:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                time.sleep(delay)
                return True
    _print_manual_fallback(tab_title, claude_cmd)
    return False


def _print_manual_fallback(tab_title: str, claude_cmd: str):
    print(f"\n    ℹ️  Open a new terminal window manually and run:")
    print(f"       {claude_cmd}")


def spawn_agent(agent: dict, workspace: str, templates_dir: str,
                ado_org=None, ado_project=None, ado_repo=None,
                inject_lessons: bool = True, delay: float = 1.5) -> bool:
    """Write prompt and open Warp tab for one agent."""
    print(f"  {agent['emoji']} Spawning {agent['name']}...", end=" ", flush=True)
    ok = write_agent_prompt(agent, workspace, templates_dir, ado_org, ado_project, ado_repo,
                            inject_lessons=inject_lessons)
    if not ok:
        print("❌ (prompt template missing)")
        return False
    ok = open_terminal_window(agent, workspace, delay)
    if ok:
        print("✅")
    else:
        print("⚠️  (open tab manually — command printed above)")
    return True   # prompt was written even if tab automation failed


# ── Helpers ───────────────────────────────────────────────────────────────────

def resolve_templates_dir(args_templates_dir: str) -> str:
    """Find the agent prompt templates directory."""
    if args_templates_dir:
        return args_templates_dir
    # Default: agent-roles/scripts/ relative to this file's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.normpath(
        os.path.join(script_dir, "..", "..", "agent-roles", "scripts")
    )
    if os.path.isdir(candidate):
        return candidate
    # Fallback: same directory as this script
    return script_dir


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Avengers dev team launcher")
    parser.add_argument("--workspace", default=os.path.join(os.getcwd(), "project"),
                        help="Path to shared project workspace (default: ./project)")
    parser.add_argument("--templates-dir", default=None,
                        help="Path to agent prompt templates (default: agent-roles/scripts/)")
    parser.add_argument("--tab-delay", type=float, default=1.5,
                        help="Seconds between opening tabs (default: 1.5)")
    parser.add_argument("--agents", nargs="+", metavar="SLUG",
                        choices=list(AGENT_BY_SLUG.keys()),
                        help="Agent slugs to spawn (e.g. po-ba architect)")
    parser.add_argument("--all", action="store_true", dest="spawn_all",
                        help="Spawn all 10 agents")
    parser.add_argument("--ado-org",     default=None)
    parser.add_argument("--ado-project", default=None)
    parser.add_argument("--ado-repo",    default=None)
    parser.add_argument("--no-lessons", action="store_true",
                        help="Skip lessons injection")
    args = parser.parse_args()

    workspace       = os.path.abspath(args.workspace)
    templates_dir   = resolve_templates_dir(args.templates_dir)
    ado_org         = args.ado_org
    ado_project     = args.ado_project or None
    ado_repo        = args.ado_repo    or ado_project or None
    inject_lessons  = not args.no_lessons

    agents_to_spawn = (ALL_AGENTS if args.spawn_all
                       else [AGENT_BY_SLUG[s] for s in args.agents]
                       if args.agents
                       else [AGENT_BY_SLUG["po-ba"]])

    print(f"\n⚡ Avengers — Agent Launcher  [{SYSTEM}]\n")
    print(f"📁 Workspace:  {workspace}")
    print(f"📂 Templates:  {templates_dir}")
    if ado_org:
        print(f"🔷 Azure DevOps: {ado_org}/{ado_project}")
    if inject_lessons:
        status = "found" if os.path.exists(LESSONS_FILE) else "empty (will be created on first lesson)"
        print(f"📚 Lessons:    {LESSONS_FILE}  [{status}]")
    print(f"🤖 Agents:     {', '.join(a['slug'] for a in agents_to_spawn)}\n")

    if not os.path.isdir(workspace):
        print(f"⚠️  Workspace not found: {workspace}")
        print("   Run workspace_init.py first:")
        print(f"   python3 skills/project-workspace/scripts/workspace_init.py --workspace {workspace}")
        sys.exit(1)

    if IS_LINUX:
        has_xdotool = subprocess.run(["which", "xdotool"],
                                     capture_output=True).returncode == 0
        if not has_xdotool:
            print("ℹ️  xdotool not found. Tab automation disabled.")
            print("   Install: sudo apt install xdotool   (or run agents manually)\n")

    print("🚀 Launching terminal windows...\n")
    spawned = []
    for agent in agents_to_spawn:
        ok = spawn_agent(agent, workspace, templates_dir,
                         ado_org, ado_project, ado_repo,
                         inject_lessons=inject_lessons, delay=args.tab_delay)
        if ok:
            spawned.append(agent)
        time.sleep(args.tab_delay)

    ado_note = f"\n  🔷 ADO: {ado_org}/{ado_project}" if ado_org else ""

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {len(spawned)} agent(s) ready{ado_note}
{chr(10).join(f"  {a['emoji']} {a['name']}" for a in spawned)}

Prompts written to: {workspace}/logs/
If any windows didn't open automatically, run the printed command in a new terminal.

Next: switch to the agent's terminal and give them their first task.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
