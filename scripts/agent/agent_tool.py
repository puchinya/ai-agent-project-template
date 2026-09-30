#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from pathlib import PureWindowsPath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime
import platform
from typing import Any
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".agent" / "project.json"
STATE = ROOT / ".agent-state" / "issues"
SPEC_REQUIRED_V1 = [
    "Purpose",
    "Scope",
    "Terminology",
    "Normative requirements",
    "Observable behavior",
    "Error and boundary behavior",
    "Compatibility and versioning",
    "Acceptance traceability",
]
DESIGN_REQUIRED_V1 = [
    "Context and goals",
    "Requirements traceability",
    "Architecture overview",
    "Component responsibilities",
    "Data and control flow",
    "Ownership and lifecycle",
    "Error handling and recovery",
    "Concurrency and async model",
    "Compatibility and migration",
    "Verification strategy",
    "Alternatives considered",
    "Risks and open follow-ups",
]
SPEC_REQUIRED_V2 = [
    "Overview",
    "Purpose",
    "Scope",
    "Terminology",
    "Semantic ownership",
    "Normative requirements",
    "Observable behavior",
    "Error and boundary behavior",
    "Quality attributes",
    "Compatibility and versioning",
    "Acceptance traceability",
]
DESIGN_REQUIRED_V2 = [
    "Overview",
    "Context and goals",
    "Requirements traceability",
    "Architecture overview",
    "Architecture invariants",
    "Component responsibilities",
    "Data and control flow",
    "Ownership and lifecycle",
    "Error handling and recovery",
    "Concurrency and async model",
    "Quality attributes and operations",
    "Compatibility and migration",
    "Verification strategy",
    "Alternatives considered",
    "Risks and open follow-ups",
]
DOCUMENTATION_SCHEMA_VERSIONS = {1, 2}
DOCUMENTATION_SCHEMA_MARKER = "agent-doc-schema"
DOCUMENTATION_SCHEMA_2_MARKER = "<!-- agent-doc-schema: 2 -->"
DOCUMENTATION_SIZE_WARNING_BYTES = 50 * 1024
CANONICAL_BEGIN = "AGENT_REVIEWER_CHECKLIST_V1_BEGIN"
CANONICAL_END = "AGENT_REVIEWER_CHECKLIST_V1_END"
APPLICATION_TYPES = {"generic", "desktop-gui", "cli", "mobile", "server", "embedded", "library"}
RUNTIME_HOSTS = {"windows", "macos", "linux"}
GLOBAL_HOOK_NAMES = {"branch_switch", "verify_quick", "verify_final"}
VERIFICATION_HOOK_NAMES = {"verify_quick", "verify_final"}

def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)

def run(args: list[str], *, capture: bool = False, check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture,
    )
    return result.stdout.strip() if capture else ""

def shell(command: str) -> None:
    interpreter = re.match(r"^(\s*)(python3?)(?=\s|$)", command)
    if interpreter and shutil.which(interpreter.group(2)) is None:
        fallback = "python3" if interpreter.group(2) == "python" else "python"
        if shutil.which(fallback):
            command = interpreter.group(1) + fallback + command[interpreter.end(2):]
    print(f"+ {command}")
    subprocess.run(command, cwd=ROOT, shell=True, check=True)

def require(*commands: str) -> None:
    import shutil
    missing = [c for c in commands if shutil.which(c) is None]
    if missing:
        fail("required command(s) not found: " + ", ".join(missing))

def load_config(require_initialized: bool = True) -> dict[str, Any]:
    if not CONFIG.exists():
        fail("missing .agent/project.json; run init-project first")
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid .agent/project.json: {exc}")
    if not isinstance(data, dict):
        fail("invalid .agent/project.json: expected a JSON object")
    if require_initialized and data.get("initialized") is not True:
        fail("project profile is not initialized; run init-project")
    schema = data.get("schema_version")
    if type(schema) is not int or schema not in {1, 2}:
        fail(f"unsupported project profile schema: {schema!r}")
    if schema == 1:
        return data
    return validate_profile_v2(data)

def save_config(data: dict[str, Any]) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def validate_profile_v2(data: dict[str, Any]) -> dict[str, Any]:
    def object_field(value: Any, name: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            fail(f"invalid schema-2 project profile: {name} must be an object")
        return value

    def string_list(value: Any, name: str, *, allow_empty: bool = True) -> list[str]:
        if not isinstance(value, list) or (not allow_empty and not value):
            fail(f"invalid schema-2 project profile: {name} must be a {'' if allow_empty else 'non-empty '}array of strings")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            fail(f"invalid schema-2 project profile: {name} must contain non-empty strings")
        return value

    def validate_hooks(value: Any, name: str, expected: set[str]) -> None:
        hooks = object_field(value, name)
        unknown = set(hooks) - expected
        if unknown:
            fail(f"invalid schema-2 project profile: unsupported {name} hook(s): {', '.join(sorted(unknown))}")
        for hook_name in sorted(expected):
            commands = hooks.get(hook_name)
            if not isinstance(commands, list) or any(not isinstance(command, str) or not command.strip() for command in commands):
                fail(f"invalid schema-2 project profile: {name}.{hook_name} must be an array of non-empty command strings")

    if type(data.get("initialized")) is not bool:
        fail("invalid schema-2 project profile: initialized must be a boolean")
    components = data.get("components")
    if not isinstance(components, list) or not components:
        fail("invalid schema-2 project profile: components must be a non-empty array")
    validate_hooks(data.get("hooks"), "hooks", GLOBAL_HOOK_NAMES)

    component_ids: set[str] = set()
    for index, component_value in enumerate(components):
        name = f"components[{index}]"
        component = object_field(component_value, name)
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id.strip() or any(char in component_id for char in ",\r\n"):
            fail(f"invalid schema-2 project profile: {name}.id must be a non-empty single-line identifier without commas")
        if component_id in component_ids:
            fail(f"invalid schema-2 project profile: duplicate component id {component_id!r}")
        component_ids.add(component_id)

        roots = string_list(component.get("roots"), f"{name}.roots", allow_empty=False)
        for root in roots:
            windows_path = PureWindowsPath(root)
            normalized = root.replace("\\", "/")
            if windows_path.drive or windows_path.root or normalized.startswith("/") or any(part == ".." for part in normalized.split("/")):
                fail(f"invalid schema-2 project profile: unsafe repository-relative root {root!r}")

        string_list(component.get("stacks"), f"{name}.stacks")
        application_types = string_list(component.get("application_types"), f"{name}.application_types", allow_empty=False)
        if len(application_types) != len(set(application_types)):
            fail(f"invalid schema-2 project profile: {name}.application_types must be unique")
        unknown_types = sorted(set(application_types) - APPLICATION_TYPES)
        if unknown_types:
            fail(f"invalid schema-2 project profile: unknown application type(s): {', '.join(unknown_types)}")
        validate_hooks(component.get("hooks"), f"{name}.hooks", VERIFICATION_HOOK_NAMES)

        targets = component.get("targets")
        if not isinstance(targets, list):
            fail(f"invalid schema-2 project profile: {name}.targets must be an array")
        target_ids: set[str] = set()
        for target_index, target_value in enumerate(targets):
            target_name = f"{name}.targets[{target_index}]"
            target = object_field(target_value, target_name)
            target_id = target.get("id")
            if not isinstance(target_id, str) or not target_id.strip() or any(char in target_id for char in ",\r\n"):
                fail(f"invalid schema-2 project profile: {target_name}.id must be a non-empty single-line identifier without commas")
            if target_id in target_ids:
                fail(f"invalid schema-2 project profile: duplicate target id {target_id!r} in component {component_id!r}")
            target_ids.add(target_id)
            runnable_on = string_list(target.get("runnable_on"), f"{target_name}.runnable_on", allow_empty=False)
            if len(runnable_on) != len(set(runnable_on)):
                fail(f"invalid schema-2 project profile: {target_name}.runnable_on values must be unique")
            invalid_hosts = sorted(set(runnable_on) - (RUNTIME_HOSTS | {"any"}))
            if invalid_hosts:
                fail(f"invalid schema-2 project profile: invalid runnable_on value(s): {', '.join(invalid_hosts)}")
            validate_hooks(target.get("hooks"), f"{target_name}.hooks", VERIFICATION_HOOK_NAMES)
    return data

def detect_stacks() -> list[str]:
    stacks: list[str] = []
    if (ROOT / "Cargo.toml").exists():
        stacks.append("rust")
    if (ROOT / "package.json").exists():
        stacks.append("node")
    if (ROOT / "pyproject.toml").exists() or (ROOT / "requirements.txt").exists() or (ROOT / "setup.py").exists():
        stacks.append("python")
    if list(ROOT.glob("*.sln")) or list(ROOT.glob("*.csproj")) or list(ROOT.glob("**/*.csproj")):
        stacks.append("dotnet")
    return stacks or ["generic"]

def node_scripts() -> set[str]:
    path = ROOT / "package.json"
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        return set(scripts) if isinstance(scripts, dict) else set()
    except Exception:
        return set()

def default_hooks(stacks: list[str], cargo_clean: bool) -> dict[str, list[str]]:
    branch: list[str] = []
    quick: list[str] = []
    final: list[str] = []
    if "rust" in stacks:
        if cargo_clean:
            branch.append("cargo clean")
        quick.append("cargo check --workspace")
        final.extend(["cargo fmt --all -- --check", "cargo test --workspace"])
    if "node" in stacks:
        scripts = node_scripts()
        if "typecheck" in scripts:
            quick.append("npm run typecheck")
        elif "build" in scripts:
            quick.append("npm run build")
        if "lint" in scripts:
            final.append("npm run lint")
        if "test" in scripts:
            final.append("npm test")
        if "typecheck" in scripts and "npm run typecheck" not in quick:
            final.append("npm run typecheck")
    if "python" in stacks:
        # Conservative defaults: only use pytest when project already signals pytest config/dependency.
        pytest_signal = any([
            (ROOT / "pytest.ini").exists(),
            (ROOT / "conftest.py").exists(),
            (ROOT / "pyproject.toml").exists() and "pytest" in (ROOT / "pyproject.toml").read_text(encoding="utf-8", errors="ignore"),
        ])
        if pytest_signal:
            quick.append("python -m pytest -q")
            final.append("python -m pytest")
    if "dotnet" in stacks:
        quick.append("dotnet build")
        final.extend(["dotnet build --no-restore", "dotnet test --no-build"])
    final.append("python scripts/agent/agent_tool.py validate-docs")
    return {"branch_switch": branch, "verify_quick": quick, "verify_final": final}

def default_component_hooks(stacks: list[str]) -> dict[str, list[str]]:
    hooks = default_hooks(stacks, cargo_clean=False)
    return {
        "verify_quick": hooks["verify_quick"],
        "verify_final": [
            command for command in hooks["verify_final"]
            if command != "python scripts/agent/agent_tool.py validate-docs"
        ],
    }

def runtime_host() -> str:
    system = platform.system().casefold()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    return system or "unknown"

def runtime_host_label() -> str:
    return f"{runtime_host()}/{platform.machine() or 'unknown'}"

def merge_gitignore(stacks: list[str]) -> None:
    path = ROOT / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    additions: list[str] = []
    if "rust" in stacks:
        additions += ["/target/"]
    if "node" in stacks:
        additions += ["/node_modules/"]
    if "python" in stacks:
        additions += ["__pycache__/", "*.py[cod]", "/.venv/"]
    if "dotnet" in stacks:
        additions += ["**/bin/", "**/obj/"]
    missing = [line for line in additions if line not in existing.splitlines()]
    if missing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += "\n# Added by scripts/agent/init-project\n" + "\n".join(missing) + "\n"
        path.write_text(existing, encoding="utf-8")

def cmd_init(args: argparse.Namespace) -> None:
    stacks = [x.strip().lower() for x in args.stack.split(",") if x.strip()] if args.stack else detect_stacks()
    if len(stacks) != len(set(stacks)):
        fail("--stack values must be unique")
    cargo_clean = args.cargo_clean == "on" if args.cargo_clean else False
    milestones = args.version_milestones == "on" if args.version_milestones else False
    application_types = [item.strip() for item in (getattr(args, "application_type", None) or "generic").split(",") if item.strip()]
    if not application_types:
        fail("--application-type must contain at least one value")
    unknown_types = sorted(set(application_types) - APPLICATION_TYPES)
    if unknown_types:
        fail("unsupported application type(s): " + ", ".join(unknown_types))
    if len(application_types) != len(set(application_types)):
        fail("--application-type values must be unique")
    target_ids = [item.strip() for item in (getattr(args, "target", None) or "").split(",") if item.strip()]
    if len(target_ids) != len(set(target_ids)):
        fail("--target values must be unique")
    component_hooks = default_component_hooks(stacks)
    global_hooks = {
        "branch_switch": ["cargo clean"] if cargo_clean else [],
        "verify_quick": [],
        "verify_final": ["python scripts/agent/agent_tool.py validate-docs"],
    }
    targets = [
        {
            "id": target_id,
            "runnable_on": ["any"],
            "hooks": {"verify_quick": [], "verify_final": []},
        }
        for target_id in target_ids
    ]
    data = {
        "schema_version": 2,
        "initialized": True,
        "project_name": ROOT.name,
        "components": [{
            "id": "root",
            "roots": ["."],
            "stacks": stacks,
            "application_types": application_types,
            "targets": targets,
            "hooks": component_hooks,
        }],
        "branch": {"prefix": "feature", "max_slug_length": 48},
        "milestones": {"enabled": milestones, "version_source": "auto"},
        "hooks": global_hooks,
    }
    save_config(data)
    merge_gitignore(stacks)
    project_md = ROOT / "docs" / "agents" / "project.md"
    project_md.parent.mkdir(parents=True, exist_ok=True)
    component_rows = []
    for component in data["components"]:
        roots = ", ".join(f"`{value}`" for value in component["roots"])
        component_stacks = ", ".join(f"`{value}`" for value in component["stacks"]) or "None"
        types = ", ".join(f"`{value}`" for value in component["application_types"])
        component_targets = ", ".join(
            f"`{target['id']}` ({', '.join(target['runnable_on'])})" for target in component["targets"]
        ) or "None"
        component_rows.append(f"| `{component['id']}` | {roots} | {component_stacks} | {types} | {component_targets} |")
    component_table = (
        "## Components\n\n"
        "| ID | Roots | Stacks | Application types | Targets (`runnable_on`) |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(component_rows)
        + "\n\n"
    )
    def hook_lines(name: str) -> str:
        cmds = data["hooks"][name] + [
            command
            for component in data["components"]
            for command in component["hooks"].get(name, [])
        ]
        return "\n".join(f"- `{c}`" for c in cmds) if cmds else "- None"
    project_md.write_text(
        "# Project profile\n\n"
        f"- Project: `{ROOT.name}`\n"
        "- Profile schema: `2`\n"
        f"- Version milestones: {'enabled' if milestones else 'disabled'}\n\n"
        + component_table
        + "## Branch-switch hook\n\n" + hook_lines("branch_switch") + "\n\n"
        "## Quick verification\n\n" + hook_lines("verify_quick") + "\n\n"
        "## Final verification\n\n" + hook_lines("verify_final") + "\n\n"
        "This file is generated from `.agent/project.json`. Edit the JSON when changing project execution policy, then keep this file synchronized.\n",
        encoding="utf-8",
    )
    print(f"initialized={ROOT.name}")
    print("stacks=" + ",".join(stacks))
    print(f"cargo_clean={'on' if cargo_clean else 'off'}")
    print(f"version_milestones={'on' if milestones else 'off'}")

def cmd_setup_github(args: argparse.Namespace) -> None:
    require("git", "gh")
    run(["gh", "auth", "status"])
    labels = {
        "phase:requirements": "Requirements discovery and acceptance criteria",
        "phase:design": "Specification/design in progress",
        "phase:ready": "Approved and ready for implementation",
        "phase:implementation": "Implementation in progress",
        "phase:review": "Pull request / review in progress",
        "needs-user-decision": "A user or maintainer decision is required",
        "blocked": "External or technical blocker",
    }
    colors = {
        "phase:requirements": "D4C5F9",
        "phase:design": "BFDADC",
        "phase:ready": "0E8A16",
        "phase:implementation": "1D76DB",
        "phase:review": "5319E7",
        "needs-user-decision": "FBCA04",
        "blocked": "D93F0B",
    }
    for name, desc in labels.items():
        subprocess.run(
            ["gh", "label", "create", name, "--description", desc, "--color", colors[name], "--force"],
            cwd=ROOT, check=True
        )
    print("github_labels=ready")

def cmd_run_hook(args: argparse.Namespace) -> None:
    cfg = load_config()
    if cfg.get("schema_version") == 2:
        if args.name not in GLOBAL_HOOK_NAMES:
            fail(f"unknown hook: {args.name}")
        if args.name == "branch_switch":
            if getattr(args, "component", None):
                fail("--component only applies to verification hooks")
            commands = cfg["hooks"].get(args.name, [])
            for command in commands:
                shell(command)
            print(f"hook={args.name} commands={len(commands)}")
            return

        components = cfg["components"]
        requested = getattr(args, "component", None) or []
        known_ids = {component["id"] for component in components}
        unknown = [component_id for component_id in requested if component_id not in known_ids]
        if unknown:
            fail("unknown component id(s): " + ", ".join(dict.fromkeys(unknown)))
        selected_ids = set(requested) if requested else known_ids
        selected = [component for component in components if component["id"] in selected_ids]
        steps: list[tuple[str, str]] = []
        for command in cfg["hooks"].get(args.name, []):
            steps.append(("command", command))
        for component in selected:
            for command in component["hooks"].get(args.name, []):
                steps.append(("command", command))
            for target in component["targets"]:
                target_commands = target["hooks"].get(args.name, [])
                if not target_commands:
                    continue
                runnable_on = target["runnable_on"]
                if "any" in runnable_on or runtime_host() in runnable_on:
                    for command in target_commands:
                        steps.append(("command", command))
                else:
                    steps.append((
                        "diagnostic",
                        "SKIPPED_TARGET_VERIFICATION "
                        f"component={component['id']} target={target['id']} reason=host_mismatch",
                    ))
        executed = 0
        for kind, value in steps:
            if kind == "command":
                shell(value)
                executed += 1
            else:
                print(value)
        print(f"hook={args.name} commands={executed}")
        return

    hooks = cfg.get("hooks", {})
    if args.name not in hooks:
        fail(f"unknown hook: {args.name}")
    if getattr(args, "component", None):
        fail("--component is only supported by schema-2 project profiles")
    commands = hooks.get(args.name) or []
    if not commands:
        print(f"hook={args.name} commands=0")
        return
    for command in commands:
        shell(command)
    print(f"hook={args.name} commands={len(commands)}")

def issue_exists(number: int) -> None:
    require("gh")
    run(["gh", "issue", "view", str(number)])

def slugify(text: str, limit: int) -> str:
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)[:limit].rstrip("-")
    if not value:
        fail("description could not be converted to an ASCII branch slug; use a short English description")
    return value

def cmd_start_branch(args: argparse.Namespace) -> None:
    require("git", "gh")
    cfg = load_config()
    issue_exists(args.issue)
    if run(["git", "status", "--porcelain"], capture=True):
        fail("working tree is not clean")
    default_branch = run(["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"], capture=True)
    if not default_branch:
        fail("could not determine default branch")
    prefix = cfg.get("branch", {}).get("prefix", "feature")
    limit = int(cfg.get("branch", {}).get("max_slug_length", 48))
    branch = f"{prefix}/{args.issue}-{slugify(args.description, limit)}"
    run(["git", "fetch", "origin", default_branch])
    subprocess.run(["git", "fetch", "origin", branch], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    current = run(["git", "branch", "--show-current"], capture=True)
    changed = current != branch
    if current == branch:
        pass
    elif subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=ROOT).returncode == 0:
        run(["git", "switch", branch])
    elif subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"], cwd=ROOT).returncode == 0:
        run(["git", "switch", "--track", "-c", branch, f"origin/{branch}"])
    else:
        run(["git", "switch", "-c", branch, f"origin/{default_branch}"])
    if changed:
        for command in cfg.get("hooks", {}).get("branch_switch", []):
            shell(command)
    print(branch)

def discover_version() -> str | None:
    cargo = ROOT / "Cargo.toml"
    if cargo.exists():
        try:
            import tomllib
            data = tomllib.loads(cargo.read_text(encoding="utf-8"))
            return data.get("workspace", {}).get("package", {}).get("version") or data.get("package", {}).get("version")
        except Exception:
            pass
    package = ROOT / "package.json"
    if package.exists():
        try:
            v = json.loads(package.read_text(encoding="utf-8")).get("version")
            if isinstance(v, str) and v:
                return v
        except Exception:
            pass
    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            v = data.get("project", {}).get("version")
            if isinstance(v, str) and v:
                return v
        except Exception:
            pass
    for csproj in ROOT.glob("**/*.csproj"):
        try:
            tree = ET.parse(csproj)
            for tag in ("Version", "VersionPrefix"):
                node = tree.find(f".//{tag}")
                if node is not None and node.text:
                    return node.text.strip()
        except Exception:
            continue
    return None

def cmd_milestone(args: argparse.Namespace) -> None:
    cfg = load_config()
    if not cfg.get("milestones", {}).get("enabled"):
        print("milestones=disabled")
        return
    require("gh")
    issue_exists(args.issue)
    version = discover_version()
    if not version:
        fail("version milestones enabled but no supported version source was detected")
    repo = run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], capture=True)
    milestones_json = run(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"], capture=True)
    milestones = json.loads(milestones_json)
    match = next((m for m in milestones if m.get("title") == version), None)
    if not match:
        created = json.loads(run(["gh", "api", "--method", "POST", f"repos/{repo}/milestones", "-f", f"title={version}"], capture=True))
        match = created
    number = match.get("number")
    run(["gh", "issue", "edit", str(args.issue), "--milestone", version])
    print(f"milestone={version}")
    print(f"milestone_number={number}")

def extract_phase(issue: dict[str, Any]) -> str:
    labels = issue.get("labels", [])
    names = [x.get("name", "") for x in labels if isinstance(x, dict)]
    return next((n for n in names if n.startswith("phase:")), "")

def parse_affected_components(body: str) -> list[str] | None:
    lines = markdown_without_fences(body).splitlines()
    headings = [
        index for index, line in enumerate(lines)
        if re.fullmatch(r"##\s+Affected components\s*#*\s*", line.strip(), re.I)
    ]
    if not headings:
        return None
    if len(headings) != 1:
        fail("Issue body must contain at most one '## Affected components' section")
    values: list[str] = []
    for line in lines[headings[0] + 1:]:
        if re.match(r"^#{1,6}\s+", line):
            break
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*-\s+`([^`]+)`\s*", line)
        if not match:
            fail("Affected components entries must use '- `component-id`' list items")
        values.append(match.group(1))
    if not values:
        fail("Affected components section must list at least one component")
    if len(values) != len(set(values)):
        fail("Affected components section contains duplicate component ids")
    return values

def context_profile_components(cfg: dict[str, Any], issue_body: str) -> tuple[int, list[dict[str, Any]], list[str]]:
    schema = cfg["schema_version"]
    if schema == 1:
        component = {
            "id": "root",
            "roots": ["."],
            "stacks": cfg.get("stacks", []),
            "application_types": ["generic"],
            "targets": [],
        }
        return schema, [component], ["root"]

    components = cfg["components"]
    component_by_id = {component["id"]: component for component in components}
    requested = parse_affected_components(issue_body)
    if requested is None:
        if len(components) != 1:
            fail("multi-component Issue must include an '## Affected components' section")
        requested = [components[0]["id"]]
    unknown = [component_id for component_id in requested if component_id not in component_by_id]
    if unknown:
        fail("unknown affected component id(s): " + ", ".join(unknown))
    selected_ids = [component["id"] for component in components if component["id"] in set(requested)]
    return schema, [component_by_id[item] for item in selected_ids], selected_ids

def cmd_context(args: argparse.Namespace) -> None:
    require("git", "gh")
    issue_json = json.loads(run(["gh", "issue", "view", str(args.issue), "--json", "number,labels,url,body"], capture=True))
    phase = extract_phase(issue_json)
    workflow = {
        "phase:requirements": "docs/agent-workflow/requirements.md",
        "phase:design": "docs/agent-workflow/design.md",
        "phase:ready": "docs/agent-workflow/implementation.md",
        "phase:implementation": "docs/agent-workflow/implementation.md",
        "phase:review": "docs/agent-workflow/review.md",
    }.get(phase, "")
    branch = run(["git", "branch", "--show-current"], capture=True)
    head = run(["git", "rev-parse", "HEAD"], capture=True)
    default = run(["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"], capture=True)
    dirty = bool(run(["git", "status", "--porcelain"], capture=True))
    pr = run(["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "1", "--json", "number,url", "--jq", ".[0] // {}"], capture=True)
    base = STATE / str(args.issue)
    contract = base / "implementation-contract.md"
    sha_path = base / "implementation-contract.sha256"
    contract_status = "absent"
    contract_sha = ""
    if contract.exists() or sha_path.exists():
        contract_status = "invalid"
        if contract.is_file() and sha_path.is_file():
            contract_sha = hashlib.sha256(contract.read_bytes()).hexdigest()
            recorded = sha_path.read_text(encoding="utf-8").strip().split()[0] if sha_path.read_text(encoding="utf-8").strip() else ""
            if recorded == contract_sha:
                contract_status = "ok"
    cfg = load_config()
    profile_schema, components, affected_ids = context_profile_components(cfg, issue_json.get("body", ""))
    print(f"issue={args.issue}")
    print(f"phase={phase}")
    print(f"workflow={workflow}")
    print(f"branch={branch}")
    print(f"head={head}")
    print(f"default_branch={default}")
    print(f"worktree={'dirty' if dirty else 'clean'}")
    print(f"pr={pr}")
    print(f"contract_status={contract_status}")
    print(f"contract_sha256={contract_sha}")
    print(f"profile_schema={profile_schema}")
    print(f"runtime_host={runtime_host_label()}")
    print(f"affected_components={','.join(affected_ids)}")
    for component in components:
        prefix = f"component.{component['id']}"
        print(f"{prefix}.roots={','.join(component['roots'])}")
        print(f"{prefix}.stacks={','.join(component['stacks'])}")
        print(f"{prefix}.application_types={','.join(component['application_types'])}")
        print(f"{prefix}.targets={','.join(target['id'] for target in component['targets'])}")
    profile_types = sorted({
        application_type
        for component in components
        for application_type in component["application_types"]
        if application_type != "generic"
    })
    for application_type in profile_types:
        print(f"application_profile=docs/standards/application-profiles/{application_type}.md")

def state_dir(issue: int) -> Path:
    p = STATE / str(issue)
    (p / "logs").mkdir(parents=True, exist_ok=True)
    (p / "screenshots").mkdir(parents=True, exist_ok=True)
    return p

def cmd_prepare_evidence(args: argparse.Namespace) -> None:
    p = state_dir(args.issue)
    print(p)

def normalize_item(text: str) -> str:
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", text).strip())

def extract_markdown_checklist(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    items: list[str] = []
    active_level: int | None = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s+Reviewer Checklist\s*$", line, re.I)
        if m:
            active_level = len(m.group(1))
            continue
        if active_level is not None:
            h = re.match(r"^(#{1,6})\s+", line)
            if h and len(h.group(1)) <= active_level:
                active_level = None
                continue
            c = re.match(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$", line)
            if c:
                item = normalize_item(c.group(1))
                if item:
                    items.append(item)
    return items

def extract_canonical(text: str) -> list[str] | None:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    begins = [i for i, x in enumerate(lines) if x.strip() == CANONICAL_BEGIN]
    ends = [i for i, x in enumerate(lines) if x.strip() == CANONICAL_END]
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0]:
        fail("malformed canonical reviewer checklist block")
    items: list[str] = []
    for line in lines[begins[0] + 1:ends[0]]:
        s = line.strip()
        if not s:
            continue
        if s.startswith("REVIEW_ITEM:"):
            item = normalize_item(s[len("REVIEW_ITEM:"):])
        else:
            m = re.match(r"^[-*]\s+\[[ xX]\]\s+(.+)$", s)
            if not m:
                fail("unexpected line in canonical reviewer checklist block")
            item = normalize_item(m.group(1))
        if not item:
            fail("empty canonical reviewer checklist item")
        items.append(item)
    if not items:
        fail("canonical reviewer checklist is empty")
    return items

def verify_contract(base: Path) -> list[str]:
    contract = base / "implementation-contract.md"
    sha_path = base / "implementation-contract.sha256"
    if not contract.exists() and not sha_path.exists():
        return []
    if not contract.is_file() or not sha_path.is_file():
        fail("Implementation Contract mirror is incomplete")
    actual = hashlib.sha256(contract.read_bytes()).hexdigest()
    recorded = sha_path.read_text(encoding="utf-8").strip().split()[0]
    if actual != recorded:
        fail("Implementation Contract integrity check failed")
    text = contract.read_text(encoding="utf-8")
    return extract_canonical(text) or extract_markdown_checklist(text)

def effective_checklist(issue: int) -> tuple[list[tuple[str, str, str]], str]:
    require("gh")
    body = json.loads(run(["gh", "issue", "view", str(issue), "--json", "number,body"], capture=True)).get("body", "")
    base = state_dir(issue)
    contract_items = verify_contract(base)
    issue_items = extract_markdown_checklist(body)
    if not contract_items and not issue_items:
        fail("no effective Reviewer Checklist found")
    entries: list[tuple[str, str, str]] = []
    seen: dict[str, str] = {}
    for prefix, source, items in [("C", "contract", contract_items), ("I", "issue", issue_items)]:
        for i, item in enumerate(items, 1):
            key = normalize_item(item).casefold()
            if key in seen:
                fail(f"duplicate Reviewer Checklist item: {source} duplicates {seen[key]}")
            item_id = f"{prefix}{i:03d}"
            seen[key] = item_id
            entries.append((item_id, source, item))
    canonical = "".join(f"{i}\t{text}\n" for i, _s, text in entries)
    return entries, hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def cmd_prepare_review(args: argparse.Namespace) -> None:
    entries, fingerprint = effective_checklist(args.issue)
    base = state_dir(args.issue)
    checklist = base / "reviewer-checklist.md"
    sha_path = base / "reviewer-checklist.sha256"
    review = base / "self-review.md"
    checklist.write_text(
        "# Reviewer Checklist\n\n"
        f"Issue: #{args.issue}\n"
        f"Checklist-SHA256: {fingerprint}\n\n" +
        "\n".join(f"- {i} | {s} | {text}" for i, s, text in entries) + "\n",
        encoding="utf-8"
    )
    old = sha_path.read_text(encoding="utf-8").strip() if sha_path.exists() else ""
    changed = old != fingerprint or not review.exists()
    sha_path.write_text(fingerprint + "\n", encoding="utf-8")
    if changed:
        review.write_text(
            "# Self-review\n\n"
            f"Issue: #{args.issue}\n"
            f"Checklist-SHA256: {fingerprint}\n"
            "Reviewed-HEAD: \n\n" +
            "\n".join(f"- {i} | PENDING |" for i, _s, _t in entries) + "\n",
            encoding="utf-8"
        )
    print(f"review_checklist_path={checklist.relative_to(ROOT)}")
    print(f"review_checklist_sha256={fingerprint}")
    print(f"self_review_path={review.relative_to(ROOT)}")
    print(f"checklist_changed={1 if changed else 0}")

def cmd_validate_review(args: argparse.Namespace) -> None:
    require("git", "gh")
    entries, fingerprint = effective_checklist(args.issue)
    base = state_dir(args.issue)
    prepared = base / "reviewer-checklist.sha256"
    review_path = base / "self-review.md"
    if not prepared.exists() or prepared.read_text(encoding="utf-8").strip() != fingerprint:
        fail("prepared Reviewer Checklist is stale; rerun prepare-self-review")
    if not review_path.exists():
        fail("self-review.md is missing")
    text = review_path.read_text(encoding="utf-8")
    def meta(name: str) -> str:
        matches = [x.split(":", 1)[1].strip() for x in text.splitlines() if x.startswith(name + ":")]
        if len(matches) != 1:
            fail(f"self-review metadata {name} missing/duplicated")
        return matches[0]
    if meta("Issue") != f"#{args.issue}":
        fail("self-review Issue metadata mismatch")
    if meta("Checklist-SHA256") != fingerprint:
        fail("self-review checklist SHA is stale")
    reviewed_head = meta("Reviewed-HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", reviewed_head):
        fail("Reviewed-HEAD must be a full 40-character commit SHA")
    current = run(["git", "rev-parse", "HEAD"], capture=True)
    if reviewed_head != current:
        fail("Reviewed-HEAD is stale")
    if run(["git", "status", "--porcelain", "--untracked-files=all"], capture=True):
        fail("worktree is dirty; commit/stash/remove repository changes before final self-review validation")
    expected = {i for i, _s, _t in entries}
    results: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|", 2)]
        if len(parts) != 3:
            fail("malformed self-review result line")
        item_id, status, detail = parts
        if item_id in expected:
            if item_id in results:
                fail(f"duplicate self-review result: {item_id}")
            results[item_id] = (status, detail)
    missing = expected - results.keys()
    if missing:
        fail("missing self-review result(s): " + ", ".join(sorted(missing)))
    passed = na = 0
    for item_id, (status, detail) in results.items():
        if status == "PASS":
            if not detail.startswith("Evidence:") or not detail[len("Evidence:"):].strip():
                fail(f"{item_id} PASS requires concrete Evidence:")
            passed += 1
        elif status == "N/A":
            if not detail.startswith("Reason:") or not detail[len("Reason:"):].strip():
                fail(f"{item_id} N/A requires concrete Reason:")
            na += 1
        elif status in {"PENDING", "FAIL"}:
            fail(f"{item_id} is {status}")
        else:
            fail(f"{item_id} has invalid status {status}")
    print("self_review_status=pass")
    print(f"reviewed_head={reviewed_head}")
    print(f"review_checklist_sha256={fingerprint}")
    print(f"pass={passed}")
    print(f"na={na}")
    print("fail=0")

def cmd_save_contract(args: argparse.Namespace) -> None:
    require("gh")
    issue_exists(args.issue)
    base = state_dir(args.issue)
    dest = base / "implementation-contract.md"
    sha_path = base / "implementation-contract.sha256"
    if args.path:
        data = Path(args.path).read_bytes()
    else:
        data = sys.stdin.buffer.read()
    if not data:
        fail("contract input is empty")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        fail("contract input must be UTF-8")
    sha = hashlib.sha256(data).hexdigest()
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != sha:
        fail("immutable contract mirror already exists with different content")
    dest.write_bytes(data)
    sha_path.write_text(f"{sha}  implementation-contract.md\n", encoding="utf-8")
    print(f"contract_path={dest.relative_to(ROOT)}")
    print(f"contract_sha256={sha}")

def cmd_checkpoint(args: argparse.Namespace) -> None:
    require("git", "gh")
    issue_exists(args.issue)
    base = state_dir(args.issue)
    path = base / "checkpoint.md"
    branch = run(["git", "branch", "--show-current"], capture=True)
    head = run(["git", "rev-parse", "HEAD"], capture=True)
    status = run(["git", "status", "--porcelain"], capture=True)
    issue = json.loads(run(["gh", "issue", "view", str(args.issue), "--json", "labels"], capture=True))
    phase = extract_phase(issue)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    body = ""
    if path.exists():
        current = path.read_text(encoding="utf-8")
        body = re.sub(r"\A---\n.*?\n---\n", "", current, flags=re.S)
    if not body.strip():
        body = """# Objective

- TODO

# Completed

- TODO

# Current state

- TODO

# Next action

- TODO

# Verification

- TODO

# Uncommitted work

- None

# Blockers

- None
"""
    if status:
        body = re.sub(r"# Uncommitted work\n\n.*?(?=\n# |\Z)",
                      "# Uncommitted work\n\n" + "\n".join(f"- `{x}`" for x in status.splitlines()) + "\n",
                      body, flags=re.S)
    front = (
        "---\n"
        f"schema: 1\nissue: {args.issue}\nphase: {json.dumps(phase)}\n"
        f"branch: {json.dumps(branch)}\nhead: {json.dumps(head)}\nupdated_at: {json.dumps(timestamp)}\n"
        f"working_tree: {json.dumps('dirty' if status else 'clean')}\n"
        "---\n\n"
    )
    path.write_text(front + body.lstrip(), encoding="utf-8")
    print(path.relative_to(ROOT))

def cmd_resume(args: argparse.Namespace) -> None:
    require("git", "gh")
    path = STATE / str(args.issue) / "checkpoint.md"
    if not path.exists():
        fail(f"checkpoint not found: {path.relative_to(ROOT)}")
    print(path.read_text(encoding="utf-8").rstrip())
    print("\n--- CURRENT CONTEXT ---")
    cmd_context(args)

def markdown_without_fences(text: str) -> str:
    kept: list[str] = []
    fence_char: str | None = None
    fence_size = 0
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            fence = match.group(1)
            if fence_char is None:
                fence_char, fence_size = fence[0], len(fence)
            elif fence[0] == fence_char and len(fence) >= fence_size:
                fence_char, fence_size = None, 0
            continue
        if fence_char is None:
            kept.append(line)
    return "\n".join(kept)


def markdown_headings(text: str) -> set[str]:
    heads = set()
    for line in markdown_without_fences(text).splitlines():
        match = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if match:
            heads.add(match.group(1).strip())
    return heads


def parse_document_schema(text: str, path: Path) -> tuple[int, list[str]]:
    body = markdown_without_fences(text)
    matches = [
        (line_number, line)
        for line_number, line in enumerate(body.splitlines(), start=1)
        if DOCUMENTATION_SCHEMA_MARKER in line
    ]
    label = str(path.relative_to(ROOT))
    if not matches:
        return 1, []
    if len(matches) > 1:
        return 1, [f"{label}: duplicate {DOCUMENTATION_SCHEMA_MARKER} markers"]
    line_number, line = matches[0]
    if line == DOCUMENTATION_SCHEMA_2_MARKER:
        return 2, []
    marker = re.fullmatch(r"<!-- agent-doc-schema: (-?\d+) -->", line)
    if marker:
        return 1, [f"{label}:{line_number}: unsupported documentation schema '{marker.group(1)}'"]
    return 1, [f"{label}:{line_number}: malformed {DOCUMENTATION_SCHEMA_MARKER} marker"]


def read_documentation_schema(manifest_path: Path) -> tuple[int, list[str]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return 1, [f"{manifest_path}: invalid template manifest: {exc}"]
    version = manifest.get("documentation_schema_version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or version not in DOCUMENTATION_SCHEMA_VERSIONS:
        return 1, [
            f"{manifest_path}: documentation_schema_version must be one of "
            f"{sorted(DOCUMENTATION_SCHEMA_VERSIONS)}, got {version!r}"
        ]
    return version, []


def markdown_link_targets(text: str) -> list[str]:
    body = markdown_without_fences(text)
    references: dict[str, str] = {}
    definition = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
    for match in definition.finditer(body):
        references[match.group(1).strip().casefold()] = match.group(2) or match.group(3)
    body = definition.sub("", body)
    targets: list[str] = []
    inline = re.compile(r"(?<!!)\[[^\]]+\]\(\s*(?:<([^>]+)>|([^\s)]+))")
    for match in inline.finditer(body):
        targets.append(match.group(1) or match.group(2))
    reference = re.compile(r"(?<!!)\[[^\]]+\]\[([^\]]+)\]")
    for match in reference.finditer(body):
        target = references.get(match.group(1).strip().casefold())
        if target:
            targets.append(target)
    return targets


def local_markdown_target(source: Path, target: str) -> Path | None:
    parts = urlsplit(target.strip())
    if parts.scheme.casefold() in {"http", "https", "mailto"} or not parts.path:
        return None
    path_text = unquote(parts.path)
    if Path(path_text).suffix.casefold() != ".md":
        return None
    return (source.parent / path_text).resolve()


def validate_markdown_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for target in markdown_link_targets(text):
        resolved = local_markdown_target(path, target)
        if resolved is not None and not resolved.is_file():
            errors.append(f"{path.relative_to(ROOT)}: broken local Markdown link '{target}'")
    return errors


def validate_doc(path: Path, doc_type: str, required_schema: int = 1) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    schema, schema_errors = parse_document_schema(text, path)
    errors.extend(schema_errors)
    if required_schema == 2 and schema != 2:
        errors.append(f"{path.relative_to(ROOT)}: requires {DOCUMENTATION_SCHEMA_2_MARKER}")
    if doc_type == "specification":
        required = SPEC_REQUIRED_V2 if schema == 2 else SPEC_REQUIRED_V1
    else:
        required = DESIGN_REQUIRED_V2 if schema == 2 else DESIGN_REQUIRED_V1
    headings = markdown_headings(text)
    errors.extend(
        f"{path.relative_to(ROOT)}: missing section '## {heading}'"
        for heading in required if heading not in headings
    )
    if schema == 2:
        errors.extend(validate_markdown_links(path, text))
    return errors


def documentation_warnings(path: Path, text: str, doc_type: str, schema: int) -> list[str]:
    if schema != 2:
        return []
    label = str(path.relative_to(ROOT))
    warnings: list[str] = []
    if len(text.encode("utf-8")) > DOCUMENTATION_SIZE_WARNING_BYTES:
        warnings.append(
            f"{label}: exceeds 50 KiB; review semantic ownership; size alone does not require splitting"
        )
    base = ROOT / "docs" / ("specs" if doc_type == "specification" else "design")
    linked = False
    for index in sorted(base.rglob("README.md")) if base.exists() else []:
        for target in markdown_link_targets(index.read_text(encoding="utf-8")):
            resolved = local_markdown_target(index, target)
            if resolved == path.resolve():
                linked = True
                break
        if linked:
            break
    if not linked:
        warnings.append(f"{label}: add a link from a README ownership index under {base.relative_to(ROOT)}")
    return warnings

def cmd_validate_docs(args: argparse.Namespace) -> None:
    errors: list[str] = []
    warnings: list[str] = []
    checked = 0
    required_schema, schema_errors = read_documentation_schema(TEMPLATE_FILES)
    errors.extend(schema_errors)
    for base, marker, typ in [
        (ROOT / "docs" / "specs", "<!-- agent-doc-type: specification -->", "specification"),
        (ROOT / "docs" / "design", "<!-- agent-doc-type: design -->", "design"),
    ]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            if marker not in text:
                errors.append(f"{path.relative_to(ROOT)}: missing required marker {marker}")
                continue
            checked += 1
            doc_errors = validate_doc(path, typ, required_schema)
            errors.extend(doc_errors)
            schema, _ = parse_document_schema(text, path)
            if schema == 2:
                warnings.extend(documentation_warnings(path, text, typ, schema))
    if errors:
        print("\n".join("error: " + x for x in errors), file=sys.stderr)
        raise SystemExit(1)
    for warning in warnings:
        print(f"warning: {warning}")
    print(f"docs_validation=pass checked={checked} warnings={len(warnings)} required_schema={required_schema}")


def cmd_new_doc(args: argparse.Namespace) -> None:
    kinds = {
        "specification": ("docs/templates/spec-template.md", "docs/specs", "-spec.md", "<Feature / Contract>"),
        "design": ("docs/templates/design-template.md", "docs/design", "-design.md", "<Feature / Architecture>"),
        "status": ("docs/templates/status-template.md", "docs/status", "-status.md", "<Area>"),
    }
    template_rel, dest_dir_rel, suffix, title_token = kinds[args.kind]
    slug = args.slug.strip().lower()
    slug = re.sub(r"[^a-z0-9/_-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-/")
    if not slug or ".." in slug.split("/"):
        fail("document slug must be a safe relative ASCII slug")
    leaf = slug.split("/")[-1]
    if not leaf.endswith(suffix[:-3]):
        leaf += suffix[:-3]
    parts = slug.split("/")[:-1] + [leaf + ".md"]
    dest = ROOT / dest_dir_rel / Path(*parts)
    if dest.exists():
        fail(f"document already exists: {dest.relative_to(ROOT)}")
    template = (ROOT / template_rel).read_text(encoding="utf-8")
    title = (args.title or slug.split("/")[-1]).replace("-", " ").replace("_", " ").strip().title()
    template = template.replace(title_token, title)
    if args.issue:
        template = template.replace("#<issue>", f"#{args.issue}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(template, encoding="utf-8")
    print(dest.relative_to(ROOT))


TEMPLATE_STATE = ROOT / ".agent" / "template-state.json"
TEMPLATE_FILES = ROOT / ".agent" / "template-files.json"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_template_manifest(source_root: Path) -> dict[str, Any]:
    manifest = source_root / ".agent" / "template-files.json"
    if not manifest.is_file():
        fail(f"template manifest not found: {manifest}")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid template manifest: {exc}")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        fail("template manifest must contain a non-empty files array")
    return data


def documentation_migrations(required_schema: int) -> list[str]:
    if required_schema < 2:
        return []
    migrations: list[str] = []
    for base in [ROOT / "docs" / "specs", ROOT / "docs" / "design"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name.casefold() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            schema, schema_errors = parse_document_schema(text, path)
            if not schema_errors and schema < required_schema:
                migrations.append(str(path.relative_to(ROOT)))
    return sorted(set(migrations))


def read_template_state() -> dict[str, Any]:
    if not TEMPLATE_STATE.exists():
        return {"schema_version": 1, "template_id": "ai-agent-project-template", "files": {}}
    try:
        data = json.loads(TEMPLATE_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid template state: {exc}")
    if not isinstance(data.get("files"), dict):
        data["files"] = {}
    return data


def write_template_state(state: dict[str, Any]) -> None:
    TEMPLATE_STATE.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_rel(path: str) -> Path:
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts:
        fail(f"unsafe manifest path: {path}")
    return rel


def cmd_update_template(args: argparse.Namespace) -> None:
    source_root = Path(args.source).expanduser().resolve()
    if not source_root.is_dir():
        fail(f"template source does not exist: {source_root}")
    manifest = load_template_manifest(source_root)
    source_schema, source_schema_errors = read_documentation_schema(
        source_root / ".agent" / "template-files.json"
    )
    if source_schema_errors:
        fail("\n".join(source_schema_errors))
    state = read_template_state()
    state["schema_version"] = 1
    state["template_id"] = manifest.get("template_id", "ai-agent-project-template")
    state["template_version"] = manifest.get("template_version", "unknown")
    state_files: dict[str, Any] = state.setdefault("files", {})
    applied = []
    adopted = []
    unchanged = []
    conflicts = []
    missing_source = []
    for entry in manifest["files"]:
        if isinstance(entry, str):
            rel_text = entry
        elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
            rel_text = entry["path"]
        else:
            fail("template manifest entries must be strings or objects with path")
        rel = safe_rel(rel_text)
        src = source_root / rel
        dst = ROOT / rel
        if not src.is_file():
            missing_source.append(rel_text)
            continue
        src_data = src.read_bytes()
        src_sha = hash_bytes(src_data)
        prev_sha = (state_files.get(rel_text) or {}).get("source_sha256")
        dst_exists = dst.exists()
        dst_sha = hash_bytes(dst.read_bytes()) if dst_exists and dst.is_file() else None
        if dst_exists and not dst.is_file():
            conflicts.append(rel_text + " (destination is not a file)")
            continue
        if dst_sha == src_sha:
            state_files[rel_text] = {"source_sha256": src_sha}
            unchanged.append(rel_text)
            continue
        if not dst_exists:
            if not args.check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src_data)
            state_files[rel_text] = {"source_sha256": src_sha}
            applied.append(rel_text)
            continue
        if prev_sha and dst_sha == prev_sha:
            if not args.check:
                dst.write_bytes(src_data)
            state_files[rel_text] = {"source_sha256": src_sha}
            applied.append(rel_text)
            continue
        if args.adopt and not prev_sha:
            incoming = dst.with_name(dst.name + ".incoming-template")
            if not args.check:
                incoming.write_bytes(src_data)
            state_files[rel_text] = {"source_sha256": dst_sha, "adopted_local_sha256": dst_sha}
            adopted.append(rel_text)
            conflicts.append(rel_text + " (adopted local file; incoming template written)")
            continue
        incoming = dst.with_name(dst.name + ".incoming-template")
        if not args.check:
            incoming.write_bytes(src_data)
        conflicts.append(rel_text)
    if missing_source:
        fail("manifest references missing source file(s): " + ", ".join(missing_source))
    if not args.check:
        write_template_state(state)
    print(f"template_update_mode={'check' if args.check else 'apply'}")
    print(f"applied={len(applied)}")
    print(f"unchanged={len(unchanged)}")
    print(f"adopted={len(adopted)}")
    print(f"conflicts={len(conflicts)}")
    migrations = documentation_migrations(source_schema)
    print(f"documentation_schema_required={source_schema}")
    print(f"documentation_migration_required={len(migrations)}")
    for item in migrations:
        print(f"MIGRATION_REQUIRED {item}")
    for item in conflicts:
        print(f"CONFLICT {item}")
    if conflicts:
        raise SystemExit(2)
    if migrations:
        raise SystemExit(3)


def cmd_refresh_template_manifest(args: argparse.Namespace) -> None:
    managed = []
    candidates = [
        "AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.AGENTS_WORKFLOW.md",
        ".agent/README.md", ".agent/template-files.json",
        ".github/ISSUE_TEMPLATE/feature.yml", ".github/ISSUE_TEMPLATE/bug.yml", ".github/ISSUE_TEMPLATE/config.yml", ".github/pull_request_template.md",
    ]
    candidates += [str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "agent-workflow").glob("*.md")]
    candidates += [str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "standards").rglob("*.md")]
    candidates += [str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "templates").glob("*.md")]
    candidates += [str(p.relative_to(ROOT)) for p in (ROOT / "scripts" / "agent").glob("*") if p.is_file()]
    candidates += ["docs/specs/agent-tooling-spec.md", "docs/specs/project-profile-spec.md"]
    # Presentation is included as template documentation, but project teams may replace it intentionally.
    candidates += ["docs/presentations/README.md", "docs/presentations/ai-agent-project-template-introduction.pptx"]
    for rel in sorted(set(candidates)):
        p = ROOT / rel
        if p.is_file():
            managed.append(rel)
    data = {
        "schema_version": 1,
        "template_id": "ai-agent-project-template",
        "template_version": args.version,
        "documentation_schema_version": 2,
        "files": managed,
    }
    TEMPLATE_FILES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"template_files={len(managed)}")
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init-project")
    s.add_argument("--stack", help="comma-separated: rust,node,python,dotnet,generic")
    s.add_argument("--application-type", help="comma-separated application types")
    s.add_argument("--target", help="comma-separated build/run target ids")
    s.add_argument("--cargo-clean", choices=["on", "off"])
    s.add_argument("--version-milestones", choices=["on", "off"])
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("setup-github")
    s.set_defaults(func=cmd_setup_github)

    s = sub.add_parser("run-hook")
    s.add_argument("name")
    s.add_argument("--component", action="append", default=[], help="component id; repeat to select multiple components")
    s.set_defaults(func=cmd_run_hook)

    s = sub.add_parser("start-feature-branch")
    s.add_argument("issue", type=int)
    s.add_argument("description")
    s.set_defaults(func=cmd_start_branch)

    s = sub.add_parser("ensure-version-milestone")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_milestone)

    s = sub.add_parser("agent-context")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_context)

    s = sub.add_parser("prepare-work-evidence")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_prepare_evidence)

    s = sub.add_parser("save-implementation-contract")
    s.add_argument("issue", type=int)
    s.add_argument("path", nargs="?")
    s.set_defaults(func=cmd_save_contract)

    s = sub.add_parser("prepare-self-review")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_prepare_review)

    s = sub.add_parser("validate-self-review")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_validate_review)

    s = sub.add_parser("save-work-checkpoint")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("resume-work")
    s.add_argument("issue", type=int)
    s.set_defaults(func=cmd_resume)

    s = sub.add_parser("new-doc")
    s.add_argument("kind", choices=["specification", "design", "status"])
    s.add_argument("slug")
    s.add_argument("--issue", type=int)
    s.add_argument("--title")
    s.set_defaults(func=cmd_new_doc)

    s = sub.add_parser("update-template")
    s.add_argument("--source", required=True, help="path to a newer ai-agent-project-template checkout")
    s.add_argument("--adopt", action="store_true", help="first-time adoption mode for existing projects")
    s.add_argument("--check", action="store_true", help="detect changes/conflicts without writing files")
    s.set_defaults(func=cmd_update_template)

    s = sub.add_parser("refresh-template-manifest")
    s.add_argument("--version", default="0.5.0")
    s.set_defaults(func=cmd_refresh_template_manifest)

    s = sub.add_parser("validate-docs")
    s.set_defaults(func=cmd_validate_docs)
    return p

def main() -> None:
    os.chdir(ROOT)
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
