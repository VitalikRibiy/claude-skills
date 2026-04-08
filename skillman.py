#!/usr/bin/env python3
"""
skillman.py  Claude Skills package manager.

Commands:
    install <name>              Install a skill and all its dependencies
    install <name>==1.0.0       Install a specific version
    uninstall <name>            Remove an installed skill
    update                      Update all installed skills to latest
    list                        List installed skills
    info <name>                 Show skill details
"""

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

try:
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
except ImportError:
    print("Error: 'packaging' is required. Run: pip install packaging")
    sys.exit(1)

BASE_DIR      = Path(__file__).parent
REGISTRY_PATH = BASE_DIR / "registry.json"
INSTALL_DIR   = BASE_DIR / "skills"


def get_github_raw_base() -> str:
    """Detect the GitHub raw content base URL from git remote origin."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            m = re.match(r"https?://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?$", url)
            if m:
                return f"https://raw.githubusercontent.com/{m.group(1)}/main"
    except Exception:
        pass
    return "https://raw.githubusercontent.com/VitalikRibiy/claude-skills/main"


# -- Registry ------------------------------------------------------------------

def load_registry(remote: bool = False) -> dict:
    """Load the skill registry. If remote=True, fetch latest from GitHub."""
    if remote:
        return _fetch_remote_registry()
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"skills": []}


def _fetch_remote_registry() -> dict:
    """Fetch registry.json from GitHub."""
    url = f"{get_github_raw_base()}/registry.json"
    try:
        with urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except (HTTPError, URLError) as e:
        print(f"    Could not fetch remote registry ({e}), using local copy.")
        return load_registry(remote=False)


def registry_index(registry: dict) -> dict:
    """Return {name: entry} dict from registry."""
    return {s["name"]: s for s in registry.get("skills", [])}


# -- Installed skills ----------------------------------------------------------

def load_installed() -> dict:
    """Return {name: version} of currently installed skills."""
    installed = {}
    if not INSTALL_DIR.exists():
        return installed
    for skill_dir in INSTALL_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8")
        if content.startswith("---"):
            try:
                import yaml
                parts = content.split("---", 2)
                fm = yaml.safe_load(parts[1])
                installed[fm["name"]] = str(fm["version"])
            except Exception:
                pass
    return installed


# -- Dependency resolution -----------------------------------------------------

class DependencyError(Exception):
    pass


def resolve_dependencies(
    target_name: str,
    target_version_spec: str,
    index: dict,
    resolved: dict = None,
    visiting: set = None,
) -> dict:
    if resolved is None:
        resolved = {}
    if visiting is None:
        visiting = set()

    if target_name in visiting:
        cycle = "  ".join(visiting) + f"  {target_name}"
        raise DependencyError(f"Circular dependency detected: {cycle}")

    if target_name not in index:
        raise DependencyError(f"Skill '{target_name}' not found in registry")

    entry             = index[target_name]
    available_version = entry["version"]

    if target_version_spec and target_version_spec != "latest":
        spec = SpecifierSet(target_version_spec)
        if Version(available_version) not in spec:
            raise DependencyError(
                f"Version conflict: '{target_name}' requires {target_version_spec} "
                f"but registry has {available_version}"
            )

    if target_name in resolved:
        if resolved[target_name] != available_version:
            raise DependencyError(
                f"Version conflict: '{target_name}' resolved to both "
                f"{resolved[target_name]} and {available_version}"
            )
        return resolved

    resolved[target_name] = available_version
    visiting.add(target_name)

    for dep in entry.get("depends_on") or []:
        resolve_dependencies(dep["name"], dep.get("version", ""), index, resolved, visiting)

    visiting.remove(target_name)
    return resolved


def topo_sort(install_plan: dict, index: dict) -> list:
    """Return skill names in dependency-first order."""
    order   = []
    visited = set()

    def visit(name: str):
        if name in visited:
            return
        visited.add(name)
        for dep in (index.get(name, {}).get("depends_on") or []):
            visit(dep["name"])
        order.append(name)

    for name in install_plan:
        visit(name)
    return order


# -- Download & install --------------------------------------------------------

def download_skill(name: str, version: str, artifact_url: str) -> Path:
    """Download a .skill archive from GitHub. Returns local path."""
    dest = BASE_DIR / "dist" / f"{name}-{version}.skill"
    dest.parent.mkdir(exist_ok=True)

    if dest.exists():
        print(f"   {name} v{version} already downloaded")
        return dest

    print(f"    Downloading {name} v{version}...")
    try:
        with urlopen(artifact_url, timeout=60) as resp:
            dest.write_bytes(resp.read())
    except HTTPError as e:
        raise RuntimeError(f"Download failed for {name}: HTTP {e.code} {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Download failed for {name}: {e.reason}")

    return dest


def install_from_archive(name: str, archive_path: Path):
    """Extract a .skill archive into skills/<name>/."""
    skill_dir = INSTALL_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(skill_dir)
    print(f"   Installed {name}")


def confirm_plan(action: str, plan_lines: list) -> bool:
    print(f"\n[plan] {action} plan:")
    for line in plan_lines:
        print(f"   {line}")
    answer = input("\nProceed? [Y/n]: ").strip().lower()
    return answer in ("", "y", "yes")


# -- Commands ------------------------------------------------------------------

def cmd_install(args):
    raw   = args.name
    match = re.match(r"^([a-z0-9_-]+)==(.+)$", raw)
    if match:
        name, version_pin = match.group(1), match.group(2)
        version_spec = f"=={version_pin}"
    else:
        name, version_spec = raw, ""

    print(f"\n Resolving dependencies for '{name}'...")
    registry = load_registry(remote=False)
    index    = registry_index(registry)

    try:
        install_plan = resolve_dependencies(name, version_spec, index)
    except DependencyError as e:
        print(f"\n Dependency error: {e}")
        sys.exit(1)

    installed = load_installed()
    to_install = {n: v for n, v in install_plan.items()
                  if n not in installed or installed[n] != v}

    if not to_install:
        print(f" '{name}' and all dependencies are already installed.")
        return

    ordered    = topo_sort(to_install, index)
    plan_lines = [f"+ {n} v{install_plan[n]}" for n in ordered]

    if not confirm_plan("Install", plan_lines):
        print("Cancelled.")
        return

    for skill_name in ordered:
        version = to_install[skill_name]
        entry   = index[skill_name]
        archive = download_skill(skill_name, version, entry["artifact_url"])
        install_from_archive(skill_name, archive)

    print(f"\n Done. Installed {len(ordered)} skill(s).")


def cmd_uninstall(args):
    name      = args.name
    installed = load_installed()

    if name not in installed:
        print(f"'{name}' is not installed.")
        return

    dependents = []
    registry   = load_registry()
    index      = registry_index(registry)
    for other_name in installed:
        if other_name == name:
            continue
        for dep in (index.get(other_name, {}).get("depends_on") or []):
            if dep["name"] == name:
                dependents.append(other_name)

    if dependents:
        print(f"\n  Warning: the following installed skills depend on '{name}':")
        for d in dependents:
            print(f"   - {d}")
        print("   Uninstalling may break them.")

    if not confirm_plan("Uninstall", [f"- {name} v{installed[name]}"]):
        print("Cancelled.")
        return

    skill_dir = INSTALL_DIR / name
    if skill_dir.exists():
        import shutil
        shutil.rmtree(skill_dir)
        print(f" Uninstalled '{name}'.")
    else:
        print(f"  Directory not found: {skill_dir}")


def cmd_update(args):
    installed = load_installed()
    if not installed:
        print("No skills installed.")
        return

    print("\n Checking for updates...")
    registry = load_registry(remote=False)
    index    = registry_index(registry)

    updates = [
        (name, current, index[name]["version"])
        for name, current in installed.items()
        if name in index and Version(index[name]["version"]) > Version(current)
    ]

    if not updates:
        print(" All skills are up to date.")
        return

    plan_lines = [f"  {n}: {cur}  {new}" for n, cur, new in updates]
    if not confirm_plan("Update", plan_lines):
        print("Cancelled.")
        return

    for name, _current, new_version in updates:
        entry   = index[name]
        archive = download_skill(name, new_version, entry["artifact_url"])
        install_from_archive(name, archive)

    print(f"\n Updated {len(updates)} skill(s).")


def cmd_list(args):
    installed = load_installed()
    if not installed:
        print("No skills installed.")
        return

    registry = load_registry(remote=False)
    index    = registry_index(registry)

    print(f"\n{'Skill':<25} {'Installed':<12} {'Latest':<12}")
    print("-" * 50)
    for name in sorted(installed):
        current = installed[name]
        latest  = index.get(name, {}).get("version", "unknown")
        flag    = " (update available)" if (
            latest != "unknown" and Version(latest) > Version(current)
        ) else ""
        print(f"{name:<25} {current:<12} {latest:<12}{flag}")


def cmd_info(args):
    name     = args.name
    registry = load_registry(remote=False)
    index    = registry_index(registry)

    if name not in index:
        print(f"Skill '{name}' not found in registry.")
        sys.exit(1)

    entry     = index[name]
    installed = load_installed()

    print(f"\n{'-' * 60}")
    print(f"  {entry['name']}  v{entry['version']}")
    print(f"{'-' * 60}")
    print(f"\nDescription:\n  {entry['description']}\n")

    deps = entry.get("depends_on") or []
    if deps:
        print("Dependencies:")
        for dep in deps:
            print(f"  - {dep['name']} {dep.get('version', '')}")
    else:
        print("Dependencies: none")

    status = "installed" if name in installed else "not installed"
    print(f"\nStatus: {status}")
    if name in installed:
        current = installed[name]
        latest  = entry["version"]
        if Version(latest) > Version(current):
            print(f"  Installed: v{current}    Update available: v{latest}")
        else:
            print(f"  Version: v{current} (up to date)")
    print()


# -- Entry point ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Claude Skills package manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 skillman.py install agent-orchestrator
  python3 skillman.py install project-workspace==1.0.0
  python3 skillman.py uninstall team-protocol
  python3 skillman.py update
  python3 skillman.py list
  python3 skillman.py info agent-orchestrator
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Install a skill and its dependencies")
    p_install.add_argument("name", help="Skill name (optionally with ==version pin)")

    p_uninstall = sub.add_parser("uninstall", help="Remove an installed skill")
    p_uninstall.add_argument("name", help="Skill name to uninstall")

    sub.add_parser("update", help="Update all installed skills")
    sub.add_parser("list",   help="List installed skills")

    p_info = sub.add_parser("info", help="Show skill details")
    p_info.add_argument("name", help="Skill name")

    args = parser.parse_args()
    dispatch = {
        "install":   cmd_install,
        "uninstall": cmd_uninstall,
        "update":    cmd_update,
        "list":      cmd_list,
        "info":      cmd_info,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
