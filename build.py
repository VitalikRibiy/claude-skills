#!/usr/bin/env python3
"""
build.py  Build and package Claude skills into distributable .skill archives.

Usage:
    python3 build.py              # build all skills
    python3 build.py project-workspace team-protocol   # build specific skills
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Run: pip install pyyaml")
    sys.exit(1)

BASE_DIR  = Path(__file__).parent
SKILLS_DIR = BASE_DIR / "skills"
DIST_DIR   = BASE_DIR / "dist"
REGISTRY_PATH = BASE_DIR / "registry.json"

MAX_DESCRIPTION_LENGTH = 1024
ORG = "VitaliiRibii"
FEED = "claude-skills-feed"
PROJECT = "claude-skills"


def parse_skill_frontmatter(skill_dir: Path) -> dict:
    """Read and parse the YAML frontmatter from a skill's SKILL.md."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError(f"{skill_md}: SKILL.md must start with YAML frontmatter (---)")

    # Extract frontmatter between first and second ---
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{skill_md}: Could not find closing --- in frontmatter")

    frontmatter = yaml.safe_load(parts[1])
    return frontmatter


def validate_description(name: str, description: str):
    """Validate description length. Exits with a clear error if too long."""
    length = len(description.strip())
    if length > MAX_DESCRIPTION_LENGTH:
        print(f"\n Build failed: description too long in skill '{name}'")
        print(f"   Length: {length} characters (max: {MAX_DESCRIPTION_LENGTH})")
        print(f"   Trim {length - MAX_DESCRIPTION_LENGTH} characters from the description in SKILL.md")
        sys.exit(1)


def package_skill(skill_dir: Path, frontmatter: dict) -> Path:
    """Package a skill directory into a .skill ZIP archive."""
    name    = frontmatter["name"]
    version = frontmatter["version"]

    DIST_DIR.mkdir(exist_ok=True)
    output_path = DIST_DIR / f"{name}-{version}.skill"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(skill_dir.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(skill_dir)
                zf.write(file_path, arcname)

    return output_path


def artifact_url(name: str, version: str) -> str:
    """Build the ADO Universal Package download URL for a skill."""
    return (
        f"https://pkgs.dev.azure.com/{ORG}/{PROJECT}/_apis/packaging/feeds/"
        f"{FEED}/upack/packages/{name}/versions/{version}"
    )


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"skills": []}


def save_registry(registry: dict):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")


def update_registry(registry: dict, frontmatter: dict):
    """Upsert a skill entry in the registry."""
    name    = frontmatter["name"]
    version = str(frontmatter["version"])
    description = frontmatter.get("description", "").strip()
    depends_on  = frontmatter.get("depends_on") or []

    entry = {
        "name": name,
        "version": version,
        "description": description,
        "depends_on": depends_on,
        "artifact_url": artifact_url(name, version),
    }

    skills = registry.setdefault("skills", [])
    for i, existing in enumerate(skills):
        if existing["name"] == name:
            skills[i] = entry
            return

    skills.append(entry)


def build_skill(skill_dir: Path) -> tuple[str, str, Path]:
    """Build one skill. Returns (name, version, output_path)."""
    frontmatter = parse_skill_frontmatter(skill_dir)

    name        = frontmatter.get("name")
    version     = str(frontmatter.get("version", ""))
    description = (frontmatter.get("description") or "").strip()

    if not name:
        raise ValueError(f"{skill_dir}: 'name' field missing from frontmatter")
    if not version:
        raise ValueError(f"{skill_dir}: 'version' field missing from frontmatter")
    if not description:
        raise ValueError(f"{skill_dir}: 'description' field missing or empty")

    validate_description(name, description)

    output_path = package_skill(skill_dir, frontmatter)
    return name, version, output_path, frontmatter


def main():
    parser = argparse.ArgumentParser(description="Build Claude skill packages")
    parser.add_argument("skills", nargs="*",
                        help="Skill names to build (default: all)")
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print(f"Error: skills/ directory not found at {SKILLS_DIR}")
        sys.exit(1)

    # Determine which skills to build
    if args.skills:
        skill_dirs = []
        for name in args.skills:
            d = SKILLS_DIR / name
            if not d.is_dir():
                print(f"Error: skill directory not found: {d}")
                sys.exit(1)
            skill_dirs.append(d)
    else:
        skill_dirs = sorted(
            d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
        )

    if not skill_dirs:
        print("No skills found to build.")
        sys.exit(0)

    print(f"\nBuilding {len(skill_dirs)} skill(s)...\n")

    registry = load_registry()
    built = []
    errors = []

    for skill_dir in skill_dirs:
        try:
            name, version, output_path, frontmatter = build_skill(skill_dir)
            update_registry(registry, frontmatter)
            built.append((name, version, output_path))
            size_kb = output_path.stat().st_size / 1024
            print(f"  [OK] {name} v{version}  ->  {output_path.name}  ({size_kb:.1f} KB)")
        except SystemExit:
            raise   # propagate validation errors immediately
        except Exception as e:
            errors.append((skill_dir.name, str(e)))
            print(f"  [FAIL] {skill_dir.name}: {e}")

    if errors:
        print(f"\n[FAIL] {len(errors)} skill(s) failed to build.")
        sys.exit(1)

    save_registry(registry)
    print(f"\n[OK] registry.json updated ({len(built)} skills)")

    print(f"""
==================================================
Build complete -- {len(built)} skill(s) packaged

Output directory: {DIST_DIR}
""")
    for name, version, path in built:
        print(f"  {name} v{version}  ->  {path}")
    print()


if __name__ == "__main__":
    main()
