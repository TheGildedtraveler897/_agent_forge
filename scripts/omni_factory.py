#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = ROOT.parent
PROJECTS_CATALOG_PATH = ROOT / "projects.json"
GLOBAL_MCP_PATH = ROOT / "global-mcp.json"
HOOKS_PATH = ROOT / "policies" / "hooks.json"
MEMORY_POLICY_PATH = ROOT / "policies" / "memory.json"
REGISTRY_PATH = ROOT / "registry.json"
RUNTIME_DIR = ROOT / "runtime"
MANAGED_STATE_PATH = RUNTIME_DIR / "managed-state.json"
KNOWLEDGE_ANCHOR_PATH = ROOT / "docs" / "LESSONS_LEARNED.md"

CLAUDE_COMMAND_MARKER = "Managed by Agent Forge omni-factory"
CLAUDE_AGENT_MARKER = "Managed by Agent Forge omni-factory"
GEMINI_COMMAND_MARKER = "agent_forge_managed = true"
CODEX_AGENT_MARKER = "agent_forge_managed = true"
MARKDOWN_MANAGED_COMMENT = "<!-- Managed by Agent Forge omni-factory. Do not edit by hand. -->"
BOOTSTRAP_REPLACE_MARKER = "Managed by Agent Forge bootstrap. The sync script will replace this stub."
CAPABILITY_TARGETS = ("claude", "codex", "gemini")


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    root: Path
    required_files: list[str]
    trusted_workspace: bool = False


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    description: str
    skill_path: Path
    skill_dir: Path
    scope: str
    project: str | None
    capability_class: str
    delivery_projects: list[str]
    hosts: list[str]
    context_cost: str | None
    model_tier: str | None
    claude_command_name: str | None
    gemini_command_name: str | None
    codex_sandbox_mode: str | None
    requires_mcp_servers: list[str]

    @property
    def is_workflow(self) -> bool:
        return self.capability_class == "workflow"

    @property
    def is_expert(self) -> bool:
        return self.capability_class == "expert"

    @property
    def relative_skill_path(self) -> str:
        return self.skill_path.relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "none"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        # Handle unquoted lists: [a, b, c]
        content = value[1:-1].strip()
        if not content:
            return []
        return [item.strip().strip("'").strip('"') for item in content.split(",")]
    if value.startswith(("{", "'", '"')) or value.lstrip("-").isdigit():
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError, NameError):
            return value
    return value


def parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}
    metadata: dict[str, Any] = {}
    for raw_line in lines[1:]:
        line = raw_line.rstrip()
        if line.strip() == "---":
            break
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = parse_scalar(value)
    return metadata


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def toml_string(value: str) -> str:
    return f'"{toml_escape(value)}"'


def toml_multiline(value: str) -> str:
    return '"""\n' + value.rstrip() + "\n\"\"\""


def relpath(from_dir: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, from_dir)


def home_projects_reference(path: Path) -> str:
    relative = path.relative_to(PROJECTS_ROOT)
    return f"~/Projects/{relative.as_posix()}"


def knowledge_anchor_read_path(from_dir: Path) -> str:
    return relpath(from_dir, KNOWLEDGE_ANCHOR_PATH)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_managed_state() -> dict[str, Any]:
    if not MANAGED_STATE_PATH.exists():
        return {}
    return json.loads(MANAGED_STATE_PATH.read_text())


def save_managed_state(state: dict[str, Any]) -> None:
    MANAGED_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANAGED_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def mark_managed(state: dict[str, Any], path: Path, kind: str) -> None:
    state[str(path)] = {"kind": kind, "updated_at": utc_now()}


def unmark_managed(state: dict[str, Any], path: Path) -> None:
    state.pop(str(path), None)


def is_managed_path(state: dict[str, Any], path: Path) -> bool:
    return str(path) in state


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    existing = path.read_text() if path.exists() else None
    if existing != content:
        path.write_text(content)


def write_text_if_missing(path: Path, content: str) -> None:
    ensure_parent(path)
    if not path.exists():
        path.write_text(content)


def write_managed_text(path: Path, content: str, kind: str, state: dict[str, Any]) -> None:
    if path.exists() and not is_managed_path(state, path):
        if path.is_file():
            existing = path.read_text()
            if existing == content:
                mark_managed(state, path, kind)
                return
            if BOOTSTRAP_REPLACE_MARKER in existing:
                write_text(path, content)
                mark_managed(state, path, kind)
                return
        raise RuntimeError(f"Refusing to overwrite unmanaged file: {path}")
    write_text(path, content)
    mark_managed(state, path, kind)


def remove_managed_text(path: Path, state: dict[str, Any]) -> None:
    if path.exists() and is_managed_path(state, path):
        path.unlink()
    unmark_managed(state, path)


def ensure_symlink(target: Path, source: Path) -> None:
    ensure_parent(target)
    if target.exists() or target.is_symlink():
        if not target.is_symlink():
            raise RuntimeError(f"Refusing to replace non-symlink target: {target}")
        actual = target.resolve()
        if actual == source.resolve():
            return
        target.unlink()
    target.symlink_to(source)


def sync_symlink_dir(target_dir: Path, desired: dict[str, Path]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, source in desired.items():
        ensure_symlink(target_dir / name, source)

    for existing in target_dir.iterdir():
        if existing.name in desired:
            continue
        if existing.is_symlink():
            existing.unlink()


def sync_managed_dir(target_dir: Path, desired: dict[str, str], marker: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, content in desired.items():
        path = target_dir / name
        if path.is_symlink():
            path.unlink()
        if path.exists() and not path.is_file():
            raise RuntimeError(f"Expected regular file target: {path}")
        if path.exists() and path.is_file():
            existing = path.read_text()
            if existing != content and marker not in existing:
                raise RuntimeError(f"Refusing to overwrite unmanaged file: {path}")
        write_text(path, content)

    for existing in target_dir.iterdir():
        if existing.name in desired:
            continue
        if existing.is_symlink():
            existing.unlink()
            continue
        if existing.is_file() and marker in existing.read_text():
            existing.unlink()


def _all_governed_project_names() -> list[str]:
    data = load_json(PROJECTS_CATALOG_PATH)
    return [entry["name"] for entry in data.get("governed_projects", [])]


def _resolve_project_root(project_name: str, projects_root: Path) -> Path:
    data = load_json(PROJECTS_CATALOG_PATH)
    for entry in data.get("governed_projects", []):
        if entry["name"] == project_name:
            return projects_root / entry["root"]
    return projects_root / project_name


def discover_capabilities() -> list[Capability]:
    capabilities: list[Capability] = []
    all_governed = _all_governed_project_names()
    for skill_path in sorted(ROOT.glob("skills/**/SKILL.md")):
        meta = parse_frontmatter(skill_path.read_text())
        capability_id = skill_path.parent.name
        relative_parts = skill_path.relative_to(ROOT).parts
        if relative_parts[:2] == ("skills", "global"):
            scope = "global"
            project = None
        else:
            scope = "project-local"
            project = relative_parts[2]

        capability_class = meta.get("capability_class")
        if capability_class not in {"workflow", "expert", "reference"}:
            raise RuntimeError(f"{skill_path} is missing capability_class")

        hosts = list(meta.get("targets") or meta.get("hosts") or ["claude", "codex", "gemini"])

        raw_delivery = meta.get("delivery_projects")
        if raw_delivery is None:
            delivery_projects = list(all_governed) if project is None else [project]
        elif list(raw_delivery) == ["*"]:
            delivery_projects = list(all_governed)
        else:
            delivery_projects = list(raw_delivery)
        capabilities.append(
            Capability(
                capability_id=capability_id,
                name=str(meta.get("name") or capability_id),
                description=str(meta.get("description") or ""),
                skill_path=skill_path,
                skill_dir=skill_path.parent,
                scope=scope,
                project=project,
                capability_class=capability_class,
                delivery_projects=delivery_projects,
                hosts=hosts,
                context_cost=meta.get("context_cost"),
                model_tier=meta.get("model_tier"),
                claude_command_name=meta.get("claude_command_name"),
                gemini_command_name=meta.get("gemini_command_name"),
                codex_sandbox_mode=meta.get("codex_sandbox_mode"),
                requires_mcp_servers=list(meta.get("requires_mcp_servers") or []),
            )
        )
    return capabilities


def validate_skill_frontmatter() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for skill_path in sorted(ROOT.glob("skills/**/SKILL.md")):
        meta = parse_frontmatter(skill_path.read_text())
        rel = skill_path.relative_to(ROOT).as_posix()
        capability_id = skill_path.parent.name

        name = meta.get("name")
        if not name:
            errors.append(f"{rel} frontmatter missing required field 'name'")
        elif name != capability_id:
            errors.append(f"{rel} frontmatter name '{name}' must match folder '{capability_id}'")

        description = meta.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{rel} frontmatter missing required field 'description'")

        capability_class = meta.get("capability_class")
        if capability_class not in {"workflow", "expert", "reference"}:
            errors.append(f"{rel} frontmatter missing or invalid 'capability_class'")

        targets = meta.get("targets")
        hosts = meta.get("hosts")
        if targets is None and hosts is None:
            errors.append(f"{rel} frontmatter missing required field 'targets'")
            continue
        if targets is None and hosts is not None:
            warnings.append(f"{rel} uses legacy 'hosts'; prefer canonical 'targets'")
            targets = hosts
        if not isinstance(targets, list) or not targets or not all(isinstance(item, str) for item in targets):
            errors.append(f"{rel} frontmatter 'targets' must be a non-empty string list")
            continue
        invalid_targets = [target for target in targets if target not in CAPABILITY_TARGETS]
        if invalid_targets:
            errors.append(f"{rel} frontmatter has invalid targets: {invalid_targets}")

    return errors, warnings


def load_projects() -> list[ProjectSpec]:
    data = load_json(PROJECTS_CATALOG_PATH)
    projects: list[ProjectSpec] = []
    for entry in data.get("governed_projects", []):
        projects.append(
            ProjectSpec(
                name=entry["name"],
                root=PROJECTS_ROOT / entry["root"],
                required_files=list(entry.get("required_files") or []),
                trusted_workspace=bool(entry.get("trusted_workspace", False)),
            )
        )
    return projects


def load_team_entries() -> list[dict[str, Any]]:
    teams: list[dict[str, Any]] = []
    for path in sorted((ROOT / "teams").glob("*.json")):
        data = load_json(path)
        teams.append(
            {
                "name": data["name"],
                "canonical_manifest": path.relative_to(ROOT).as_posix(),
                "purpose": data.get("summary", ""),
                "roles": [role["name"] for role in data.get("roles", [])],
            }
        )
    return teams


def validate_team_manifest_references(capabilities: list[Capability]) -> list[str]:
    errors: list[str] = []
    global_skill_ids = {capability.capability_id for capability in capabilities if capability.scope == "global"}
    project_skill_ids = {capability.capability_id for capability in capabilities if capability.scope == "project-local"}
    mapping_keys = ("claude_mapping", "codex_mapping", "gemini_mapping")

    for path in sorted((ROOT / "teams").glob("*.json")):
        data = load_json(path)
        rel = path.relative_to(ROOT).as_posix()
        for mapping_key in mapping_keys:
            preferred = (data.get(mapping_key) or {}).get("preferred_entries") or []
            if not isinstance(preferred, list):
                errors.append(f"{rel} {mapping_key}.preferred_entries must be a list")
                continue
            for entry in preferred:
                if entry in global_skill_ids:
                    continue
                if entry in project_skill_ids:
                    errors.append(
                        f"{rel} {mapping_key}.preferred_entries references project-local skill '{entry}'"
                    )
                else:
                    errors.append(
                        f"{rel} {mapping_key}.preferred_entries references unknown skill '{entry}'"
                    )

    return errors


def build_registry(capabilities: list[Capability], projects: list[ProjectSpec]) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    for capability in capabilities:
        entry: dict[str, Any] = {
            "name": capability.capability_id,
            "display_name": capability.name,
            "scope": capability.scope,
            "project": capability.project,
            "capability_class": capability.capability_class,
            "canonical_skill": capability.relative_skill_path,
            "targets": capability.hosts,
            "delivery_projects": capability.delivery_projects,
        }
        if "claude" in capability.hosts:
            mode = "skill" if capability.is_workflow else "agent"
            entry["claude"] = {
                "mode": mode,
                "generated": True,
                "command_name": capability.claude_command_name or capability.capability_id if capability.is_workflow else None,
                "agent_name": capability.capability_id if capability.is_expert else None,
            }
        if "gemini" in capability.hosts:
            mode = "skill" if capability.is_workflow else "agent"
            entry["gemini"] = {
                "mode": mode,
                "generated": True,
                "command_name": capability.gemini_command_name or capability.capability_id if capability.is_workflow else None,
                "agent_name": capability.capability_id if capability.is_expert else None,
            }
        if "codex" in capability.hosts:
            entry["codex"] = {
                "generated": True,
                "global_skill": capability.scope == "global",
                "project_skill": capability.scope == "project-local" or bool(capability.delivery_projects),
                "custom_agent": capability.is_expert,
            }
        skills.append(entry)

    return {
        "version": 5,
        "generated_from": {
            "projects": "projects.json",
            "capabilities": "skills/**/SKILL.md",
            "teams": "teams/*.json",
            "mcp": "global-mcp.json",
        },
        "governed_projects": [
            {
                "name": project.name,
                "root": project.root.relative_to(PROJECTS_ROOT).as_posix(),
                "required_files": project.required_files,
            }
            for project in projects
        ],
        "skills": skills,
        "teams": load_team_entries(),
    }


def skill_read_path_for_project(project_root: Path, capability: Capability) -> str:
    return relpath(project_root, capability.skill_path)


def skill_read_path_for_home(home_dir: Path, capability: Capability) -> str:
    del home_dir
    return home_projects_reference(capability.skill_path)


def render_claude_command(capability: Capability, read_path: str) -> str:
    command_name = capability.claude_command_name or capability.capability_id
    return (
        "---\n"
        f"description: {capability.description}\n"
        "argument-hint: [optional focus]\n"
        "---\n"
        f"{MARKDOWN_MANAGED_COMMENT}\n\n"
        f"Use the canonical Agent Forge capability `{capability.capability_id}`.\n\n"
        f"Before acting, read `{read_path}` and treat it as the source of truth.\n"
        "Follow that skill's workflow, guardrails, and output contract.\n\n"
        f"Operator entrypoint: `/{command_name}`\n"
    )


def render_claude_agent(capability: Capability, read_path: str) -> str:
    return (
        "---\n"
        f"name: {capability.capability_id}\n"
        f"description: {capability.description}\n"
        "---\n"
        f"{MARKDOWN_MANAGED_COMMENT}\n\n"
        f"You are the `{capability.capability_id}` specialist.\n\n"
        f"Before doing any work, read `{read_path}`.\n"
        "Treat that canonical skill as the durable capability contract.\n"
        "Apply the skill's doctrine and stay inside its scope.\n"
    )


def render_gemini_command(capability: Capability, read_path: str) -> str:
    return (
        f"{GEMINI_COMMAND_MARKER}\n"
        f'description = {toml_string(capability.description)}\n'
        "prompt = "
        + toml_multiline(
            "\n".join(
                [
                    f"Use the canonical Agent Forge capability `{capability.capability_id}`.",
                    f"Before acting, read `{read_path}` and treat it as the source of truth.",
                    "Follow that skill's workflow, constraints, and output contract.",
                ]
            )
        )
        + "\n"
    )


def render_gemini_agent(capability: Capability, read_path: str) -> str:
    return (
        "---\n"
        f"name: {capability.capability_id}\n"
        f"description: {capability.description}\n"
        "---\n"
        f"{MARKDOWN_MANAGED_COMMENT}\n\n"
        f"You are the `{capability.capability_id}` specialist.\n"
        f"Before doing any work, read `{read_path}`.\n"
        "Treat that canonical skill as the source of truth and stay inside its scope.\n"
    )


def render_codex_agent(capability: Capability, project_root: Path) -> str:
    skill_path = relpath(project_root / ".codex" / "agents", capability.skill_path)
    lessons_path = knowledge_anchor_read_path(project_root / ".codex" / "agents")
    sandbox_mode = capability.codex_sandbox_mode or ("workspace-write" if capability.project else "read-only")
    instructions = "\n".join(
        [
            f"Use the canonical Agent Forge capability `{capability.capability_id}`.",
            f"Before acting, read `{skill_path}` and follow it as the source of truth.",
            f"When prior workaround history matters, read `{lessons_path}` before generalizing a fix.",
            "Respect repo AGENTS.md and durable project docs when they are more specific.",
            "Stay inside the capability scope and avoid unrelated work.",
        ]
    )
    return (
        f"{CODEX_AGENT_MARKER}\n"
        f'name = {toml_string(capability.capability_id)}\n'
        f'description = {toml_string(capability.description)}\n'
        f'sandbox_mode = {toml_string(sandbox_mode)}\n'
        f"developer_instructions = {toml_multiline(instructions)}\n\n"
        "[[skills.config]]\n"
        f"path = {toml_string(skill_path)}\n"
        "enabled = true\n"
    )


def render_project_gemini_md(project_root: Path) -> str:
    raw_imports = [
        relpath(project_root, ROOT / "AGENTS.md"),
        relpath(project_root, KNOWLEDGE_ANCHOR_PATH),
        "AGENTS.md",
        "docs/CONOPS.md",
        "docs/HANDOFF.md",
    ]
    if _memory_sections() and (project_root / "MEMORY.md").exists():
        raw_imports.append("MEMORY.md")
    imports = list(dict.fromkeys(raw_imports))
    lines = [MARKDOWN_MANAGED_COMMENT, "", "# Agent Forge Gemini Context", ""]
    lines.extend(f"@{item}" for item in imports)
    lines.append("")
    return "\n".join(lines)


def render_global_gemini_md() -> str:
    return "\n".join(
        [
            MARKDOWN_MANAGED_COMMENT,
            "",
            "# Agent Forge Global Gemini Context",
            "",
            "Use this as the thin global Gemini layer. Project-local `GEMINI.md` files remain the primary context surface.",
            "",
            "@../Projects/_agent_forge/AGENTS.md",
            "@../Projects/_agent_forge/docs/LESSONS_LEARNED.md",
            "",
        ]
    )


MCP_TARGETS = ("claude", "codex", "gemini")
MCP_SCOPES = ("user", "project", "shared")
MCP_TRANSPORT_TYPES = ("stdio", "streamable_http", "sse")
MCP_AUTH_MODES = ("none", "bearer", "oauth")
MCP_TRUST_MODES = ("local", "remote-trusted", "remote-sandboxed")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if value == "*":
        return ["*"]
    if isinstance(value, list):
        return value
    return [value]


def mcp_server_alias(prefix: str) -> str:
    return prefix.replace(".", "-")


def _expand_transport_paths(transport: dict[str, Any]) -> dict[str, Any]:
    """Expand ${HOME}, $HOME, and ~ in transport command/args at render time.

    The canonical global-mcp.json uses ${HOME}-style placeholders so the file
    is portable across operator workstations. Expansion happens here, against
    the renderer's environment, so the rendered host configs (Claude .mcp.json,
    Codex .codex/config.toml, Gemini .gemini/settings.json) contain absolute
    paths that work on the operator's machine without needing a shell wrapper.

    This is what removes the Windows blocker: prior canonical args invoked
    `sh -c "exec python3 ..."` to get $HOME expansion at runtime; native
    Windows has no `sh`, so we pre-expand at render and invoke python3 directly.
    """
    result = dict(transport)
    if "command" in result and isinstance(result["command"], str):
        result["command"] = os.path.expanduser(os.path.expandvars(result["command"]))
    if "args" in result and isinstance(result["args"], list):
        result["args"] = [
            os.path.expanduser(os.path.expandvars(arg)) if isinstance(arg, str) else arg
            for arg in result["args"]
        ]
    if "cwd" in result and isinstance(result["cwd"], str):
        result["cwd"] = os.path.expanduser(os.path.expandvars(result["cwd"]))
    return result


def normalize_mcp_server(server_id: str, server: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    prefix = str(server.get("prefix") or server_id)
    tool_filter = list(server.get("tool_filter") or server.get("tool_allow") or [])
    trust = str(server.get("trust") or ("remote-trusted" if server.get("trust_server") else "local"))
    bearer_token_env_var = (
        server.get("bearer_token_env_var")
        or server.get("bearer_token_env")
        or (server.get("transport") or {}).get("bearer_token_env_var")
    )
    merged = {
        "id": server_id,
        "server_alias": str(server.get("server_alias") or mcp_server_alias(prefix)),
        "prefix": prefix,
        "description": server.get("description", ""),
        "scope": server.get("scope", "project"),
        "projects": _as_list(server.get("projects")),
        "targets": list(server.get("targets") or MCP_TARGETS),
        "transport": _expand_transport_paths(dict(server.get("transport") or {})),
        "auth": server.get("auth", "none"),
        "trust": trust,
        "env_passthrough": list(server.get("env_passthrough") or []),
        "env_optional": list(server.get("env_optional") or []),
        "env_literal": dict(server.get("env_literal") or {}),
        "headers": dict(server.get("headers") or {}),
        "env_headers": dict(server.get("env_headers") or server.get("env_http_headers") or {}),
        "bearer_token_env_var": bearer_token_env_var,
        "tool_filter": tool_filter,
        "tool_allow": tool_filter,
        "tool_deny": list(server.get("tool_deny") or []),
        "required": server.get("required", defaults.get("required", False)),
        "trust_server": server.get("trust_server", defaults.get("trust_server", False)),
        "parallel_safe": server.get("parallel_safe", defaults.get("parallel_safe", False)),
        "startup_timeout_ms": server.get("startup_timeout_ms", defaults.get("startup_timeout_ms", 20000)),
        "tool_timeout_ms": server.get("tool_timeout_ms", defaults.get("tool_timeout_ms", 60000)),
    }
    return merged


def load_mcp_servers() -> list[dict[str, Any]]:
    payload = load_json(GLOBAL_MCP_PATH)
    defaults = payload.get("defaults") or {}
    servers: list[dict[str, Any]] = []
    for server_id, server in sorted((payload.get("servers") or {}).items()):
        servers.append(normalize_mcp_server(server_id, server, defaults))
    return servers


def project_is_trusted(project_name: str) -> bool:
    for project in load_projects():
        if project.name == project_name:
            return project.trusted_workspace
    return False


def mcp_server_requires_trusted_workspace(server: dict[str, Any]) -> bool:
    transport_type = (server.get("transport") or {}).get("type")
    return (
        server.get("scope") == "project"
        or str(server.get("trust", "")).startswith("remote")
        or transport_type in {"streamable_http", "sse"}
    )


def mcp_server_selected_for_project(server: dict[str, Any], project_name: str) -> bool:
    scope = server["scope"]
    projects = server["projects"]
    if scope not in {"project", "shared"}:
        return False
    if projects and "*" not in projects and project_name not in projects:
        return False
    if mcp_server_requires_trusted_workspace(server) and not project_is_trusted(project_name):
        return False
    return True


def project_mcp_servers(project_name: str, host: str | None = None) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for server in load_mcp_servers():
        if host is not None and host not in server["targets"]:
            continue
        if mcp_server_selected_for_project(server, project_name):
            selected.append(server)
    return selected


def user_mcp_servers(host: str | None = None) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for server in load_mcp_servers():
        if server["scope"] != "user":
            continue
        if host is not None and host not in server["targets"]:
            continue
        selected.append(server)
    return selected


def validate_mcp_inventory() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    payload = load_json(GLOBAL_MCP_PATH)
    version = payload.get("version")
    if version != 2:
        errors.append(f"global-mcp.json unsupported version: {version}")
        return errors, warnings

    seen_prefixes: dict[str, str] = {}
    projects = {project.name: project for project in load_projects()}
    servers = load_mcp_servers()
    for server in servers:
        if not server.get("prefix"):
            errors.append(f"global-mcp.json[{server['id']}] missing prefix")
        elif server["prefix"] in seen_prefixes:
            errors.append(
                f"global-mcp.json duplicate prefix '{server['prefix']}' for "
                f"{seen_prefixes[server['prefix']]} and {server['id']}"
            )
        else:
            seen_prefixes[server["prefix"]] = server["id"]

        if server["scope"] not in MCP_SCOPES:
            errors.append(f"global-mcp.json[{server['id']}] invalid scope '{server['scope']}'")
        if any(target not in MCP_TARGETS for target in server["targets"]):
            errors.append(f"global-mcp.json[{server['id']}] invalid targets {server['targets']}")
        if server["auth"] not in MCP_AUTH_MODES:
            errors.append(f"global-mcp.json[{server['id']}] invalid auth '{server['auth']}'")
        if server["trust"] not in MCP_TRUST_MODES:
            errors.append(f"global-mcp.json[{server['id']}] invalid trust '{server['trust']}'")

        transport = server["transport"]
        transport_type = transport.get("type")
        if transport_type not in MCP_TRANSPORT_TYPES:
            errors.append(f"global-mcp.json[{server['id']}] invalid transport type '{transport_type}'")
        elif transport_type == "stdio":
            if not transport.get("command"):
                errors.append(f"global-mcp.json[{server['id']}] stdio transport missing command")
        elif transport_type in {"streamable_http", "sse"}:
            if not (transport.get("http_url") or transport.get("url")):
                errors.append(f"global-mcp.json[{server['id']}] {transport_type} transport missing url")

        if "gemini" in server["targets"] and "_" in server["server_alias"]:
            errors.append(
                f"global-mcp.json[{server['id']}] server alias '{server['server_alias']}' "
                "contains '_' which Gemini CLI cannot namespace safely"
            )

        if any(not isinstance(name, str) for name in server["tool_filter"]):
            errors.append(f"global-mcp.json[{server['id']}] tool_filter must contain only strings")

        if server["auth"] == "bearer" and not server.get("bearer_token_env_var") and not transport.get("bearer_token_env_var"):
            warnings.append(f"global-mcp.json[{server['id']}] bearer auth has no bearer_token_env_var")

        required_env = [
            name for name in server["env_passthrough"]
            if name not in set(server["env_optional"])
        ]
        if server["scope"] in {"project", "shared"}:
            candidate_projects = server["projects"]
            if not candidate_projects or "*" in candidate_projects:
                candidate_projects = list(projects.keys())
            for project_name in candidate_projects:
                project = projects.get(project_name)
                if project is None:
                    errors.append(f"global-mcp.json[{server['id']}] references unknown project '{project_name}'")
                    continue
                if mcp_server_requires_trusted_workspace(server) and not project.trusted_workspace:
                    errors.append(
                        f"global-mcp.json[{server['id']}] cannot emit to untrusted project '{project_name}'"
                    )
            for env_name in required_env:
                if env_name not in os.environ:
                    warnings.append(
                        f"global-mcp.json[{server['id']}] env_passthrough '{env_name}' is unset"
                    )

    return errors, warnings


HOOK_TARGETS = ("claude", "codex", "gemini")
HOOK_HANDLER_TYPES = ("command", "http", "mcp_tool", "prompt", "agent")

_EVENT_ALIASES: dict[str, dict[str, str | None]] = {
    "claude": {
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "permission_request": "PermissionRequest",
        "permission_denied": "PermissionDenied",
        "post_tool_use_failure": "PostToolUseFailure",
        "post_tool_batch": "PostToolBatch",
        "user_prompt_submit": "UserPromptSubmit",
        "user_prompt_expansion": "UserPromptExpansion",
        "notification": "Notification",
        "subagent_start": "SubagentStart",
        "subagent_stop": "SubagentStop",
        "task_created": "TaskCreated",
        "task_completed": "TaskCompleted",
        "stop_failure": "StopFailure",
        "teammate_idle": "TeammateIdle",
        "instructions_loaded": "InstructionsLoaded",
        "config_change": "ConfigChange",
        "cwd_changed": "CwdChanged",
        "file_changed": "FileChanged",
        "worktree_create": "WorktreeCreate",
        "worktree_remove": "WorktreeRemove",
        "pre_compact": "PreCompact",
        "post_compact": "PostCompact",
        "elicitation": "Elicitation",
        "elicitation_result": "ElicitationResult",
        "session_end": "SessionEnd",
        "pre_commit": "PreToolUse",
        "post_edit": "PostToolUse",
        "session_start": "SessionStart",
        "stop": "Stop",
        "before_agent": None,
        "after_agent": None,
        "before_model": None,
        "after_model": None,
        "before_tool_selection": None,
    },
    "codex": {
        # Codex hook docs use PascalCase event keys in hooks.json. Keep this
        # allow-list aligned with the public event table; aliases set to None
        # mean the canonical event is not supported by Codex.
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "permission_request": "PermissionRequest",
        "user_prompt_submit": "UserPromptSubmit",
        "session_start": "SessionStart",
        "stop": "Stop",
        "subagent_start": "SubagentStart",
        "subagent_stop": "SubagentStop",
        "pre_compact": "PreCompact",
        "post_compact": "PostCompact",
        "pre_commit": "PreToolUse",
        "post_edit": "PostToolUse",
        "permission_denied": None,
        "post_tool_use_failure": None,
        "post_tool_batch": None,
        "user_prompt_expansion": None,
        "notification": None,
        "task_created": None,
        "task_completed": None,
        "stop_failure": None,
        "teammate_idle": None,
        "instructions_loaded": None,
        "config_change": None,
        "cwd_changed": None,
        "file_changed": None,
        "worktree_create": None,
        "worktree_remove": None,
        "elicitation": None,
        "elicitation_result": None,
        "session_end": None,
        "before_agent": None,
        "after_agent": None,
        "before_model": None,
        "after_model": None,
        "before_tool_selection": None,
    },
    "gemini": {
        # Corrected 2026-04-25 (Sprint 1 / C1 fix). Gemini CLI v0.39 expects
        # PascalCase event names (BeforeTool/AfterTool/SessionStart/SessionEnd),
        # not the camelCase preToolUse/postToolUse pattern that Claude uses.
        # The pre-fix aliases produced rendered settings whose event keys were
        # never recognized by Gemini's hook dispatcher, so seeded hooks
        # (including telemetry-guardian) silently never fired on Gemini.
        # See docs/PATHFINDER_LEDGER.md §2.3 and PATHFINDER_ROADMAP.md C1.
        "pre_tool_use": "BeforeTool",
        "post_tool_use": "AfterTool",
        "pre_commit": "BeforeTool",
        "post_edit": "AfterTool",
        "session_start": "SessionStart",
        "session_end": "SessionEnd",
        "stop": "SessionEnd",
        "before_agent": "BeforeAgent",
        "after_agent": "AfterAgent",
        "before_model": "BeforeModel",
        "after_model": "AfterModel",
        "before_tool_selection": "BeforeToolSelection",
        "notification": "Notification",
        "pre_compact": "PreCompress",
        "permission_request": None,
        "permission_denied": None,
        "post_tool_use_failure": None,
        "post_tool_batch": None,
        "user_prompt_submit": None,
        "user_prompt_expansion": None,
        "subagent_start": None,
        "subagent_stop": None,
        "task_created": None,
        "task_completed": None,
        "stop_failure": None,
        "teammate_idle": None,
        "instructions_loaded": None,
        "config_change": None,
        "cwd_changed": None,
        "file_changed": None,
        "worktree_create": None,
        "worktree_remove": None,
        "post_compact": None,
        "elicitation": None,
        "elicitation_result": None,
    },
}


CANONICAL_HOOK_EVENTS = frozenset(
    event for aliases in _EVENT_ALIASES.values() for event in aliases
)


def native_hook_event(host: str, event: str) -> str | None:
    aliases = _EVENT_ALIASES.get(host)
    if aliases is None:
        raise KeyError(f"unknown hook host: {host}")
    return aliases.get(event)


def normalize_hook_record(record: dict[str, Any], bucket: str) -> dict[str, Any]:
    handler = record.get("handler")
    if handler is None and record.get("command"):
        handler = {"type": "command", "command": record["command"]}
    if not isinstance(handler, dict):
        handler = {}

    if "targets" in record:
        targets = list(record.get("targets") or [])
    elif bucket in HOOK_TARGETS:
        targets = [bucket]
    else:
        targets = list(HOOK_TARGETS)

    normalized = dict(record)
    normalized["handler"] = dict(handler)
    normalized["targets"] = targets
    normalized["enabled"] = bool(record.get("enabled", True))
    return normalized


def _all_hook_records(include_disabled: bool = False) -> list[dict[str, Any]]:
    payload = load_json(HOOKS_PATH)
    records: list[dict[str, Any]] = []
    for bucket in ("shared", "claude", "codex", "gemini"):
        for record in (payload.get(bucket) or []):
            normalized = normalize_hook_record(record, bucket)
            normalized["_bucket"] = bucket
            if include_disabled or normalized["enabled"]:
                records.append(normalized)
    return records


def _hooks_for_host(host: str, include_disabled: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in _all_hook_records(include_disabled=include_disabled):
        if not record["enabled"] and not include_disabled:
            continue
        if host in record.get("targets", []):
            out.append(record)
    return out


def hook_command_script_path(command: str) -> Path | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if len(parts) < 2:
        return None
    runner = Path(parts[0]).name
    if runner not in {"bash", "python", "python3"}:
        return None
    return Path(os.path.expanduser(parts[1]))


def _timeout_seconds(timeout_ms: int | None) -> int | None:
    if not timeout_ms:
        return None
    return max(1, int((timeout_ms + 999) / 1000))


def _render_claude_handler(hook: dict[str, Any]) -> dict[str, Any]:
    handler = hook["handler"]
    handler_type = handler.get("type")
    rendered: dict[str, Any] = {"type": handler_type}
    if hook.get("if"):
        rendered["if"] = hook["if"]
    if hook.get("status_message"):
        rendered["statusMessage"] = hook["status_message"]
    timeout = _timeout_seconds(hook.get("timeout_ms"))
    if timeout:
        rendered["timeout"] = timeout

    if handler_type == "command":
        rendered["command"] = handler.get("command", "")
        if hook.get("async"):
            rendered["async"] = True
        if hook.get("async_rewake"):
            rendered["async"] = True
            rendered["asyncRewake"] = True
    elif handler_type == "http":
        rendered["url"] = handler.get("url", "")
        if handler.get("headers"):
            rendered["headers"] = handler["headers"]
        if handler.get("allowed_env_vars"):
            rendered["allowedEnvVars"] = handler["allowed_env_vars"]
    elif handler_type == "mcp_tool":
        rendered["server"] = handler.get("server", "")
        rendered["tool"] = handler.get("tool", "")
        if handler.get("input"):
            rendered["input"] = handler["input"]
    elif handler_type in {"prompt", "agent"}:
        rendered["prompt"] = handler.get("prompt", "")
        if handler_type == "prompt" and handler.get("model"):
            rendered["model"] = handler["model"]
    return rendered


def _render_command_handler_for_host(hook: dict[str, Any], host: str) -> dict[str, Any] | None:
    handler = hook["handler"]
    if handler.get("type") != "command":
        return None

    if host == "gemini":
        rendered: dict[str, Any] = {
            "type": "command",
            "command": handler.get("command", ""),
            "name": hook.get("id", ""),
        }
        if hook.get("timeout_ms"):
            rendered["timeout"] = hook["timeout_ms"]
        if hook.get("description"):
            rendered["description"] = hook["description"]
        return rendered

    rendered = {
        "type": "command",
        "command": handler.get("command", ""),
    }
    if hook.get("status_message"):
        rendered["statusMessage"] = hook["status_message"]
    timeout = _timeout_seconds(hook.get("timeout_ms"))
    if timeout:
        rendered["timeout"] = timeout
    return rendered


def codex_hook_payload() -> dict[str, Any]:
    hooks = _hooks_for_host("codex")
    grouped: dict[str, list[dict[str, Any]]] = {"hooks": {}}
    for hook in hooks:
        event = native_hook_event("codex", hook["event"])
        handler = _render_command_handler_for_host(hook, "codex")
        if event is None or handler is None:
            continue
        grouped["hooks"].setdefault(event, []).append(
            {
                "matcher": hook.get("matcher", ""),
                "hooks": [handler],
            }
        )
    return grouped


def claude_hook_payload() -> dict[str, list[dict[str, Any]]]:
    hooks = _hooks_for_host("claude")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hook in hooks:
        native_event = native_hook_event("claude", hook["event"])
        if native_event is None:
            continue
        entry: dict[str, Any] = {
            "matcher": hook.get("matcher", ""),
            "hooks": [_render_claude_handler(hook)],
        }
        grouped.setdefault(native_event, []).append(entry)
    return grouped


def gemini_hook_payload() -> dict[str, list[dict[str, Any]]]:
    hooks = _hooks_for_host("gemini")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hook in hooks:
        native_event = native_hook_event("gemini", hook["event"])
        handler = _render_command_handler_for_host(hook, "gemini")
        if native_event is None or handler is None:
            continue
        entry: dict[str, Any] = {
            "matcher": hook.get("matcher", ""),
            "hooks": [handler],
        }
        if "sequential" in hook:
            entry["sequential"] = bool(hook["sequential"])
        grouped.setdefault(native_event, []).append(entry)
    return grouped


def _memory_sections() -> list[dict[str, Any]]:
    if not MEMORY_POLICY_PATH.exists():
        return []
    payload = load_json(MEMORY_POLICY_PATH)
    return list(payload.get("sections") or [])


def _memory_policy() -> dict[str, Any]:
    if not MEMORY_POLICY_PATH.exists():
        return {}
    return load_json(MEMORY_POLICY_PATH)


def _memory_bridge_policy() -> dict[str, Any]:
    bridge = _memory_policy().get("bridge") or {}
    return dict(bridge) if isinstance(bridge, dict) else {}


def memory_bridge_enabled() -> bool:
    return bool(_memory_bridge_policy().get("enabled", False))


def memory_bridge_hosts() -> list[str]:
    return list(_memory_bridge_policy().get("hosts") or [])


def claude_memory_bridge_project_slug(project_root: Path) -> str:
    return str(project_root.resolve()).replace("/", "-")


def memory_bridge_native_target(project_root: Path, host: str) -> Path:
    if host == "claude":
        return Path.home() / ".claude" / "projects" / claude_memory_bridge_project_slug(project_root) / "memory" / "MEMORY.md"
    if host == "codex":
        return project_root / ".codex" / "memory" / "AGENTS_MEMORY.md"
    if host == "gemini":
        return project_root / ".gemini" / "memory" / "MEMORY.md"
    raise ValueError(f"unknown memory bridge host: {host}")


def render_bridge_state(project_root: Path) -> str:
    hosts = memory_bridge_hosts()
    state = {
        "version": 1,
        "last_outbound": {},
        "last_inbound": {},
        "last_outbound_hash": {},
        "last_inbound_diff_hash": {},
        "imported_entry_hashes": {},
        "native_targets": {
            host: str(memory_bridge_native_target(project_root, host))
            for host in hosts
        },
        "last_errors": {},
    }
    return json.dumps(state, indent=2, sort_keys=True) + "\n"


def render_memory_md(project_root: Path) -> str:
    sections = _memory_sections()
    lines = [
        MARKDOWN_MANAGED_COMMENT,
        "",
        "# Project Memory",
        "",
        f"Universal cross-host session-state layer for `{project_root.name}`. "
        "Renderers translate `policies/memory.json` into this file and the sibling `.forge_state/` directory.",
        "",
        "Append-first by default. Use the `memory-archivist` skill to add entries; never edit anchor lines by hand. "
        "Secrets, credentials, and machine-local residue are denied at write time per `policies/memory.json`.",
        "",
    ]
    for section in sections:
        section_id = section["id"]
        name = section.get("name") or section_id
        description = section.get("description") or ""
        append_only = section.get("append_only", True)
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"<!-- section:{section_id} -->")
        if description:
            lines.append(f"_{description}_")
        if not append_only:
            lines.append("")
            lines.append("_Rewriteable section — entries reflect current state, not history._")
        lines.append("")
        lines.append("<!-- entries:start -->")
        lines.append("<!-- entries:end -->")
        lines.append("")
    return "\n".join(lines)


def render_forge_state_readme() -> str:
    return "\n".join(
        [
            MARKDOWN_MANAGED_COMMENT,
            "",
            "# .forge_state",
            "",
            "Local working state for the universal memory layer. Companion to the project's `MEMORY.md`.",
            "",
            "- `manifest.json` — schema version, section list, and last-updated timestamp.",
            "- `archivist.log` — append-only audit trail produced by the `memory-archivist` skill.",
            "- `bridge.json` — mutable memory bridge state for host-local synchronization.",
            "- `bridge.log` — append-only JSONL audit trail produced by the `memory-bridge` skill.",
            "",
            "This directory is factory-managed. Do not edit `manifest.json` by hand; use the `memory-archivist` skill or re-run `python3 scripts/omni_factory.py sync-claude --project <name>` (or `sync-codex` / `sync-gemini`).",
            "",
        ]
    )


def render_forge_state_manifest(project_root: Path) -> str:
    policy = _memory_policy()
    manifest = {
        "version": policy.get("version", 1),
        "project": project_root.name,
        "sections": [
            {
                "id": s["id"],
                "name": s.get("name") or s["id"],
                "append_only": s.get("append_only", True),
            }
            for s in _memory_sections()
        ],
        "retention": policy.get("retention", {}),
        "secrets_policy": policy.get("secrets_policy", "deny"),
        "last_updated": utc_now(),
    }
    bridge = policy.get("bridge")
    if bridge:
        manifest["bridge"] = bridge
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def sync_memory(project_root: Path, state: dict[str, Any]) -> None:
    """Write MEMORY.md and .forge_state/ for a single governed project. Idempotent."""
    if not _memory_sections():
        return
    memory_path = project_root / "MEMORY.md"
    if memory_path.exists() and not is_managed_path(state, memory_path):
        return
    write_managed_text(memory_path, render_memory_md(project_root), "memory-md", state)
    forge_dir = project_root / ".forge_state"
    write_managed_text(forge_dir / "README.md", render_forge_state_readme(), "forge-state-readme", state)
    write_managed_text(forge_dir / "manifest.json", render_forge_state_manifest(project_root), "forge-state-manifest", state)
    if memory_bridge_enabled():
        write_text_if_missing(forge_dir / "bridge.json", render_bridge_state(project_root))
        write_text_if_missing(forge_dir / "bridge.log", "")


def render_claude_project_mcp(project_name: str) -> str | None:
    servers = project_mcp_servers(project_name, host="claude")
    if not servers:
        return None
    payload = {"mcpServers": {}}
    for server in servers:
        transport = server["transport"]
        entry: dict[str, Any] = {
            "description": server["description"],
        }
        env_map = {key: f"${key}" for key in server["env_passthrough"]}
        env_map.update(server["env_literal"])
        if transport.get("type") == "stdio":
            entry.update(
                {
                    "type": "stdio",
                    "command": transport.get("command"),
                    "args": transport.get("args", []),
                    **({"cwd": transport["cwd"]} if transport.get("cwd") else {}),
                }
            )
        elif transport.get("type") == "streamable_http":
            entry["type"] = "http"
            entry["url"] = transport.get("http_url") or transport.get("url")
        elif transport.get("type") == "sse":
            entry["type"] = "sse"
            entry["url"] = transport.get("url")
        if server["headers"]:
            entry["headers"] = server["headers"]
        if env_map:
            entry["env"] = env_map
        payload["mcpServers"][server["server_alias"]] = entry
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_gemini_settings(project_name: str) -> str:
    settings: dict[str, Any] = {
        "context": {
            "fileName": "GEMINI.md",
        }
    }
    servers = project_mcp_servers(project_name, host="gemini")
    if servers:
        settings["mcpServers"] = {}
        for server in servers:
            transport = server["transport"]
            entry: dict[str, Any] = {
                "description": server["description"],
                "timeout": server["tool_timeout_ms"],
                "trust": server["trust_server"],
            }
            if transport.get("type") == "stdio":
                entry["command"] = transport.get("command")
                if transport.get("args"):
                    entry["args"] = transport["args"]
                env_map = {key: f"${key}" for key in server["env_passthrough"]}
                env_map.update(server["env_literal"])
                if env_map:
                    entry["env"] = env_map
                if transport.get("cwd"):
                    entry["cwd"] = transport["cwd"]
            elif transport.get("type") == "streamable_http":
                entry["httpUrl"] = transport.get("http_url") or transport.get("url")
            elif transport.get("type") == "sse":
                entry["url"] = transport.get("url")
            if server["headers"]:
                entry["headers"] = server["headers"]
            if server["tool_deny"]:
                entry["excludeTools"] = server["tool_deny"]
            if server["tool_filter"]:
                entry["includeTools"] = server["tool_filter"]
            settings["mcpServers"][server["server_alias"]] = entry
    gemini_hooks = gemini_hook_payload()
    if gemini_hooks:
        settings["hooks"] = gemini_hooks
    return json.dumps(settings, indent=2, sort_keys=True) + "\n"


def render_codex_config(project_name: str, project_root: Path, capabilities: list[Capability]) -> str:
    lines = [
        "# Managed by Agent Forge omni-factory. Do not edit by hand.",
        "",
        "[agents]",
        "max_threads = 4",
        "max_depth = 1",
    ]

    if _hooks_for_host("codex"):
        lines.extend(["", "[features]", "hooks = true"])

    relevant_ids = set()
    for capability in capabilities:
        relevant_ids.update(capability.requires_mcp_servers)

    for server in project_mcp_servers(project_name, host="codex"):
        if relevant_ids and server["id"] not in relevant_ids:
            continue
        lines.extend(["", f"[mcp_servers.{server['server_alias']}]"])
        transport = server["transport"]
        if transport.get("type") == "stdio":
            if transport.get("command"):
                lines.append(f"command = {toml_string(transport['command'])}")
            if transport.get("args"):
                args = ", ".join(toml_string(item) for item in transport["args"])
                lines.append(f"args = [{args}]")
            if transport.get("cwd"):
                lines.append(f"cwd = {toml_string(transport['cwd'])}")
        elif transport.get("type") == "streamable_http":
            url = transport.get("http_url") or transport.get("url")
            lines.append(f"url = {toml_string(url)}")
            bearer_env = server.get("bearer_token_env_var") or transport.get("bearer_token_env_var")
            if bearer_env:
                lines.append(f"bearer_token_env_var = {toml_string(bearer_env)}")
        elif transport.get("type") == "sse":
            lines.append(f"url = {toml_string(transport['url'])}")
        lines.append(f"required = {'true' if server['required'] else 'false'}")
        lines.append(f"supports_parallel_tool_calls = {'true' if server['parallel_safe'] else 'false'}")
        lines.append(f"startup_timeout_sec = {max(1, server['startup_timeout_ms'] // 1000)}")
        lines.append(f"tool_timeout_sec = {max(1, server['tool_timeout_ms'] // 1000)}")
        if server["tool_filter"]:
            items = ", ".join(toml_string(item) for item in server["tool_filter"])
            lines.append(f"enabled_tools = [{items}]")
        if server["tool_deny"]:
            items = ", ".join(toml_string(item) for item in server["tool_deny"])
            lines.append(f"disabled_tools = [{items}]")
        if server["env_passthrough"]:
            items = ", ".join(toml_string(item) for item in server["env_passthrough"])
            lines.append(f"env_vars = [{items}]")
        if server["env_literal"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".env]")
            for key, value in server["env_literal"].items():
                lines.append(f"{key} = {toml_string(value)}")
        if server["headers"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".http_headers]")
            for key, value in server["headers"].items():
                lines.append(f"{key} = {toml_string(value)}")
        if server["env_headers"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".env_http_headers]")
            for key, value in server["env_headers"].items():
                lines.append(f"{key} = {toml_string(value)}")
    lines.append("")
    return "\n".join(lines)


def render_user_codex_mcp_block() -> str:
    servers = user_mcp_servers(host="codex")
    if not servers:
        return ""
    lines = [
        "# BEGIN AGENT FORGE MCP",
        "# Generated by Agent Forge omni-factory.",
    ]
    for server in servers:
        lines.extend(["", f"[mcp_servers.{server['server_alias']}]"])
        transport = server["transport"]
        if transport.get("type") == "stdio":
            if transport.get("command"):
                lines.append(f"command = {toml_string(transport['command'])}")
            if transport.get("args"):
                args = ", ".join(toml_string(item) for item in transport["args"])
                lines.append(f"args = [{args}]")
            if transport.get("cwd"):
                lines.append(f"cwd = {toml_string(transport['cwd'])}")
        elif transport.get("type") == "streamable_http":
            url = transport.get("http_url") or transport.get("url")
            lines.append(f"url = {toml_string(url)}")
            bearer_env = server.get("bearer_token_env_var") or transport.get("bearer_token_env_var")
            if bearer_env:
                lines.append(f"bearer_token_env_var = {toml_string(bearer_env)}")
        elif transport.get("type") == "sse":
            lines.append(f"url = {toml_string(transport['url'])}")
        lines.append(f"required = {'true' if server['required'] else 'false'}")
        lines.append(f"supports_parallel_tool_calls = {'true' if server['parallel_safe'] else 'false'}")
        lines.append(f"startup_timeout_sec = {max(1, server['startup_timeout_ms'] // 1000)}")
        lines.append(f"tool_timeout_sec = {max(1, server['tool_timeout_ms'] // 1000)}")
        if server["tool_filter"]:
            items = ", ".join(toml_string(item) for item in server["tool_filter"])
            lines.append(f"enabled_tools = [{items}]")
        if server["tool_deny"]:
            items = ", ".join(toml_string(item) for item in server["tool_deny"])
            lines.append(f"disabled_tools = [{items}]")
        if server["env_passthrough"]:
            items = ", ".join(toml_string(item) for item in server["env_passthrough"])
            lines.append(f"env_vars = [{items}]")
        if server["env_literal"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".env]")
            for key, value in server["env_literal"].items():
                lines.append(f"{key} = {toml_string(value)}")
        if server["headers"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".http_headers]")
            for key, value in server["headers"].items():
                lines.append(f"{key} = {toml_string(value)}")
        if server["env_headers"]:
            lines.append("[mcp_servers." + server["server_alias"] + ".env_http_headers]")
            for key, value in server["env_headers"].items():
                lines.append(f"{key} = {toml_string(value)}")
    lines.extend(["", "# END AGENT FORGE MCP", ""])
    return "\n".join(lines)


def merge_managed_toml_block(path: Path, block: str) -> None:
    if not block:
        return
    ensure_parent(path)
    existing = path.read_text() if path.exists() else ""
    start_marker = "# BEGIN AGENT FORGE MCP"
    end_marker = "# END AGENT FORGE MCP"
    if start_marker in existing and end_marker in existing:
        prefix = existing.split(start_marker, 1)[0].rstrip()
        suffix = existing.split(end_marker, 1)[1].lstrip()
        new_text = prefix + ("\n\n" if prefix else "") + block + suffix
    else:
        new_text = existing.rstrip()
        if new_text:
            new_text += "\n\n"
        new_text += block
    write_text(path, new_text)


def sync_claude(project_name: str | None, projects_root: Path, claude_home: Path) -> None:
    capabilities = discover_capabilities()
    user_agents: dict[str, str] = {}
    user_commands: dict[str, str] = {}
    user_skills: dict[str, Path] = {}
    for capability in capabilities:
        if capability.scope != "global" or "claude" not in capability.hosts:
            continue
        user_skills[capability.capability_id] = capability.skill_dir
        read_path = skill_read_path_for_home(claude_home / "commands", capability)
        if capability.is_workflow:
            name = f"{capability.claude_command_name or capability.capability_id}.md"
            user_commands[name] = render_claude_command(capability, read_path)
        elif capability.is_expert:
            name = f"{capability.capability_id}.md"
            user_agents[name] = render_claude_agent(capability, read_path)

    sync_symlink_dir(claude_home / "skills", user_skills)
    sync_managed_dir(claude_home / "commands", user_commands, CLAUDE_COMMAND_MARKER)
    sync_managed_dir(claude_home / "agents", user_agents, CLAUDE_AGENT_MARKER)

    if project_name:
        project_root = _resolve_project_root(project_name, projects_root)
        if not project_root.exists():
            raise RuntimeError(f"Project root not found: {project_root}")
        project_agents: dict[str, str] = {}
        project_commands: dict[str, str] = {}
        desired_skills: dict[str, Path] = {}
        for capability in capabilities:
            if "claude" not in capability.hosts:
                continue
            if capability.project == project_name:
                read_path = skill_read_path_for_project(project_root, capability)
                if capability.is_workflow:
                    name = f"{capability.claude_command_name or capability.capability_id}.md"
                    project_commands[name] = render_claude_command(capability, read_path)
                elif capability.is_expert:
                    name = f"{capability.capability_id}.md"
                    project_agents[name] = render_claude_agent(capability, read_path)
            if project_name in capability.delivery_projects:
                desired_skills[capability.capability_id] = capability.skill_dir

        sync_managed_dir(project_root / ".claude" / "commands", project_commands, CLAUDE_COMMAND_MARKER)
        sync_managed_dir(project_root / ".claude" / "agents", project_agents, CLAUDE_AGENT_MARKER)
        sync_symlink_dir(project_root / ".claude" / "skills", desired_skills)

        state = load_managed_state()
        sync_memory(project_root, state)
        mcp_payload = render_claude_project_mcp(project_name)
        mcp_path = project_root / ".mcp.json"
        if mcp_payload:
            write_managed_text(mcp_path, mcp_payload, "claude-project-mcp", state)
        else:
            remove_managed_text(mcp_path, state)

        claude_hooks = claude_hook_payload()
        claude_settings_path = project_root / ".claude" / "settings.json"
        if claude_hooks:
            claude_settings_payload = json.dumps({"hooks": claude_hooks}, indent=2, sort_keys=True) + "\n"
            write_managed_text(claude_settings_path, claude_settings_payload, "claude-project-settings", state)
        else:
            remove_managed_text(claude_settings_path, state)
        save_managed_state(state)


def sync_codex(project_name: str | None, projects_root: Path, codex_home: Path, target_skills: Path | None = None) -> None:
    capabilities = discover_capabilities()
    user_skill_target = target_skills or (Path.home() / ".agents" / "skills")
    user_skills: dict[str, Path] = {}
    for capability in capabilities:
        if capability.scope == "global" and "codex" in capability.hosts:
            user_skills[capability.capability_id] = capability.skill_dir
    sync_symlink_dir(user_skill_target, user_skills)
    merge_managed_toml_block(codex_home / "config.toml", render_user_codex_mcp_block())

    if not project_name:
        return

    project_root = _resolve_project_root(project_name, projects_root)
    if not project_root.exists():
        raise RuntimeError(f"Project root not found: {project_root}")

    desired_project_skills: dict[str, Path] = {}
    desired_agents: dict[str, str] = {}
    relevant_capabilities: list[Capability] = []
    for capability in capabilities:
        if "codex" not in capability.hosts:
            continue
        if capability.project == project_name or project_name in capability.delivery_projects:
            desired_project_skills[capability.capability_id] = capability.skill_dir
            relevant_capabilities.append(capability)
            if capability.is_expert:
                desired_agents[f"{capability.capability_id}.toml"] = render_codex_agent(capability, project_root)

    sync_symlink_dir(project_root / ".agents" / "skills", desired_project_skills)
    sync_managed_dir(project_root / ".codex" / "agents", desired_agents, CODEX_AGENT_MARKER)

    state = load_managed_state()
    sync_memory(project_root, state)
    config_path = project_root / ".codex" / "config.toml"
    write_managed_text(config_path, render_codex_config(project_name, project_root, relevant_capabilities), "codex-project-config", state)

    hooks_payload = codex_hook_payload()
    hooks_path = project_root / ".codex" / "hooks.json"
    if hooks_payload["hooks"]:
        write_managed_text(hooks_path, json.dumps(hooks_payload, indent=2, sort_keys=True) + "\n", "codex-project-hooks", state)
    else:
        remove_managed_text(hooks_path, state)
    save_managed_state(state)


def sync_gemini(project_name: str | None, projects_root: Path, gemini_home: Path) -> None:
    capabilities = discover_capabilities()
    user_skills: dict[str, Path] = {}
    user_commands: dict[str, str] = {}
    user_agents: dict[str, str] = {}
    workflow_ids: list[str] = []

    for capability in capabilities:
        if capability.scope != "global" or "gemini" not in capability.hosts:
            continue
        
        # Unify global skills in ~/.agents/skills (the open standard path)
        user_skills[capability.capability_id] = capability.skill_dir
        
        read_path = skill_read_path_for_home(gemini_home, capability)
        if capability.is_workflow:
            workflow_ids.append(capability.capability_id)
            name = f"{capability.gemini_command_name or capability.capability_id}.toml"
            user_commands[name] = render_gemini_command(capability, read_path)
        elif capability.is_expert:
            name = f"{capability.capability_id}.md"
            user_agents[name] = render_gemini_agent(capability, read_path)

    # Deploy all global skills to the shared ~/.agents/skills path
    sync_symlink_dir(Path.home() / ".agents" / "skills", user_skills)
    
    # Purge redundant ~/.gemini/skills to avoid host-level conflicts
    sync_symlink_dir(gemini_home / "skills", {})
    
    sync_managed_dir(gemini_home / "commands", user_commands, GEMINI_COMMAND_MARKER)
    sync_managed_dir(gemini_home / "agents", user_agents, MARKDOWN_MANAGED_COMMENT)

    # Manage ~/.gemini/settings.json to disable workflow skills and avoid command conflicts
    settings_path = gemini_home / "settings.json"
    if settings_path.exists():
        settings = load_json(settings_path)
        if "skills" not in settings:
            settings["skills"] = {}
        
        # Use the name field if present, fallback to ID, as Gemini CLI uses the name for discovery
        disabled_names = set()
        for cap in capabilities:
            if cap.scope == "global" and cap.is_workflow and "gemini" in cap.hosts:
                disabled_names.add(cap.name)
        
        current_disabled = set(settings["skills"].get("disabled", []))
        new_disabled = current_disabled.union(disabled_names)
        
        if current_disabled != new_disabled:
            settings["skills"]["disabled"] = sorted(list(new_disabled))
            write_text(settings_path, json.dumps(settings, indent=2) + "\n")

    state = load_managed_state()
    global_gemini_md = gemini_home / "GEMINI.md"
    try:
        write_managed_text(global_gemini_md, render_global_gemini_md(), "gemini-global-context", state)
    except RuntimeError as exc:
        print(f"Skipping unmanaged Gemini global context: {exc}")
    save_managed_state(state)

    if not project_name:
        return

    project_root = _resolve_project_root(project_name, projects_root)
    if not project_root.exists():
        raise RuntimeError(f"Project root not found: {project_root}")

    desired_skills: dict[str, Path] = {}
    project_commands: dict[str, str] = {}
    project_agents: dict[str, str] = {}
    for capability in capabilities:
        if "gemini" not in capability.hosts:
            continue
        if project_name in capability.delivery_projects:
            desired_skills[capability.capability_id] = capability.skill_dir
        if capability.project == project_name:
            read_path = skill_read_path_for_project(project_root, capability)
            if capability.is_workflow:
                name = f"{capability.gemini_command_name or capability.capability_id}.toml"
                project_commands[name] = render_gemini_command(capability, read_path)
            elif capability.is_expert:
                name = f"{capability.capability_id}.md"
                project_agents[name] = render_gemini_agent(capability, read_path)

    sync_symlink_dir(project_root / ".gemini" / "skills", desired_skills)
    sync_managed_dir(project_root / ".gemini" / "commands", project_commands, GEMINI_COMMAND_MARKER)
    sync_managed_dir(project_root / ".gemini" / "agents", project_agents, MARKDOWN_MANAGED_COMMENT)

    state = load_managed_state()
    sync_memory(project_root, state)
    write_managed_text(project_root / "GEMINI.md", render_project_gemini_md(project_root), "gemini-project-context", state)
    write_managed_text(project_root / ".gemini" / "settings.json", render_gemini_settings(project_name), "gemini-project-settings", state)
    save_managed_state(state)


def verify() -> int:
    status = 0

    def ok(message: str) -> None:
        print(f"[OK]   {message}")

    def fail(message: str) -> None:
        nonlocal status
        print(f"[FAIL] {message}")
        status = 1

    def warn(message: str) -> None:
        print(f"[WARN] {message}")

    required_paths = [
        ROOT / "scripts" / "bootstrap-project.sh",
        ROOT / "scripts" / "bootstrap-workstation.sh",
        ROOT / "scripts" / "deploy-and-bootstrap.sh",
        ROOT / "scripts" / "deploy-factory.sh",
        ROOT / "scripts" / "factory-export.sh",
        ROOT / "scripts" / "sync-claude-adapters.sh",
        ROOT / "scripts" / "sync-codex-skills.sh",
        ROOT / "scripts" / "sync-gemini-adapters.sh",
        ROOT / "scripts" / "verify-agent-forge.py",
        ROOT / "scripts" / "validate-codex-runtime.py",
        ROOT / "scripts" / "omni_factory.py",
        ROOT / "projects.json",
        ROOT / "global-mcp.json",
        ROOT / "policies" / "hooks.json",
        ROOT / "CLAUDE.md",
        ROOT / "GEMINI.md",
        ROOT / "docs" / "CONOPS.md",
        ROOT / "docs" / "HOST_INTEGRATIONS.md",
        ROOT / "docs" / "TRIAD_RUNTIME_VALIDATION.md",
        ROOT / "docs" / "LESSONS_LEARNED.md",
        ROOT / "runtime" / "validation-matrix.json",
        ROOT / "evals" / "scorecard.schema.json",
    ]
    for path in required_paths:
        if path.exists():
            ok(f"Present: {path.relative_to(ROOT)}")
        else:
            fail(f"Missing required path: {path.relative_to(ROOT)}")

    skill_metadata_errors, skill_metadata_warnings = validate_skill_frontmatter()
    for message in skill_metadata_errors:
        fail(message)
    for message in skill_metadata_warnings:
        warn(message)

    capabilities: list[Capability] = []
    try:
        capabilities = discover_capabilities()
    except Exception as exc:
        fail(f"Capability discovery failed: {exc}")
    else:
        for skill in capabilities:
            ok(f"Capability metadata OK: {skill.capability_id}")

    if capabilities:
        generated_registry = build_registry(capabilities, load_projects())
        if REGISTRY_PATH.exists():
            current = load_json(REGISTRY_PATH)
            if current == generated_registry:
                ok("registry.json matches generated compatibility registry")
            else:
                fail("registry.json is out of date with canonical omni-factory sources")
        else:
            fail("Missing registry.json")

    try:
        errors, warnings = validate_mcp_inventory()
    except Exception as exc:
        fail(f"global-mcp.json validation failed to run: {exc}")
    else:
        if not errors:
            ok("global-mcp.json inventory valid")
        for message in errors:
            fail(message)
        for message in warnings:
            warn(message)

    for message in validate_team_manifest_references(capabilities):
        fail(message)

    for team in load_team_entries():
        ok(f"Team manifest present: {team['name']}")

    for project in load_projects():
        if project.root.exists():
            ok(f"Governed project present: {project.name}")
        else:
            fail(f"Missing governed project root: {project.root}")
            continue
        for rel_name in project.required_files:
            target = project.root / rel_name
            if target.exists() or target.is_symlink():
                ok(f"Governance file present: {project.name}/{rel_name}")
            else:
                fail(f"Missing governance file: {project.name}/{rel_name}")

    legacy_paths = [
        ROOT / "claude",
        ROOT / "docs" / "CLAUDE_NATIVE.md",
        ROOT / "docs" / "CLAUDE_VALIDATION_RUN.md",
    ]
    for path in legacy_paths:
        if path.exists():
            fail(f"Legacy residue should be removed: {path.relative_to(ROOT)}")
        else:
            ok(f"Legacy residue removed: {path.relative_to(ROOT)}")

    try:
        hooks_payload = load_json(HOOKS_PATH)
    except Exception as exc:
        fail(f"policies/hooks.json does not parse: {exc}")
    else:
        ok("policies/hooks.json parses")
        if hooks_payload.get("version") == 2:
            warn("policies/hooks.json is schema v2; v3 handler records are preferred")
        elif hooks_payload.get("version") != 3:
            fail(f"policies/hooks.json unsupported version: {hooks_payload.get('version')}")
        for bucket in ("shared", "claude", "codex", "gemini"):
            for hook in (hooks_payload.get(bucket) or []):
                normalized = normalize_hook_record(hook, bucket)
                for key in ("id", "event"):
                    if not normalized.get(key):
                        fail(f"hooks.json[{bucket}] record missing '{key}': {hook}")

                event = normalized.get("event")
                if event and event not in CANONICAL_HOOK_EVENTS:
                    fail(f"hooks.json[{bucket}] unknown canonical event '{event}': {hook}")

                targets = normalized.get("targets") or []
                bad_targets = [target for target in targets if target not in HOOK_TARGETS]
                if bad_targets:
                    fail(f"hooks.json[{bucket}] invalid targets {bad_targets}: {hook}")
                if normalized["enabled"] and not targets:
                    fail(f"hooks.json[{bucket}] enabled record has no targets: {hook}")

                handler = normalized.get("handler") or {}
                handler_type = handler.get("type")
                if handler_type not in HOOK_HANDLER_TYPES:
                    fail(f"hooks.json[{bucket}] invalid handler.type '{handler_type}': {hook}")
                    continue

                if normalized.get("async_rewake") and not normalized.get("async"):
                    fail(f"hooks.json[{bucket}] async_rewake requires async=true: {hook}")
                if normalized.get("async") and handler_type != "command":
                    warn(f"hooks.json[{bucket}] async ignored for non-command hook: {normalized.get('id')}")

                for target in targets:
                    native_event = native_hook_event(target, event) if event else None
                    if native_event is None and normalized["enabled"]:
                        warn(f"hooks.json[{bucket}] {normalized.get('id')} event '{event}' is unsupported on {target}; renderer skips it")
                    if handler_type != "command" and target in {"codex", "gemini"} and normalized["enabled"]:
                        warn(f"hooks.json[{bucket}] {normalized.get('id')} handler '{handler_type}' is unsupported on {target}; renderer skips it")

                if handler_type == "command":
                    cmd = (handler.get("command") or "").strip()
                    if not cmd:
                        fail(f"hooks.json[{bucket}] command handler missing command: {hook}")
                        continue
                    if not normalized["enabled"]:
                        continue
                    script_path = hook_command_script_path(cmd)
                    if script_path is not None:
                        resolved = script_path
                        if not resolved.exists():
                            fail(f"hooks.json '{normalized.get('id')}' command script missing: {resolved}")
                        else:
                            ok(f"Hook script present: {normalized.get('id')} -> {resolved.relative_to(Path.home()) if resolved.is_relative_to(Path.home()) else resolved}")
                elif handler_type == "http":
                    if not handler.get("url"):
                        fail(f"hooks.json[{bucket}] http handler missing url: {hook}")
                elif handler_type == "mcp_tool":
                    if not handler.get("server") or not handler.get("tool"):
                        fail(f"hooks.json[{bucket}] mcp_tool handler missing server/tool: {hook}")
                elif handler_type in {"prompt", "agent"}:
                    if not handler.get("prompt"):
                        fail(f"hooks.json[{bucket}] {handler_type} handler missing prompt: {hook}")

    if MEMORY_POLICY_PATH.exists():
        try:
            memory_payload = load_json(MEMORY_POLICY_PATH)
        except Exception as exc:
            fail(f"policies/memory.json does not parse: {exc}")
        else:
            ok("policies/memory.json parses")
            version = memory_payload.get("version")
            if version not in {1, 2}:
                fail(f"policies/memory.json unsupported version: {version}")
            section_ids = [s.get("id") for s in (memory_payload.get("sections") or [])]
            if not section_ids:
                fail("policies/memory.json has no sections")
            bridge_policy = memory_payload.get("bridge") or {}
            bridge_enabled = bool(bridge_policy.get("enabled", False))
            if bridge_policy:
                allowed_hosts = set(HOOK_TARGETS)
                hosts = bridge_policy.get("hosts") or []
                bad_hosts = [host for host in hosts if host not in allowed_hosts]
                if bad_hosts:
                    fail(f"policies/memory.json bridge has invalid hosts: {bad_hosts}")
                for key in ("enabled", "hosts", "outbound_event", "inbound_event", "conflict_policy", "secrets_policy_inheritance"):
                    if key not in bridge_policy:
                        fail(f"policies/memory.json bridge missing key '{key}'")
                if bridge_policy.get("outbound_event") != "session_start":
                    fail("policies/memory.json bridge outbound_event must be session_start")
                if bridge_policy.get("inbound_event") != "stop":
                    fail("policies/memory.json bridge inbound_event must be stop")
                if bridge_policy.get("conflict_policy") != "append-first":
                    fail("policies/memory.json bridge conflict_policy must be append-first")
                if bridge_policy.get("secrets_policy_inheritance") != "deny":
                    fail("policies/memory.json bridge secrets_policy_inheritance must be deny")
                if bridge_enabled and set(hosts) != set(HOOK_TARGETS):
                    fail("policies/memory.json bridge enabled hosts must include claude, codex, and gemini")
            for project in load_projects():
                project_root = project.root
                memory_md = project_root / "MEMORY.md"
                if not memory_md.exists():
                    fail(f"Memory surface missing: {memory_md.relative_to(PROJECTS_ROOT)}")
                    continue
                body = memory_md.read_text()
                missing_anchors = [sid for sid in section_ids if f"<!-- section:{sid} -->" not in body]
                if missing_anchors:
                    fail(f"Memory surface missing anchors {missing_anchors}: {memory_md.relative_to(PROJECTS_ROOT)}")
                else:
                    ok(f"Memory surface present: {memory_md.relative_to(PROJECTS_ROOT)}")
                manifest_path = project_root / ".forge_state" / "manifest.json"
                if not manifest_path.exists():
                    fail(f"Forge state manifest missing: {manifest_path.relative_to(PROJECTS_ROOT)}")
                    continue
                try:
                    manifest = load_json(manifest_path)
                except Exception as exc:
                    fail(f"Forge state manifest does not parse: {manifest_path.relative_to(PROJECTS_ROOT)}: {exc}")
                    continue
                for key in ("version", "sections", "last_updated"):
                    if key not in manifest:
                        fail(f"Forge state manifest missing key '{key}': {manifest_path.relative_to(PROJECTS_ROOT)}")
                        break
                else:
                    ok(f"Forge state manifest valid: {manifest_path.relative_to(PROJECTS_ROOT)}")
                if bridge_enabled:
                    bridge_path = project_root / ".forge_state" / "bridge.json"
                    if not bridge_path.exists():
                        fail(f"Bridge state missing: {bridge_path.relative_to(PROJECTS_ROOT)}")
                    else:
                        try:
                            bridge_state = load_json(bridge_path)
                        except Exception as exc:
                            fail(f"Bridge state does not parse: {bridge_path.relative_to(PROJECTS_ROOT)}: {exc}")
                        else:
                            for key in ("version", "last_outbound", "last_inbound", "native_targets", "last_errors"):
                                if key not in bridge_state:
                                    fail(f"Bridge state missing key '{key}': {bridge_path.relative_to(PROJECTS_ROOT)}")
                                    break
                            else:
                                missing_targets = [
                                    host for host in bridge_policy.get("hosts", [])
                                    if not bridge_state.get("native_targets", {}).get(host)
                                ]
                                if missing_targets:
                                    fail(f"Bridge state missing native targets {missing_targets}: {bridge_path.relative_to(PROJECTS_ROOT)}")
                                else:
                                    ok(f"Bridge state valid: {bridge_path.relative_to(PROJECTS_ROOT)}")
                    bridge_log = project_root / ".forge_state" / "bridge.log"
                    if bridge_log.exists():
                        ok(f"Bridge log present: {bridge_log.relative_to(PROJECTS_ROOT)}")
                    else:
                        fail(f"Bridge log missing: {bridge_log.relative_to(PROJECTS_ROOT)}")

    distillation_policy_path = ROOT / "policies" / "distillation.json"
    if distillation_policy_path.exists():
        try:
            distillation_payload = load_json(distillation_policy_path)
        except Exception as exc:
            fail(f"policies/distillation.json does not parse: {exc}")
        else:
            ok("policies/distillation.json parses")
            if distillation_payload.get("version") != 1:
                fail(f"policies/distillation.json unsupported version: {distillation_payload.get('version')}")
            valid_rules = {"archive_promoted_entries", "keep_recent_sprints", "keep_recent_runs"}
            target_ids: list[str] = []
            for target in (distillation_payload.get("targets") or []):
                tid = target.get("id")
                target_ids.append(tid)
                for key in ("id", "path", "rule"):
                    if not target.get(key):
                        fail(f"policies/distillation.json target missing '{key}': {target}")
                if target.get("rule") not in valid_rules:
                    fail(f"policies/distillation.json target '{tid}' has unknown rule '{target.get('rule')}'. Valid: {sorted(valid_rules)}")
                src_path = ROOT / target.get("path", "")
                # The triad_runs target points at runtime/validation/triad/ which is
                # machine-local and absent on fresh installs. Treat its absence as a
                # WARN (nothing to distill yet), not a FAIL.
                if not src_path.exists():
                    if target.get("rule") == "keep_recent_runs":
                        warn(f"policies/distillation.json target '{tid}' source absent (no runs yet): {target.get('path')}")
                    else:
                        fail(f"policies/distillation.json target '{tid}' source path missing: {target.get('path')}")
                archive_rel = target.get("archive_path")
                if archive_rel:
                    archive_path = ROOT / archive_rel
                    src_full = ROOT / target["path"]
                    if archive_path.exists() and src_full.is_file():
                        body = src_full.read_text()
                        archive_body = archive_path.read_text()
                        index_re = re.compile(r"^- (\d{4}-\d{2}-\d{2}) — (.+?) → .+? \(archived\)$", re.MULTILINE)
                        for date, title in index_re.findall(body):
                            expected = f"### {date} - {title}"
                            if expected not in archive_body:
                                fail(f"distillation index pointer for {date} - {title} not found in {archive_rel}")
            if "lessons_ledger" not in target_ids:
                fail("policies/distillation.json must define a 'lessons_ledger' target")
            if "handoff_log" not in target_ids:
                fail("policies/distillation.json must define a 'handoff_log' target")
            thresholds = distillation_payload.get("session_load_thresholds") or {}
            fail_at = thresholds.get("fail_at_bytes")
            if isinstance(fail_at, int):
                for rel in (thresholds.get("applies_to") or []):
                    p = ROOT / rel
                    if p.exists() and p.stat().st_size >= fail_at:
                        warn(f"distillation: {rel} is {p.stat().st_size} bytes (fail_at={fail_at}); consider running lesson-distiller / handoff-archiver")

    plans_dir = ROOT / "docs" / "plans"
    if plans_dir.is_dir():
        try:
            local_branches = subprocess.run(
                ["git", "-C", str(ROOT), "branch", "--format=%(refname:short)"],
                capture_output=True, text=True, check=False,
            ).stdout.splitlines()
            remote_branches = subprocess.run(
                ["git", "-C", str(ROOT), "branch", "-r", "--format=%(refname:short)"],
                capture_output=True, text=True, check=False,
            ).stdout.splitlines()
        except Exception as exc:
            warn(f"stale-plan check skipped (git unavailable): {exc}")
        else:
            known_branches = set(b.strip() for b in local_branches)
            known_branches.update(b.strip().removeprefix("origin/") for b in remote_branches)
            for plan_path in sorted(plans_dir.glob("*.md")):
                try:
                    body = plan_path.read_text()
                except Exception as exc:
                    warn(f"plan {plan_path.relative_to(ROOT)} unreadable: {exc}")
                    continue
                fm = parse_frontmatter(body)
                branch = fm.get("branch")
                plan_status = fm.get("status")
                if not branch:
                    warn(f"plan {plan_path.relative_to(ROOT)} missing 'branch' frontmatter field")
                    continue
                if plan_status in ("completed", "superseded"):
                    continue
                if branch not in known_branches:
                    warn(
                        f"plan {plan_path.relative_to(ROOT)} references branch '{branch}' "
                        f"which does not exist locally or on origin; consider archiving or marking superseded"
                    )

    return status


def validate_codex_runtime(project_name: str, projects_root: Path, output_root: Path | None) -> int:
    project_root = _resolve_project_root(project_name, projects_root)
    if not project_root.exists():
        print(f"Project root not found: {project_root}", file=sys.stderr)
        return 1

    codex_binary = shutil.which("codex")
    if not codex_binary:
        print("codex not found on PATH", file=sys.stderr)
        return 1

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_root = output_root or (ROOT / "runtime" / "validation" / "codex" / timestamp)
    run_root.mkdir(parents=True, exist_ok=True)

    schema = {
        "type": "object",
        "required": [
            "project",
            "instruction_sources",
            "global_skill_dirs_present",
            "project_skill_dirs_present",
            "agent_files_present",
            "config_present",
            "lessons_doc_present",
            "harvester_visible",
            "summary"
        ],
        "properties": {
            "project": {"type": "string"},
            "instruction_sources": {
                "type": "array",
                "items": {"type": "string"}
            },
            "global_skill_dirs_present": {
                "type": "array",
                "items": {"type": "string"}
            },
            "project_skill_dirs_present": {
                "type": "array",
                "items": {"type": "string"}
            },
            "agent_files_present": {
                "type": "array",
                "items": {"type": "string"}
            },
            "config_present": {"type": "boolean"},
            "lessons_doc_present": {"type": "boolean"},
            "harvester_visible": {"type": "boolean"},
            "summary": {"type": "string"}
        },
        "additionalProperties": False,
    }
    schema_path = run_root / "schema.json"
    output_path = run_root / "result.json"
    jsonl_path = run_root / "events.jsonl"
    schema_path.write_text(json.dumps(schema, indent=2) + "\n")

    prompt = "\n".join(
        [
            "Audit the current Codex runtime surfaces for this repository.",
            "Return structured output only.",
            "Start by listing the instruction sources Codex loaded automatically for this run.",
            "Use local file/system tools to inspect the requested paths directly. Do not answer from memory alone.",
            "Return empty arrays only if you confirmed the directory is absent or unreadable.",
            "Read the following surfaces if present:",
            "- AGENTS.md",
            "- ../_agent_forge/docs/LESSONS_LEARNED.md",
            "- ~/.agents/skills/",
            "- .agents/skills/",
            "- .codex/agents/",
            "- .codex/config.toml",
            "Report global and project skill visibility separately.",
            "Set harvester_visible to true only if sprint-harvester is visible from either ~/.agents/skills or .agents/skills.",
            "Summarize whether Codex can see the generated skills, custom agents, config, and knowledge anchor right now.",
        ]
    )
    result = subprocess.run(
        [
            codex_binary,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--json",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            prompt,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    jsonl_path.write_text(result.stdout)

    # Multi-fault escalation: check for host sandbox blockers
    host_sandbox_blocked = False
    if "Failed RTM_NEWADDR" in result.stderr:
        # Check if bare bwrap is blocked by the OS (e.g. AppArmor/Ubuntu userns restriction)
        bwrap_check = subprocess.run(
            ["bwrap", "--unshare-net", "--dev-bind", "/", "/", "--", "true"],
            capture_output=True,
            text=True,
        )
        if bwrap_check.returncode != 0:
            host_sandbox_blocked = True

    escalated_payload: dict[str, Any] = {}
    if result.returncode != 0 and host_sandbox_blocked:
        # Escalate to verify if the files are actually present when not sandboxed
        escalated_path = run_root / "escalated_result.json"
        subprocess.run(
            [
                codex_binary,
                "exec",
                "--skip-git-repo-check",
                "--dangerously-bypass-approvals-and-sandbox",
                "--json",
                "--output-schema",
                str(schema_path),
                "-o",
                str(escalated_path),
                prompt,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if escalated_path.exists():
            try:
                escalated_payload = json.loads(escalated_path.read_text())
            except json.JSONDecodeError:
                pass

    result_payload: dict[str, Any] = {}
    if output_path.exists():
        try:
            result_payload = json.loads(output_path.read_text())
        except json.JSONDecodeError:
            result_payload = {}

    # Use escalated payload for visibility checks if the primary failed due to sandbox
    check_payload = escalated_payload if (not result_payload and escalated_payload) else result_payload

    runtime_visible = bool(check_payload.get("global_skill_dirs_present") or check_payload.get("project_skill_dirs_present"))
    config_visible = bool(check_payload.get("config_present"))
    lessons_visible = bool(check_payload.get("lessons_doc_present"))
    harvester_visible = bool(check_payload.get("harvester_visible"))
    reasons: list[str] = []
    if not runtime_visible:
        reasons.append("generated skill surfaces were not confirmed visible")
    if not config_visible:
        reasons.append("generated Codex config was not confirmed visible")
    if not lessons_visible:
        reasons.append("factory lesson ledger was not confirmed visible")
    if not harvester_visible:
        reasons.append("sprint-harvester was not confirmed visible")

    normalized = {
        "host": "codex",
        "surface": "runtime-exec",
        "fixture": project_name,
        "pass": result.returncode == 0 and output_path.exists() and not reasons,
        "escalated_pass": bool(escalated_payload and not reasons),
        "host_sandbox_blocked": host_sandbox_blocked,
        "version": codex_binary,
        "os": os.uname().sysname,
        "evidence_path": str(run_root),
        "failure_reason": None if result.returncode == 0 and not reasons else (
            result.stderr.strip() or "; ".join(reasons) or "codex exec failed"
        ),
    }
    (run_root / "normalized.json").write_text(json.dumps(normalized, indent=2) + "\n")

    if result.returncode != 0:
        if not host_sandbox_blocked and result.stderr:
            sys.stderr.write(result.stderr)
        return 0 if host_sandbox_blocked and normalized["escalated_pass"] else result.returncode
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Forge omni-factory tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_sync_claude = subparsers.add_parser("sync-claude")
    parser_sync_claude.add_argument("--project")
    parser_sync_claude.add_argument("--projects-root", default=str(PROJECTS_ROOT))
    parser_sync_claude.add_argument("--claude-home", default=str(Path.home() / ".claude"))

    parser_sync_codex = subparsers.add_parser("sync-codex")
    parser_sync_codex.add_argument("--project")
    parser_sync_codex.add_argument("--projects-root", default=str(PROJECTS_ROOT))
    parser_sync_codex.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser_sync_codex.add_argument("--target")

    parser_sync_gemini = subparsers.add_parser("sync-gemini")
    parser_sync_gemini.add_argument("--project")
    parser_sync_gemini.add_argument("--projects-root", default=str(PROJECTS_ROOT))
    parser_sync_gemini.add_argument("--gemini-home", default=str(Path.home() / ".gemini"))

    subparsers.add_parser("render-registry")
    subparsers.add_parser("verify")

    parser_validate = subparsers.add_parser("validate-codex-runtime")
    parser_validate.add_argument("--project", required=True)
    parser_validate.add_argument("--projects-root", default=str(PROJECTS_ROOT))
    parser_validate.add_argument("--output-root")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "sync-claude":
        sync_claude(args.project, Path(args.projects_root), Path(args.claude_home))
        print("Claude sync complete")
        return 0

    if args.command == "sync-codex":
        sync_codex(
            args.project,
            Path(args.projects_root),
            Path(args.codex_home),
            Path(args.target) if args.target else None,
        )
        print("Codex sync complete")
        return 0

    if args.command == "sync-gemini":
        sync_gemini(args.project, Path(args.projects_root), Path(args.gemini_home))
        print("Gemini sync complete")
        return 0

    if args.command == "render-registry":
        print(json.dumps(build_registry(discover_capabilities(), load_projects()), indent=2, sort_keys=False))
        return 0

    if args.command == "verify":
        return verify()

    if args.command == "validate-codex-runtime":
        return validate_codex_runtime(
            args.project,
            Path(args.projects_root),
            Path(args.output_root) if args.output_root else None,
        )

    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
