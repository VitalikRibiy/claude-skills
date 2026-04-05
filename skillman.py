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
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
except ImportError:
    print("Error: 'packaging' is required. Run: pip install packaging")
    sys.exit(1)

BASE_DIR       = Path(__file__).parent
REGISTRY_PATH  = BASE_DIR / "registry.json"
INSTALL_DIR    = BASE_DIR / "skills"

REGISTRY_URL   = "https://raw.githubusercontent.com/VitaliiRibii/claude-skills/main/registry.json"
ADO_ORG        = "VitaliiRibii"
ADO_PROJECT    = "claude-skills"
ADO_FEED       = "claude-skills-feed"


# -- Authentication ------------------------------------------------------------

def get_auth_token() -> str:
    """
    Get an ADO access token.
    Priority: ADO_PAT env var  az account get-access-token  error.
    """
    pat = os.environ.get("ADO_PAT")
    if pat:
        import base64
        token = base64.b64encode(f":{pat}".encode()).decode()
        return f"Basic {token}"

    try:
        result = subprocess.run(
            ["az", "account", "get-access-token",
             "--resource", "499b84ac-1321-427f-aa17-267ca6975798",
             "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"Bearer {result.stdout.strip()}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("\n Authentication failed. Provide credentials using one of these methods:")
    print("   1. Set ADO_PAT environment variable to your Personal Access Token")
    print("      (needs Packaging: Read & Write scope)")
    print("   2. Run: az login")
    print("      then retry  skillman will use your Azure CLI token")
    sys.exit(1)


# -- Registry ------------------------------------------------------------------

def load_registry(remote: bool = False) -> dict:
    """Load the skill registry. If remote=True, fetch from ADO."""
    if remote:
        return _fetch_remote_registry()
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"skills": []}


def _fetch_remote_registry() -> dict:
    """Fetch registry.json from the ADO repo."""
    auth = get_auth_token()
    url = (
        f"https://dev.azure.com/{ADO_ORG}/{ADO_PROJECT}/_apis/git/repositories/"
        f"{ADO_PROJECT}/items?path=/registry.json&api-version=7.1"
    )
    req = Request(url, headers={"Authorization": auth})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except (HTTPError, URLError) as e:
        # Fall back to local registry
        print(f"    Could not fetch remote registry ({e}), using local copy.")
        return load_registry(remote=False)


def registry_index(registry: dict) -> dict[str, dict]:
    """Return {name: entry} dict from registry."""
    return {s["name"]: s for s in registry.get("skills", [])}


# -- Installed skills ----------------------------------------------------------

def load_installed() -> dict[str, str]:
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
    index: dict[str, dict],
    resolved: dict[str, str] = None,
    visiting: set = None,
) -> dict[str, str]:
    """
    Resolve the full dependency tree for a skill.
    Returns {name: version} of everything that needs to be installed.
    Raises DependencyError on circular deps or version conflicts.
    """
    if resolved is None:
        resolved = {}
    if visiting is None:
        visiting = set()

    if target_name in visiting:
        cycle = "  ".join(visiting) + f"  {target_name}"
        raise DependencyError(f"Circular dependency detected: {cycle}")

    if target_name not in index:
        raise DependencyError(f"Skill '{target_name}' not found in registry")

    entry = index[target_name]
    available_version = entry["version"]

    # Check version specifier
    if target_version_spec and target_version_spec != "latest":
        spec = SpecifierSet(target_version_spec)
        if Version(available_version) not in spec:
            raise DependencyError(
                f"Version conflict: '{target_name}' requires {target_version_spec} "
                f"but registry has {available_version}"
            )

    # Check for conflict with already-resolved version
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
        dep_name = dep["name"]
        dep_spec = dep.get("version", "")
        resolve_dependencies(dep_name, dep_spec, index, resolved, visiting)

    visiting.remove(target_name)
    return resolved


def topo_sort(install_plan: dict[str, str], index: dict[str, dict]) -> list[str]:
    """Return skill names in dependency-first order."""
    order = []
    visited = set()

    def visit(name: str):
        if name in visited:
            return
        visited.add(name)
        entry = index.get(name, {})
        for dep in entry.get("depends_on") or []:
            visit(dep["name"])
        order.append(name)

    for name in install_plan:
        visit(name)
    return order


# -- Download & install --------------------------------------------------------

def download_skill(name: str, version: str, artifact_url: str, auth: str) -> Path:
    """Download a .skill archive from ADO Artifacts. Returns local path."""
    dest = BASE_DIR / "dist" / f"{name}-{version}.skill"
    dest.parent.mkdir(exist_ok=True)

    if dest.exists():
        print(f"   {name} v{version} already downloaded")
        return dest

    print(f"    Downloading {name} v{version}...")
    req = Request(artifact_url, headers={"Authorization": auth})
    try:
        with urlopen(req, timeout=60) as resp:
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


def confirm_plan(action: str, plan_lines: list[str]) -> bool:
    """Show the install/uninstall plan and ask for confirmation."""
    print(f"\n[plan] {action} plan:")
    for line in plan_lines:
        print(f"   {line}")
    answer = input("\nProceed? [Y/n]: ").strip().lower()
    return answer in ("", "y", "yes")


# -- Commands ------------------------------------------------------------------

def cmd_install(args):
    raw = args.name
    # Parse optional version pin: name==1.0.0
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
    to_install = {
        n: v for n, v in install_plan.items()
        if n not in installed or installed[n] != v
    }

    if not to_install:
        print(f" '{name}' and all dependencies are already installed.")
        return

    ordered = topo_sort(to_install, index)
    plan_lines = [f"+ {n} v{install_plan[n]}" for n in ordered]

    if not confirm_plan("Install", plan_lines):
        print("Cancelled.")
        return

    auth = get_auth_token()
    for skill_name in ordered:
        version     = to_install[skill_name]
        entry       = index[skill_name]
        archive     = download_skill(skill_name, version, entry["artifact_url"], auth)
        install_from_archive(skill_name, archive)

    print(f"\n Done. Installed {len(ordered)} skill(s).")


def cmd_uninstall(args):
    name = args.name
    installed = load_installed()

    if name not in installed:
        print(f"'{name}' is not installed.")
        return

    # Check if anything installed depends on this skill
    dependents = []
    registry = load_registry()
    index    = registry_index(registry)
    for other_name in installed:
        if other_name == name:
            continue
        entry = index.get(other_name, {})
        for dep in entry.get("depends_on") or []:
            if dep["name"] == name:
                dependents.append(other_name)

    if dependents:
        print(f"\n  Warning: the following installed skills depend on '{name}':")
        for d in dependents:
            print(f"   - {d}")
        print("   Uninstalling may break them.")

    plan_lines = [f"- {name} v{installed[name]}"]
    if not confirm_plan("Uninstall", plan_lines):
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

    updates = []
    for name, current in installed.items():
        if name in index:
            latest = index[name]["version"]
            if Version(latest) > Version(current):
                updates.append((name, current, latest))

    if not updates:
        print(" All skills are up to date.")
        return

    plan_lines = [f"  {n}: {cur}  {new}" for n, cur, new in updates]
    if not confirm_plan("Update", plan_lines):
        print("Cancelled.")
        return

    auth = get_auth_token()
    for name, _current, new_version in updates:
        entry   = index[name]
        archive = download_skill(name, new_version, entry["artifact_url"], auth)
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
    name = args.name
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
