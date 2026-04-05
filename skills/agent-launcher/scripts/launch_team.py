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
    {"slug": "po-ba",     "name": "Product Owner / BA",    "emoji": "📋", "prompt_file": "po-ba-prompt.md"},
    {"slug": "uiux",      "name": "UI/UX Designer",         "emoji": "🎨", "prompt_file": "uiux-prompt.md"},
    {"slug": "architect", "name": "Software Architect",     "emoji": "🏗️", "prompt_file": "architect-prompt.md"},
    {"slug": "frontend",  "name": "Frontend Developer",     "emoji": "⚛️",  "prompt_file": "frontend-prompt.md"},
    {"slug": "backend",   "name": "Backend Developer",      "emoji": "⚙️",  "prompt_file": "backend-prompt.md"},
    {"slug": "dba",       "name": "Database Administrator", "emoji": "🗄️", "prompt_file": "dba-prompt.md"},
    {"slug": "security",  "name": "Security Expert",        "emoji": "🔐", "prompt_file": "security-prompt.md"},
    {"slug": "reviewer",  "name": "Code Reviewer",          "emoji": "🔍", "prompt_file": "reviewer-prompt.md"},
    {"slug": "qa",        "name": "QA Engineer",            "emoji": "🧪", "prompt_file": "qa-prompt.md"},
    {"slug": "devops",    "name": "DevOps Engineer",        "emoji": "🚀", "prompt_file": "devops-prompt.md"},
]

AGENT_BY_SLUG = {a["slug"]: a for a in ALL_AGENTS}

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

# ── Prompt Writing ─────────────────────────────────────────────────────────────

def write_agent_prompt(agent: dict, workspace: str, templates_dir: str,
                       ado_org: str = None, ado_project: str = None,
                       ado_repo: str = None) -> bool:
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


# ── Cross-Platform Warp Tab Launcher ──────────────────────────────────────────

def open_warp_tab(agent: dict, workspace: str, delay: float = 1.5) -> bool:
    """Open a new Warp tab and run the claude agent."""
    prompt_path = os.path.join(workspace, "logs", agent["prompt_file"])
    tab_title   = f"{agent['emoji']} {agent['name']}"
    claude_cmd  = f'claude --system-file "{prompt_path}"'

    if IS_MAC:
        return _open_warp_tab_mac(tab_title, claude_cmd, delay)
    elif IS_WINDOWS:
        return _open_warp_tab_windows(tab_title, claude_cmd, delay)
    else:
        return _open_warp_tab_linux(tab_title, claude_cmd, delay)


def _open_warp_tab_mac(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """macOS — AppleScript via osascript."""
    script = f"""
tell application "Warp"
    activate
end tell
delay 0.5
tell application "System Events"
    tell process "Warp"
        keystroke "t" using command down
        delay {delay}
        keystroke "printf '\\\\033]0;{tab_title}\\\\007'"
        key code 36
        delay 0.3
        keystroke "{claude_cmd}"
        key code 36
    end tell
end tell
"""
    result = subprocess.run(["osascript", "-e", script],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n    ⚠️  AppleScript failed: {result.stderr.strip()}")
        print(f"    Run manually in Warp: {claude_cmd}")
        return False
    return True


def _open_warp_tab_windows(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """
    Windows — PowerShell SendKeys to Warp.
    Falls back to printing the manual command if automation fails.
    """
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Milliseconds 500

# Bring Warp to front
$warp = Get-Process -Name "Warp" -ErrorAction SilentlyContinue
if ($warp) {{
    Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Win32 {{
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
    }}
"@
    [Win32]::SetForegroundWindow($warp.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 500
}}

# Open new tab (Ctrl+T in Warp on Windows)
[System.Windows.Forms.SendKeys]::SendWait("^t")
Start-Sleep -Milliseconds {int(delay * 1000)}

# Type the command
[System.Windows.Forms.SendKeys]::SendWait("{claude_cmd.replace('"', '`"')}")
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        _print_manual_fallback(tab_title, claude_cmd)
        return False
    return True


def _open_warp_tab_linux(tab_title: str, claude_cmd: str, delay: float) -> bool:
    """
    Linux — try xdotool (X11) or wmctrl combo. Falls back to manual command.
    """
    time.sleep(0.5)

    # Try xdotool first (X11)
    if subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
        try:
            subprocess.run(["xdotool", "search", "--name", "Warp",
                            "windowactivate", "--sync"], check=True, capture_output=True)
            time.sleep(0.3)
            subprocess.run(["xdotool", "key", "ctrl+t"], check=True)
            time.sleep(delay)
            subprocess.run(["xdotool", "type", "--clearmodifiers", claude_cmd], check=True)
            subprocess.run(["xdotool", "key", "Return"], check=True)
            return True
        except subprocess.CalledProcessError:
            pass

    # Try wmctrl + xdotool combo
    if subprocess.run(["which", "wmctrl"], capture_output=True).returncode == 0:
        try:
            subprocess.run(["wmctrl", "-a", "Warp"], check=True, capture_output=True)
            time.sleep(0.3)
            subprocess.run(["xdotool", "key", "ctrl+t"], check=True)
            time.sleep(delay)
            subprocess.run(["xdotool", "type", "--clearmodifiers", claude_cmd], check=True)
            subprocess.run(["xdotool", "key", "Return"], check=True)
            return True
        except subprocess.CalledProcessError:
            pass

    _print_manual_fallback(tab_title, claude_cmd)
    return False


def _print_manual_fallback(tab_title: str, claude_cmd: str):
    print(f"\n    ℹ️  Open a new Warp tab manually and run:")
    print(f"       {claude_cmd}")


def spawn_agent(agent: dict, workspace: str, templates_dir: str,
                ado_org=None, ado_project=None, ado_repo=None,
                delay: float = 1.5) -> bool:
    """Write prompt and open Warp tab for one agent."""
    print(f"  {agent['emoji']} Spawning {agent['name']}...", end=" ", flush=True)
    ok = write_agent_prompt(agent, workspace, templates_dir, ado_org, ado_project, ado_repo)
    if not ok:
        print("❌ (prompt template missing)")
        return False
    ok = open_warp_tab(agent, workspace, delay)
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
    args = parser.parse_args()

    workspace     = os.path.abspath(args.workspace)
    templates_dir = resolve_templates_dir(args.templates_dir)
    ado_org       = args.ado_org
    ado_project   = args.ado_project or (ado_org and "MyProject") or None
    ado_repo      = args.ado_repo    or ado_project or None

    agents_to_spawn = (ALL_AGENTS if args.spawn_all
                       else [AGENT_BY_SLUG[s] for s in args.agents]
                       if args.agents
                       else [AGENT_BY_SLUG["po-ba"]])

    print(f"\n⚡ Avengers — Agent Launcher  [{SYSTEM}]\n")
    print(f"📁 Workspace:  {workspace}")
    print(f"📂 Templates:  {templates_dir}")
    if ado_org:
        print(f"🔷 Azure DevOps: {ado_org}/{ado_project}")
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

    print("🚀 Launching Warp tabs...\n")
    spawned = []
    for agent in agents_to_spawn:
        ok = spawn_agent(agent, workspace, templates_dir,
                         ado_org, ado_project, ado_repo, args.tab_delay)
        if ok:
            spawned.append(agent)
        time.sleep(args.tab_delay)

    ado_note = f"\n  🔷 ADO: {ado_org}/{ado_project}" if ado_org else ""

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {len(spawned)} agent(s) ready{ado_note}
{chr(10).join(f"  {a['emoji']} {a['name']}" for a in spawned)}

Prompts written to: {workspace}/logs/
If any tabs didn't open automatically, run the printed command in a new Warp tab.

Next: switch to the active tab and give the agent their first task.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
