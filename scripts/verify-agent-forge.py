#!/usr/bin/env python3
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
CODEX_HOME = Path.home() / ".codex" / "skills"
CLAUDE_HOME = Path.home() / ".claude"
REQUIRED_SCRIPT_PATHS = [
    ROOT / "scripts" / "bootstrap-project.sh",
    ROOT / "scripts" / "sync-claude-adapters.sh",
    ROOT / "scripts" / "sync-codex-skills.sh",
    ROOT / "scripts" / "deploy-factory.sh",
    ROOT / "scripts" / "factory-export.sh",
]
REQUIRED_DOC_PATHS = [
    ROOT / "docs" / "PORTABILITY.md",
    ROOT / "docs" / "FACTORY_SUITCASE.md",
]
EXECUTABLE_SCRIPT_PATHS = [
    ROOT / "scripts" / "bootstrap-project.sh",
    ROOT / "scripts" / "sync-claude-adapters.sh",
    ROOT / "scripts" / "sync-codex-skills.sh",
    ROOT / "scripts" / "deploy-factory.sh",
    ROOT / "scripts" / "factory-export.sh",
]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def ok(msg: str) -> None:
    print(f"[OK]   {msg}")


def check_symlink(path: Path, expected_target: Path) -> bool:
    if not path.exists() and not path.is_symlink():
      fail(f"Missing target: {path}")
      return False
    if not path.is_symlink():
      fail(f"Expected symlink but found regular path: {path}")
      return False
    actual = path.resolve()
    if actual != expected_target.resolve():
      fail(f"Symlink target mismatch: {path} -> {actual}, expected {expected_target}")
      return False
    ok(f"Symlink OK: {path}")
    return True


def check_executable(path: Path) -> bool:
    if not path.exists():
        fail(f"Missing executable script: {path}")
        return False
    if not path.is_file():
        fail(f"Expected regular executable file: {path}")
        return False
    if path.stat().st_mode & 0o111 == 0:
        fail(f"Script is not executable: {path}")
        return False
    ok(f"Executable script OK: {path}")
    return True


def project_root_by_name(registry: dict) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for project in registry.get("governed_projects", []):
        roots[project["name"]] = ROOT.parent / project["root"]
    return roots


def main() -> int:
    if not REGISTRY_PATH.exists():
        fail(f"Missing registry: {REGISTRY_PATH}")
        return 1

    with REGISTRY_PATH.open() as fh:
        registry = json.load(fh)

    status = 0
    project_roots = project_root_by_name(registry)
    expected_project_skills: dict[str, dict[str, Path]] = {}

    for script_path in REQUIRED_SCRIPT_PATHS:
        if script_path.exists():
            ok(f"Script present: {script_path}")
        else:
            fail(f"Missing required script: {script_path}")
            status = 1

    for script_path in EXECUTABLE_SCRIPT_PATHS:
        if not check_executable(script_path):
            status = 1

    for doc_path in REQUIRED_DOC_PATHS:
        if doc_path.exists():
            ok(f"Doc present: {doc_path}")
        else:
            fail(f"Missing required doc: {doc_path}")
            status = 1

    for entry in registry.get("skills", []):
        canonical_skill = ROOT / entry["canonical_skill"]
        if canonical_skill.exists():
            ok(f"Canonical skill present: {entry['name']}")
        else:
            fail(f"Missing canonical skill file: {canonical_skill}")
            status = 1
            continue

        if "codex" in entry.get("targets", []):
            codex_source = ROOT / entry["codex"]["path"]
            codex_target = CODEX_HOME / entry["name"]
            if not check_symlink(codex_target, codex_source):
                status = 1

        if "claude" in entry.get("targets", []):
            claude = entry["claude"]
            adapter_source = ROOT / claude["path"]
            if adapter_source.exists():
                ok(f"Claude adapter present: {adapter_source}")
            else:
                fail(f"Missing Claude adapter file: {adapter_source}")
                status = 1
                continue

            if entry["scope"] == "global":
                if claude["mode"] == "subagent":
                    target = CLAUDE_HOME / "agents" / adapter_source.name
                else:
                    target = CLAUDE_HOME / "commands" / adapter_source.name
            else:
                project_root = ROOT.parent / entry["project"]
                if claude["mode"] == "subagent":
                    target = project_root / ".claude" / "agents" / adapter_source.name
                else:
                    target = project_root / ".claude" / "commands" / adapter_source.name

            if not check_symlink(target, adapter_source):
                status = 1

        skill_delivery = entry.get("claude_skill")
        if skill_delivery:
            skill_dir = canonical_skill.parent
            for project_name in skill_delivery.get("projects", []):
                expected_project_skills.setdefault(project_name, {})[entry["name"]] = skill_dir

    for project in registry.get("governed_projects", []):
        project_root = project_roots[project["name"]]
        if project_root.exists():
            ok(f"Governed project present: {project['name']}")
        else:
            fail(f"Missing governed project root: {project_root}")
            status = 1
            continue

        for rel_path in project.get("required_files", []):
            target = project_root / rel_path
            if target.exists() or target.is_symlink():
                ok(f"Governance file present: {target}")
            else:
                fail(f"Missing governance file: {target}")
                status = 1

        expected_skills = expected_project_skills.get(project["name"], {})
        if expected_skills:
            skills_target_dir = project_root / ".claude" / "skills"
            if not skills_target_dir.exists():
                fail(f"Missing .claude/skills/ directory: {skills_target_dir}")
                status = 1
                continue

            for skill_name, skill_dir in sorted(expected_skills.items()):
                skill_link = skills_target_dir / skill_name
                if not check_symlink(skill_link, skill_dir):
                    status = 1

            for actual_path in sorted(skills_target_dir.iterdir()):
                if actual_path.name not in expected_skills:
                    fail(f"Unexpected .claude/skills entry for {project['name']}: {actual_path}")
                    status = 1

    for team in registry.get("teams", []):
        manifest = ROOT / team["canonical_manifest"]
        if manifest.exists():
            ok(f"Team manifest present: {team['name']}")
        else:
            fail(f"Missing team manifest: {manifest}")
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
