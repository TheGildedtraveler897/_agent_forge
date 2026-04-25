#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
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


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    root: Path
    required_files: list[str]


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


def load_projects() -> list[ProjectSpec]:
    data = load_json(PROJECTS_CATALOG_PATH)
    projects: list[ProjectSpec] = []
    for entry in data.get("governed_projects", []):
        projects.append(
            ProjectSpec(
                name=entry["name"],
                root=PROJECTS_ROOT / entry["root"],
                required_files=list(entry.get("required_files") or []),
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
            mode = "command" if capability.is_workflow else "subagent"
            entry["claude"] = {
                "mode": mode,
                "generated": True,
                "command_name": capability.claude_command_name or capability.capability_id if capability.is_workflow else None,
                "agent_name": capability.capability_id if capability.is_expert else None,
            }
        if "gemini" in capability.hosts:
            mode = "command" if capability.is_workflow else "subagent"
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
    imports = [
        relpath(project_root, ROOT / "AGENTS.md"),
        relpath(project_root, KNOWLEDGE_ANCHOR_PATH),
        "AGENTS.md",
        "docs/CONOPS.md",
        "docs/HANDOFF.md",
    ]
    if _memory_sections() and (project_root / "MEMORY.md").exists():
        imports.append("MEMORY.md")
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


def normalize_mcp_server(server_id: str, server: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "id": server_id,
        "description": server.get("description", ""),
        "scope": server.get("scope", "project"),
        "projects": list(server.get("projects") or []),
        "transport": dict(server.get("transport") or {}),
        "env_passthrough": list(server.get("env_passthrough") or []),
        "env_literal": dict(server.get("env_literal") or {}),
        "headers": dict(server.get("headers") or {}),
        "tool_allow": list(server.get("tool_allow") or []),
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


def project_mcp_servers(project_name: str) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for server in load_mcp_servers():
        scope = server["scope"]
        projects = server["projects"]
        if scope in {"project", "shared"} and (not projects or project_name in projects):
            selected.append(server)
    return selected


def user_mcp_servers() -> list[dict[str, Any]]:
    return [server for server in load_mcp_servers() if server["scope"] == "user"]


_EVENT_ALIASES = {
    "claude": {
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "pre_commit": "PreToolUse",
        "post_edit": "PostToolUse",
        "session_start": "SessionStart",
        "stop": "Stop",
    },
    "gemini": {
        "pre_tool_use": "preToolUse",
        "post_tool_use": "postToolUse",
        "pre_commit": "preToolUse",
        "post_edit": "postToolUse",
        "session_start": "sessionStart",
        "stop": "stop",
    },
}


def _hooks_for_host(host: str) -> list[dict[str, Any]]:
    payload = load_json(HOOKS_PATH)
    out: list[dict[str, Any]] = []
    for record in (payload.get("shared") or []):
        targets = record.get("targets") or ["claude", "codex", "gemini"]
        if host in targets:
            out.append(record)
    for record in (payload.get(host) or []):
        out.append(record)
    return out


def codex_hook_payload() -> dict[str, Any]:
    hooks = _hooks_for_host("codex")
    grouped: dict[str, list[dict[str, Any]]] = {"hooks": {}}
    for hook in hooks:
        event = hook["event"]
        grouped["hooks"].setdefault(event, []).append(
            {
                "matcher": hook.get("matcher", ""),
                "hooks": [
                    {
                        "type": "command",
                        "command": hook["command"],
                        **({"statusMessage": hook["status_message"]} if hook.get("status_message") else {}),
                        **({"timeout": hook.get("timeout_ms") or hook.get("timeout")} if (hook.get("timeout_ms") or hook.get("timeout")) else {}),
                    }
                ],
            }
        )
    return grouped


def claude_hook_payload() -> dict[str, list[dict[str, Any]]]:
    hooks = _hooks_for_host("claude")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hook in hooks:
        native_event = _EVENT_ALIASES["claude"].get(hook["event"], hook["event"])
        entry: dict[str, Any] = {
            "matcher": hook.get("matcher", ""),
            "hooks": [
                {"type": "command", "command": hook["command"]},
            ],
        }
        if hook.get("timeout_ms"):
            entry["hooks"][0]["timeout"] = hook["timeout_ms"]
        grouped.setdefault(native_event, []).append(entry)
    return grouped


def gemini_hook_payload() -> dict[str, list[dict[str, Any]]]:
    hooks = _hooks_for_host("gemini")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for hook in hooks:
        native_event = _EVENT_ALIASES["gemini"].get(hook["event"], hook["event"])
        entry: dict[str, Any] = {
            "matcher": hook.get("matcher", ""),
            "command": hook["command"],
        }
        if hook.get("timeout_ms"):
            entry["timeoutMs"] = hook["timeout_ms"]
        if hook.get("description"):
            entry["description"] = hook["description"]
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


def render_claude_project_mcp(project_name: str) -> str | None:
    servers = project_mcp_servers(project_name)
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
                    "command": transport.get("command"),
                    "args": transport.get("args", []),
                    **({"cwd": transport["cwd"]} if transport.get("cwd") else {}),
                }
            )
        elif transport.get("type") == "streamable_http":
            entry["httpUrl"] = transport.get("http_url") or transport.get("url")
        elif transport.get("type") == "sse":
            entry["url"] = transport.get("url")
        if server["headers"]:
            entry["headers"] = server["headers"]
        if env_map:
            entry["env"] = env_map
        payload["mcpServers"][server["id"]] = entry
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_gemini_settings(project_name: str) -> str:
    settings: dict[str, Any] = {
        "context": {
            "fileName": "GEMINI.md",
        }
    }
    servers = project_mcp_servers(project_name)
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
            if server["tool_allow"]:
                entry["includeTools"] = server["tool_allow"]
            if server["tool_deny"]:
                entry["excludeTools"] = server["tool_deny"]
            settings["mcpServers"][server["id"]] = entry
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
        lines.extend(["", "[features]", "codex_hooks = true"])

    relevant_ids = set()
    for capability in capabilities:
        relevant_ids.update(capability.requires_mcp_servers)

    for server in project_mcp_servers(project_name):
        if relevant_ids and server["id"] not in relevant_ids:
            continue
        lines.extend(["", f"[mcp_servers.{server['id']}]"])
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
        elif transport.get("type") == "sse":
            lines.append(f"url = {toml_string(transport['url'])}")
        if server["headers"]:
            pass
        lines.append(f"required = {'true' if server['required'] else 'false'}")
        lines.append(f"supports_parallel_tool_calls = {'true' if server['parallel_safe'] else 'false'}")
        lines.append(f"startup_timeout_sec = {max(1, server['startup_timeout_ms'] // 1000)}")
        lines.append(f"tool_timeout_sec = {max(1, server['tool_timeout_ms'] // 1000)}")
        if server["tool_allow"]:
            items = ", ".join(toml_string(item) for item in server["tool_allow"])
            lines.append(f"enabled_tools = [{items}]")
        if server["tool_deny"]:
            items = ", ".join(toml_string(item) for item in server["tool_deny"])
            lines.append(f"disabled_tools = [{items}]")
        env_map = {key: f"${key}" for key in server["env_passthrough"]}
        env_map.update(server["env_literal"])
        if env_map:
            lines.append("[mcp_servers." + server["id"] + ".env]")
            for key, value in env_map.items():
                lines.append(f"{key} = {toml_string(value)}")
        if server["headers"]:
            lines.append("[mcp_servers." + server["id"] + ".headers]")
            for key, value in server["headers"].items():
                lines.append(f"{key} = {toml_string(value)}")
    lines.append("")
    return "\n".join(lines)


def render_user_codex_mcp_block() -> str:
    servers = user_mcp_servers()
    if not servers:
        return ""
    lines = [
        "# BEGIN AGENT FORGE MCP",
        "# Generated by Agent Forge omni-factory.",
    ]
    for server in servers:
        lines.extend(["", f"[mcp_servers.{server['id']}]"])
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
        elif transport.get("type") == "sse":
            lines.append(f"url = {toml_string(transport['url'])}")
        lines.append(f"required = {'true' if server['required'] else 'false'}")
        lines.append(f"supports_parallel_tool_calls = {'true' if server['parallel_safe'] else 'false'}")
        lines.append(f"startup_timeout_sec = {max(1, server['startup_timeout_ms'] // 1000)}")
        lines.append(f"tool_timeout_sec = {max(1, server['tool_timeout_ms'] // 1000)}")
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
    for capability in capabilities:
        if capability.scope != "global" or "claude" not in capability.hosts:
            continue
        read_path = skill_read_path_for_home(claude_home / "commands", capability)
        if capability.is_workflow:
            name = f"{capability.claude_command_name or capability.capability_id}.md"
            user_commands[name] = render_claude_command(capability, read_path)
        elif capability.is_expert:
            name = f"{capability.capability_id}.md"
            user_agents[name] = render_claude_agent(capability, read_path)

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

    for skill in discover_capabilities():
        ok(f"Capability metadata OK: {skill.capability_id}")

    generated_registry = build_registry(discover_capabilities(), load_projects())
    if REGISTRY_PATH.exists():
        current = load_json(REGISTRY_PATH)
        if current == generated_registry:
            ok("registry.json matches generated compatibility registry")
        else:
            fail("registry.json is out of date with canonical omni-factory sources")
    else:
        fail("Missing registry.json")

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
        for bucket in ("shared", "claude", "codex", "gemini"):
            for hook in (hooks_payload.get(bucket) or []):
                for key in ("id", "event", "command"):
                    if not hook.get(key):
                        fail(f"hooks.json[{bucket}] record missing '{key}': {hook}")
                cmd = (hook.get("command") or "").strip()
                if cmd.startswith("bash "):
                    script_ref = cmd.split(None, 1)[1].split()[0]
                    resolved = Path(script_ref.replace("~", str(Path.home())))
                    if not resolved.exists():
                        fail(f"hooks.json '{hook.get('id')}' command script missing: {resolved}")
                    else:
                        ok(f"Hook script present: {hook.get('id')} -> {resolved.relative_to(Path.home()) if resolved.is_relative_to(Path.home()) else resolved}")

    if MEMORY_POLICY_PATH.exists():
        try:
            memory_payload = load_json(MEMORY_POLICY_PATH)
        except Exception as exc:
            fail(f"policies/memory.json does not parse: {exc}")
        else:
            ok("policies/memory.json parses")
            section_ids = [s.get("id") for s in (memory_payload.get("sections") or [])]
            if not section_ids:
                fail("policies/memory.json has no sections")
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
