#!/usr/bin/env python3
"""
workspace_init.py — Initialize the shared project workspace for the AI dev team.

Usage:
    python3 workspace_init.py --workspace ./project
    python3 workspace_init.py --workspace /abs/path/to/project --ado-org contoso
"""

import argparse
import os


# ── Directory structure ────────────────────────────────────────────────────────

WORKSPACE_DIRS = [
    "inbox",
    "outbox",
    "decisions",
    "specs",
    "specs/test-plans",
    "tickets",
    "logs",
    "logs/archive",
    "docs/architecture",
    "docs/business-logic",
    "docs/api",
    "docs/database",
    "docs/security",
    "docs/devops",
]

# ── Stub doc files (created only if missing) ──────────────────────────────────

STUB_DOCS = {
    "docs/architecture/README.md":   "# Architecture Map\n\n_Populated by Architect._\n",
    "docs/business-logic/README.md": "# Business Logic\n\n_Populated by PO/BA._\n",
    "docs/api/README.md":            "# API Reference\n\n_Populated by Backend._\n",
    "docs/database/README.md":       "# Database Schema\n\n_Populated by DBA._\n",
    "docs/security/README.md":       "# Security Notes\n\n_Populated by Security._\n",
    "docs/devops/README.md":         "# DevOps & Deployment\n\n_Populated by DevOps._\n",
}

WORKSPACE_README = """\
# Project Workspace

Shared memory for the dev team. Managed by the Orchestrator.

## Token Efficiency Rules (ALL AGENTS MUST FOLLOW)
1. Read `docs/` before exploring the codebase or asking questions
2. Update `docs/` after every significant change
3. One concern per file — keep files under ~200 lines
4. DRY: extract shared logic, never duplicate
5. KISS: simplest solution that satisfies the requirement
6. On startup: write/update your rules in `.claude/skills/<slug>-rules.md`

## Structure
- inbox/<agent>.md              — messages TO an agent
- outbox/                       — messages FROM agents
- decisions/                    — finalized team decisions
- specs/                        — feature specs, user stories, wireframes
- tickets/                      — task tickets
- docs/architecture/README.md   — module map, tech stack (Architect)
- docs/business-logic/README.md — domain rules, flows (PO/BA)
- docs/api/README.md            — endpoint reference (Backend)
- docs/database/README.md       — schema, indexes, migrations (DBA)
- docs/security/README.md       — threat model, secrets policy (Security)
- docs/devops/README.md         — pipelines, environments, rollback (DevOps)
- .claude/skills/<slug>-rules.md — each agent's personal session rules
"""


# ── Core functions ─────────────────────────────────────────────────────────────

def init_workspace(workspace: str):
    """Create workspace directories and seed stub docs. Idempotent."""
    workspace = os.path.abspath(workspace)

    for d in WORKSPACE_DIRS:
        os.makedirs(os.path.join(workspace, d), exist_ok=True)

    # .claude/skills/ lives one level above the workspace directory
    project_root = os.path.dirname(workspace)
    os.makedirs(os.path.join(project_root, ".claude", "skills"), exist_ok=True)

    readme = os.path.join(workspace, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write(WORKSPACE_README)

    for rel, content in STUB_DOCS.items():
        full = os.path.join(workspace, rel)
        if not os.path.exists(full):
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)


def seed_po_ba_inbox(workspace: str, ado_org: str = None):
    """Write the initial planning task to the PO/BA inbox."""
    workspace = os.path.abspath(workspace)
    ado_note = (
        f"\n8. ADO is connected (org: {ado_org}). "
        "Create Work Items for each epic."
    ) if ado_org else ""

    inbox_path = os.path.join(workspace, "inbox", "po-ba.md")
    with open(inbox_path, "w", encoding="utf-8") as f:
        f.write(f"""\
## \U0001f4ec Message from Orchestrator

**To:** Product Owner / Business Analyst
**From:** Orchestrator
**Priority:** High

Before any project work, write your session rules to:
`.claude/skills/po-ba-rules.md`

Then start the planning session:
1. Introduce yourself and your role
2. Ask for the project brief
3. Break it down into epics and user stories
4. Identify risks and edge cases
5. Propose a high-level roadmap
6. Update docs/business-logic/README.md
7. Write output to: outbox/po-ba-planning.md{ado_note}
""")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Initialize the AI dev team project workspace"
    )
    parser.add_argument(
        "--workspace",
        default=os.path.join(os.getcwd(), "project"),
        help="Path to the shared workspace directory (default: ./project)",
    )
    parser.add_argument(
        "--ado-org",
        default=None,
        help="ADO organization name — if set, includes ADO note in PO/BA inbox",
    )
    parser.add_argument(
        "--seed-inbox",
        action="store_true",
        help="Also write the initial PO/BA inbox message",
    )
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)

    print(f"\n\U0001f527 Initializing workspace: {workspace}")
    init_workspace(workspace)
    print("  \u2705 Directories created")
    print("  \u2705 Stub docs seeded")

    if args.seed_inbox:
        seed_po_ba_inbox(workspace, args.ado_org)
        print("  \u2705 PO/BA inbox seeded")

    print(f"\n\U0001f4c1 Workspace ready at: {workspace}\n")


if __name__ == "__main__":
    main()
