#!/usr/bin/env python3
"""
ado-mcp-setup.py — Interactive Azure DevOps MCP server setup.
Cross-platform: Windows, macOS, Linux.

Usage:
    python3 ado-mcp-setup.py
    python3 ado-mcp-setup.py --org contoso --project MyProject --repo my-repo
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"

# ── Colours (disabled on Windows CMD, enabled in PowerShell/WT) ───────────────

def supports_colour():
    if IS_WINDOWS:
        return os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM")
    return True

C = {
    "bold":  "\033[1m"  if supports_colour() else "",
    "green": "\033[32m" if supports_colour() else "",
    "yellow":"\033[33m" if supports_colour() else "",
    "red":   "\033[31m" if supports_colour() else "",
    "cyan":  "\033[36m" if supports_colour() else "",
    "reset": "\033[0m"  if supports_colour() else "",
}

def info(msg):  print(f"  {C['green']}✓{C['reset']} {msg}")
def warn(msg):  print(f"  {C['yellow']}⚠{C['reset']} {msg}")
def error(msg): print(f"  {C['red']}✗{C['reset']} {msg}")
def head(msg):  print(f"\n{C['bold']}{msg}{C['reset']}")


# ── Checks ────────────────────────────────────────────────────────────────────

def check_node():
    head("Step 1/5: Checking Node.js...")
    node = shutil.which("node")
    if not node:
        error("Node.js not found.")
        print("  Download from: https://nodejs.org  (v20+ required)")
        sys.exit(1)
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    ver = result.stdout.strip().lstrip("v")
    major = int(ver.split(".")[0])
    if major < 20:
        error(f"Node.js v{ver} found — v20+ required.")
        print("  Upgrade: https://nodejs.org")
        sys.exit(1)
    info(f"Node.js v{ver}")


def check_az_cli():
    head("Step 2/5: Checking Azure CLI...")
    az = shutil.which("az")
    if not az:
        warn("Azure CLI not found.")
        if IS_WINDOWS:
            print("  Install options:")
            print("    winget install Microsoft.AzureCLI")
            print("    or: https://aka.ms/installazurecliwindows")
        elif SYSTEM == "Darwin":
            print("    brew install azure-cli")
        else:
            print("    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        input("\n  Press Enter after installing Azure CLI...")
        if not shutil.which("az"):
            error("Azure CLI still not found. Exiting.")
            sys.exit(1)
    result = subprocess.run(["az", "--version"], capture_output=True, text=True)
    ver_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
    info(f"Azure CLI — {ver_line}")


def ensure_az_login():
    head("Step 3/5: Azure authentication...")
    result = subprocess.run(
        ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
        capture_output=True, text=True
    )
    signed_in = result.stdout.strip()
    if not signed_in or result.returncode != 0:
        warn("Not signed in. Opening browser for az login...")
        subprocess.run(["az", "login"], check=True)
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True, text=True
        )
        signed_in = result.stdout.strip()
    info(f"Signed in as: {signed_in}")
    return signed_in


def gather_ado_details(args):
    head("Step 4/5: Azure DevOps configuration")
    print()

    org = args.org or input("  ADO Organization name (e.g. contoso): ").strip()
    if not org:
        error("Organization name is required.")
        sys.exit(1)

    project = args.project or input("  ADO Project name: ").strip()
    if not project:
        error("Project name is required.")
        sys.exit(1)

    repo = args.repo or input(f"  ADO Repository name (default: {project}): ").strip()
    repo = repo or project

    wiki = args.wiki or input(f"  ADO Wiki name (default: {project}.wiki): ").strip()
    wiki = wiki or f"{project}.wiki"

    return org, project, repo, wiki


def write_config_files(org, project, repo, wiki):
    head("Step 5/5: Writing configuration files...")

    # .claude/mcp.json
    os.makedirs(".claude", exist_ok=True)
    mcp = {
        "servers": {
            "azure-devops": {
                "type": "stdio",
                "command": "npx",
                "args": [
                    "-y", "@azure-devops/mcp", org,
                    "-d", "core", "work", "work-items",
                    "repositories", "wiki", "pipelines", "test-plans"
                ]
            }
        }
    }
    with open(os.path.join(".claude", "mcp.json"), "w") as f:
        json.dump(mcp, f, indent=2)
    info(".claude/mcp.json written")

    # project/ado-config.md
    os.makedirs("project", exist_ok=True)
    sep = "\\" if IS_WINDOWS else "/"
    with open(os.path.join("project", "ado-config.md"), "w") as f:
        f.write(f"""# Azure DevOps Config

- Organization:   {org}
- Project:        {project}
- Repo:           {repo}
- Default branch: main
- Wiki:           {wiki}
- ADO URL:        https://dev.azure.com/{org}

## Work Item Types
- Features: User Story | Bugs: Bug | Tasks: Task
- Iteration path: {project}{sep}Sprint 1  (update each sprint)

## Notes
- Read this file before every ADO MCP operation
- Run `az login` if MCP calls fail with auth errors
""")
    info("project/ado-config.md written")


def verify_mcp(org):
    print("\n  Verifying MCP package is accessible...")
    result = subprocess.run(
        ["npx", "-y", "@azure-devops/mcp", "--help"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0 or "@azure-devops/mcp" in (result.stdout + result.stderr):
        info("@azure-devops/mcp is accessible")
    else:
        warn("Could not pre-verify MCP — it will download on first use (normal)")


def confirm(org, project, repo, wiki) -> bool:
    """Show a summary and ask the user to confirm before writing anything."""
    print(f"""
{C['bold']}Please review the configuration before proceeding:{C['reset']}

  Organization:    {C['bold']}{org}{C['reset']}
  Project:         {C['bold']}{project}{C['reset']}
  Repository:      {C['bold']}{repo}{C['reset']}
  Wiki:            {C['bold']}{wiki}{C['reset']}

  Files that will be created / overwritten:
    {C['yellow']}.claude/mcp.json{C['reset']}        ← MCP server config (auto-loaded by Claude Code)
    {C['yellow']}project/ado-config.md{C['reset']}   ← Shared ADO context for all agents
""")
    answer = input("  Proceed with installation? [Y/n]: ").strip().lower()
    return answer in ("", "y", "yes")


def main():
    parser = argparse.ArgumentParser(description="ADO MCP Setup")
    parser.add_argument("--org",     default=None, help="ADO organization name")
    parser.add_argument("--project", default=None, help="ADO project name")
    parser.add_argument("--repo",    default=None, help="ADO repository name")
    parser.add_argument("--wiki",    default=None, help="ADO wiki name")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt (non-interactive mode)")
    args = parser.parse_args()

    print(f"\n{C['bold']}{C['cyan']}⚡ Azure DevOps MCP Setup for Claude Code  [{SYSTEM}]{C['reset']}")
    print(f"{C['cyan']}{'━' * 52}{C['reset']}")

    check_node()
    check_az_cli()
    ensure_az_login()
    org, project, repo, wiki = gather_ado_details(args)

    if not args.yes:
        if not confirm(org, project, repo, wiki):
            print(f"\n{C['yellow']}  Cancelled — no files were written.{C['reset']}\n")
            sys.exit(0)

    write_config_files(org, project, repo, wiki)
    verify_mcp(org)

    print(f"""
{C['cyan']}{'━' * 52}{C['reset']}
{C['green']}{C['bold']}✅ ADO MCP Setup Complete!{C['reset']}

  Organization: {C['bold']}{org}{C['reset']}
  Project:      {C['bold']}{project}{C['reset']}
  Repo:         {C['bold']}{repo}{C['reset']}
  Wiki:         {C['bold']}{wiki}{C['reset']}

  Files written:
    .claude/mcp.json        ← auto-loaded by all Claude Code sessions
    project/ado-config.md   ← shared context for all agents

  {C['bold']}Next steps:{C['reset']}
  1. Open Claude Code:  {C['bold']}claude{C['reset']}
  2. Say:               {C['bold']}"Avengers assemble"{C['reset']}
  3. The MCP server starts automatically when agents need ADO tools

  {C['yellow']}Tip: run `az login` again if auth expires during a long session{C['reset']}
""")


if __name__ == "__main__":
    main()
