#!/usr/bin/env python3
"""
lessons_manager.py — CLI for managing the shared cross-project lessons file.

Storage: ~/.claude/lessons.md  (one file, all agents, all projects)

Usage:
    python3 lessons_manager.py list
    python3 lessons_manager.py list --agent frontend
    python3 lessons_manager.py add --agent frontend "React key prop: missing on mapped elements → always key={item.id}"
    python3 lessons_manager.py clear
"""

import argparse
import os
import sys
from datetime import date

AGENT_SLUGS = [
    "global", "po-ba", "architect", "uiux", "frontend",
    "backend", "dba", "security", "reviewer", "qa", "devops",
]

LESSONS_FILE = os.path.join(os.path.expanduser("~"), ".claude", "lessons.md")


def ensure_file():
    os.makedirs(os.path.dirname(LESSONS_FILE), exist_ok=True)
    if not os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, "w", encoding="utf-8") as f:
            f.write("# Lessons Learned\n\n")


def cmd_list(args):
    if not os.path.exists(LESSONS_FILE):
        print("No lessons recorded yet.")
        return

    with open(LESSONS_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    if args.agent:
        tag = f"[{args.agent}]"
        lines = [l for l in lines if l.startswith("#") or tag in l]

    content = "".join(lines).strip()
    print(content if content else "No lessons recorded yet.")


def cmd_add(args):
    if args.agent not in AGENT_SLUGS:
        print(f"Error: unknown agent '{args.agent}'. Valid: {', '.join(AGENT_SLUGS)}", file=sys.stderr)
        sys.exit(1)
    if not args.text:
        print("Error: lesson text is required", file=sys.stderr)
        sys.exit(1)

    ensure_file()
    today = date.today().strftime("%Y-%m-%d")
    entry = f"- [{today}] [{args.agent}] {args.text.strip()}\n"

    with open(LESSONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"✅ Added to {LESSONS_FILE}")
    print(f"   {entry.strip()}")


def cmd_clear(args):
    if not os.path.exists(LESSONS_FILE):
        print("Nothing to clear.")
        return

    confirm = input("Clear ALL lessons? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        f.write("# Lessons Learned\n\n")
    print(f"✅ Cleared: {LESSONS_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Manage shared lessons-learned file")

    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List lessons")
    p_list.add_argument("--agent", metavar="SLUG", help="Filter by agent slug")

    p_add = sub.add_parser("add", help="Add a lesson")
    p_add.add_argument("--agent", metavar="SLUG", required=True, choices=AGENT_SLUGS)
    p_add.add_argument("text", nargs="?", help="Lesson text")

    sub.add_parser("clear", help="Clear all lessons")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "clear":
        cmd_clear(args)


if __name__ == "__main__":
    main()
