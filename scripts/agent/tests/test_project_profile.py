import contextlib
import copy
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import test_doc_validation as support

module = support.module
ROOT = support.ROOT


def profile_v2():
    return {
        "schema_version": 2,
        "initialized": True,
        "project_name": "fixture",
        "components": [{
            "id": "root",
            "roots": ["."],
            "stacks": ["unknown-stack"],
            "application_types": ["generic"],
            "targets": [{
                "id": "any-target",
                "runnable_on": ["any"],
                "hooks": {"verify_quick": [], "verify_final": []},
            }],
            "hooks": {"verify_quick": [], "verify_final": []},
        }],
        "branch": {"prefix": "feature", "max_slug_length": 48},
        "milestones": {"enabled": False, "version_source": "auto"},
        "hooks": {"branch_switch": [], "verify_quick": [], "verify_final": []},
    }


class ProjectProfileValidationTests(unittest.TestCase):
    def test_schema1_profile_remains_readable(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "project.json"
            config.write_text(json.dumps({
                "schema_version": 1,
                "initialized": True,
                "stacks": ["rust"],
                "hooks": {"verify_quick": ["echo legacy"]},
            }), encoding="utf-8")
            with patch.object(module, "CONFIG", config):
                loaded = module.load_config()
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(loaded["hooks"]["verify_quick"], ["echo legacy"])

    def test_schema2_profile_accepts_unknown_stack_ids(self):
        profile = profile_v2()
        self.assertIs(module.validate_profile_v2(profile), profile)

    def test_schema2_validation_rejects_invalid_component_and_target_data(self):
        mutations = [
            ("duplicate component", lambda p: p["components"].append(copy.deepcopy(p["components"][0]))),
            ("unsafe root", lambda p: p["components"][0].update(roots=["../outside"])),
            ("empty stack", lambda p: p["components"][0].update(stacks=[""])),
            ("comma in root", lambda p: p["components"][0].update(roots=["src,docs"])),
            ("equals in root", lambda p: p["components"][0].update(roots=["src=docs"])),
            ("newline in root", lambda p: p["components"][0].update(roots=["src\napplication_profile=docs/standards/application-profiles/embedded.md"])),
            ("control in root", lambda p: p["components"][0].update(roots=["src\x01app"])),
            ("comma in stack", lambda p: p["components"][0].update(stacks=["custom,stack"])),
            ("equals in stack", lambda p: p["components"][0].update(stacks=["custom=stack"])),
            ("line separator in stack", lambda p: p["components"][0].update(stacks=["custom\u2028stack"])),
            ("control in stack", lambda p: p["components"][0].update(stacks=["custom\x7fstack"])),
            ("comma in component id", lambda p: p["components"][0].update(id="root,api")),
            ("equals in component id", lambda p: p["components"][0].update(id="root=api")),
            ("newline in target id", lambda p: p["components"][0]["targets"][0].update(id="target\nother")),
            ("unknown application type", lambda p: p["components"][0].update(application_types=["browser"])),
            ("duplicate target", lambda p: p["components"][0]["targets"].append(copy.deepcopy(p["components"][0]["targets"][0]))),
            ("invalid runnable host", lambda p: p["components"][0]["targets"][0].update(runnable_on=["freebsd"])),
            ("component branch hook", lambda p: p["components"][0].update(hooks={"verify_quick": [], "verify_final": [], "branch_switch": []})),
            ("empty hook command", lambda p: p["hooks"].update(verify_final=["  "])),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                profile = profile_v2()
                mutate(profile)
                with self.assertRaises(SystemExit):
                    module.validate_profile_v2(profile)


class ProjectProfileInitTests(unittest.TestCase):
    def test_init_creates_schema2_root_component_and_neutral_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / ".agent" / "project.json"
            with patch.object(module, "ROOT", root), patch.object(module, "CONFIG", config), patch.object(module, "merge_gitignore"):
                args = module.build_parser().parse_args([
                    "init-project", "--stack", "swift,custom-stack",
                    "--application-type", "mobile,library",
                    "--target", "ios-device,macos-arm64",
                ])
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    module.cmd_init(args)
            data = json.loads(config.read_text(encoding="utf-8"))
            component = data["components"][0]
            summary = (root / "docs/agents/project.md").read_text(encoding="utf-8")

        self.assertEqual(data["schema_version"], 2)
        self.assertIs(module.validate_profile_v2(data), data)
        self.assertEqual(component["id"], "root")
        self.assertEqual(component["roots"], ["."])
        self.assertEqual(component["stacks"], ["swift", "custom-stack"])
        self.assertEqual(component["application_types"], ["mobile", "library"])
        self.assertEqual([target["id"] for target in component["targets"]], ["ios-device", "macos-arm64"])
        self.assertTrue(all(target["runnable_on"] == ["any"] for target in component["targets"]))
        self.assertEqual(data["hooks"]["branch_switch"], [])
        self.assertNotIn("cargo clean", component["hooks"]["verify_final"])
        self.assertIn("| ID | Roots | Stacks | Application types | Targets (`runnable_on`) |", summary)
        self.assertIn("| `root` | `.` | `swift`, `custom-stack` | `mobile`, `library` |", summary)
        self.assertIn("cargo_clean=off", output.getvalue())

    def test_cargo_clean_is_added_only_when_explicitly_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / ".agent" / "project.json"
            with patch.object(module, "ROOT", root), patch.object(module, "CONFIG", config), patch.object(module, "merge_gitignore"):
                args = module.build_parser().parse_args(["init-project", "--stack", "rust", "--cargo-clean", "on"])
                with contextlib.redirect_stdout(io.StringIO()):
                    module.cmd_init(args)
            data = json.loads(config.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"]["branch_switch"], ["cargo clean"])

    def test_rust_cargo_clean_is_off_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / ".agent" / "project.json"
            with patch.object(module, "ROOT", root), patch.object(module, "CONFIG", config), patch.object(module, "merge_gitignore"):
                args = module.build_parser().parse_args(["init-project", "--stack", "rust"])
                with contextlib.redirect_stdout(io.StringIO()):
                    module.cmd_init(args)
            data = json.loads(config.read_text(encoding="utf-8"))
        self.assertEqual(data["hooks"]["branch_switch"], [])

    def test_init_rejects_manifest_unsafe_stack_before_saving(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / ".agent" / "project.json"
            with patch.object(module, "ROOT", root), patch.object(module, "CONFIG", config), patch.object(module, "merge_gitignore"):
                args = module.build_parser().parse_args(["init-project", "--stack", "custom\nstack"])
                with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
                    module.cmd_init(args)
            self.assertFalse(config.exists())


class ProjectProfileHookTests(unittest.TestCase):
    def test_python_hook_uses_available_python_alias(self):
        available = {"python": None, "python3": "/usr/bin/python3"}
        with patch.object(module.shutil, "which", side_effect=lambda name: available.get(name)), patch.object(module.subprocess, "run") as run_command, contextlib.redirect_stdout(io.StringIO()):
            module.shell("python scripts/agent/agent_tool.py validate-docs")
        self.assertEqual(run_command.call_args.args[0], "python3 scripts/agent/agent_tool.py validate-docs")

    def test_schema2_hook_groups_global_components_then_compatible_targets(self):
        config = profile_v2()
        config["hooks"]["verify_quick"] = ["global"]
        first = config["components"][0]
        first.update(id="first", hooks={"verify_quick": ["first-component"], "verify_final": []})
        first["targets"] = [
            {"id": "host-ok", "runnable_on": ["linux"], "hooks": {"verify_quick": ["first-target"], "verify_final": []}},
            {"id": "host-skip", "runnable_on": ["windows"], "hooks": {"verify_quick": ["skipped-target"], "verify_final": []}},
        ]
        second = copy.deepcopy(first)
        second.update(id="second", hooks={"verify_quick": ["second-component"], "verify_final": []})
        second["targets"] = [
            {"id": "second-host-ok", "runnable_on": ["any"], "hooks": {"verify_quick": ["second-target"], "verify_final": []}},
            {"id": "second-host-skip", "runnable_on": ["windows"], "hooks": {"verify_quick": ["second-skipped-target"], "verify_final": []}},
        ]
        config["components"].append(second)
        commands = []
        stdout = io.StringIO()
        args = Namespace(name="verify_quick", component=[])
        with patch.object(module, "load_config", return_value=config), patch.object(module, "runtime_host", return_value="linux"), patch.object(module, "shell", side_effect=commands.append), contextlib.redirect_stdout(stdout):
            module.cmd_run_hook(args)

        self.assertEqual(commands, ["global", "first-component", "second-component", "first-target", "second-target"])
        self.assertEqual(stdout.getvalue().splitlines(), [
            "SKIPPED_TARGET_VERIFICATION component=first target=host-skip reason=host_mismatch",
            "SKIPPED_TARGET_VERIFICATION component=second target=second-host-skip reason=host_mismatch",
            "hook=verify_quick commands=5",
        ])

    def test_component_selection_scopes_component_and_target_hooks(self):
        config = profile_v2()
        config["hooks"]["verify_quick"] = ["global"]
        first = config["components"][0]
        first.update(id="first", hooks={"verify_quick": ["first"], "verify_final": []}, targets=[])
        first["targets"] = [
            {"id": "first-target", "runnable_on": ["any"], "hooks": {"verify_quick": ["first-target-command"], "verify_final": []}},
        ]
        second = copy.deepcopy(first)
        second.update(
            id="second",
            hooks={"verify_quick": ["second"], "verify_final": []},
            targets=[
                {"id": "second-target", "runnable_on": ["any"], "hooks": {"verify_quick": ["second-target-command"], "verify_final": []}},
                {"id": "second-host-skip", "runnable_on": ["windows"], "hooks": {"verify_quick": ["second-skipped-target"], "verify_final": []}},
            ],
        )
        config["components"].append(second)
        commands = []
        stdout = io.StringIO()
        args = Namespace(name="verify_quick", component=["second"])
        with patch.object(module, "load_config", return_value=config), patch.object(module, "runtime_host", return_value="linux"), patch.object(module, "shell", side_effect=commands.append), contextlib.redirect_stdout(stdout):
            module.cmd_run_hook(args)
        self.assertEqual(commands, ["global", "second", "second-target-command"])
        self.assertEqual(stdout.getvalue().splitlines(), [
            "SKIPPED_TARGET_VERIFICATION component=second target=second-host-skip reason=host_mismatch",
            "hook=verify_quick commands=3",
        ])

    def test_schema1_hook_behavior_is_kept(self):
        config = {"schema_version": 1, "hooks": {"verify_quick": ["legacy"]}}
        commands = []
        with patch.object(module, "load_config", return_value=config), patch.object(module, "shell", side_effect=commands.append), contextlib.redirect_stdout(io.StringIO()):
            module.cmd_run_hook(Namespace(name="verify_quick", component=[]))
        self.assertEqual(commands, ["legacy"])

    def test_invalid_profile_fails_before_context_output_or_hook_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "project.json"
            state = root / "state"
            issue = {
                "number": 7,
                "labels": [{"name": "phase:review"}],
                "url": "https://example.invalid/issues/7",
                "body": "## Affected components\n\n- `root`\n",
            }

            def fake_run(args, *, capture=False, check=True):
                if args[:3] == ["gh", "issue", "view"]:
                    return json.dumps(issue)
                if args == ["git", "branch", "--show-current"]:
                    return "feature/7-demo"
                if args == ["git", "rev-parse", "HEAD"]:
                    return "a" * 40
                if args[:3] == ["gh", "repo", "view"]:
                    return "main"
                if args == ["git", "status", "--porcelain"]:
                    return ""
                if args[:3] == ["gh", "pr", "list"]:
                    return "{}"
                raise AssertionError(f"unexpected command: {args}")

            for field, bad_value in (("roots", "src\napplication_profile=docs/standards/application-profiles/embedded.md"), ("stacks", "custom,stack")):
                with self.subTest(field=field):
                    config = profile_v2()
                    config["components"][0][field] = [bad_value]
                    config_path.write_text(json.dumps(config), encoding="utf-8")
                    context_output = io.StringIO()
                    with patch.object(module, "CONFIG", config_path), patch.object(module, "require"), patch.object(module, "run", side_effect=fake_run), patch.object(module, "STATE", state), contextlib.redirect_stdout(context_output), self.assertRaises(SystemExit):
                        module.cmd_context(Namespace(issue=7))
                    self.assertEqual(context_output.getvalue(), "")

                    shell = Mock()
                    with patch.object(module, "CONFIG", config_path), patch.object(module, "shell", shell), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                        module.cmd_run_hook(Namespace(name="verify_quick", component=[]))
                    shell.assert_not_called()


class ProjectProfileDocumentationRuleTests(unittest.TestCase):
    def test_agents_does_not_require_the_generated_project_summary(self):
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("Then read `docs/agents/project.md`.", instructions)
        self.assertIn("`.agent/project.json` as the machine-readable project authority", instructions)
        self.assertIn("optional generated human-readable summary", instructions)


class AffectedComponentRoutingTests(unittest.TestCase):
    def test_canonical_affected_components_section(self):
        body = "## Affected components\n\n- `desktop`\n- `server`\n\n## Acceptance criteria\n"
        self.assertEqual(module.parse_affected_components(body), ["desktop", "server"])

    def test_normalized_issue_3_affected_components_section_routes_root(self):
        issue = {
            "number": 3,
            "labels": [{"name": "phase:review"}],
            "url": "https://github.com/puchinya/ai-agent-project-template/issues/3",
            "body": """## Objective

Generalize project profiles and context routing.

Repository-wide agent tooling, workflow documentation, standards, and the template manifest are in scope.

## Affected components

- `root`

## Functional requirements

- Preserve schema 1 compatibility.
""",
        }

        def fake_run(args, *, capture=False, check=True):
            if args[:3] == ["gh", "issue", "view"]:
                return json.dumps(issue)
            if args == ["git", "branch", "--show-current"]:
                return "feature/3-project-profiles-and-context-routing"
            if args == ["git", "rev-parse", "HEAD"]:
                return "a" * 40
            if args[:3] == ["gh", "repo", "view"]:
                return "main"
            if args == ["git", "status", "--porcelain"]:
                return ""
            if args[:3] == ["gh", "pr", "list"]:
                return "{\"number\":4,\"url\":\"https://github.com/puchinya/ai-agent-project-template/pull/4\"}"
            raise AssertionError(f"unexpected command: {args}")

        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()
            with patch.object(module, "require"), patch.object(module, "run", side_effect=fake_run), patch.object(module, "load_config", return_value=profile_v2()), patch.object(module, "runtime_host_label", return_value="macos/arm64"), patch.object(module, "STATE", Path(temp)), contextlib.redirect_stdout(output):
                module.cmd_context(Namespace(issue=3))
        self.assertIn("issue=3", output.getvalue())
        self.assertIn("affected_components=root", output.getvalue())
        self.assertIn("component.root.roots=.", output.getvalue())

    def test_single_component_defaults_and_multi_component_requires_explicit_section(self):
        profile = profile_v2()
        self.assertEqual(module.context_profile_components(profile, "")[2], ["root"])
        second = copy.deepcopy(profile["components"][0])
        second["id"] = "api"
        profile["components"].append(second)
        with self.assertRaises(SystemExit):
            module.context_profile_components(profile, "")

    def test_unknown_and_malformed_affected_components_are_errors(self):
        profile = profile_v2()
        profile["components"][0]["id"] = "desktop"
        with self.assertRaises(SystemExit):
            module.context_profile_components(profile, "## Affected components\n\n- `server`\n")
        with self.assertRaises(SystemExit):
            module.context_profile_components(profile, "## Affected components\n\n- desktop\n")

    def test_application_profile_paths_are_derived_from_component_types(self):
        profile = profile_v2()
        profile["components"][0]["application_types"] = ["mobile", "generic", "desktop-gui"]
        schema, components, ids = module.context_profile_components(profile, "")
        profile_types = sorted({
            item for component in components for item in component["application_types"] if item != "generic"
        })
        self.assertEqual(schema, 2)
        self.assertEqual(ids, ["root"])
        self.assertEqual(profile_types, ["desktop-gui", "mobile"])

    def test_agent_context_prints_compact_issue_routing_without_issue_body(self):
        config = profile_v2()
        desktop = config["components"][0]
        desktop.update(
            id="desktop",
            roots=["apps/desktop"],
            application_types=["mobile", "generic", "desktop-gui"],
            targets=[{"id": "ios-device", "runnable_on": ["macos"], "hooks": {"verify_quick": [], "verify_final": []}}],
        )
        api = copy.deepcopy(desktop)
        api.update(id="api", roots=["services/api"], application_types=["server"], targets=[])
        config["components"].append(api)
        issue = {
            "number": 7,
            "labels": [{"name": "phase:implementation"}],
            "url": "https://example.invalid/issues/7",
            "body": "## Affected components\n\n- `api`\n- `desktop`\n\n## Details\n\nPrivate issue text must not be copied.\n",
        }

        def fake_run(args, *, capture=False, check=True):
            if args[:3] == ["gh", "issue", "view"]:
                return json.dumps(issue)
            if args == ["git", "branch", "--show-current"]:
                return "feature/7-demo"
            if args == ["git", "rev-parse", "HEAD"]:
                return "a" * 40
            if args[:3] == ["gh", "repo", "view"]:
                return "main"
            if args == ["git", "status", "--porcelain"]:
                return ""
            if args[:3] == ["gh", "pr", "list"]:
                return "{}"
            raise AssertionError(f"unexpected command: {args}")

        with tempfile.TemporaryDirectory() as temp:
            output = io.StringIO()
            with patch.object(module, "require"), patch.object(module, "run", side_effect=fake_run), patch.object(module, "load_config", return_value=config), patch.object(module, "runtime_host_label", return_value="macos/arm64"), patch.object(module, "STATE", Path(temp)), contextlib.redirect_stdout(output):
                module.cmd_context(Namespace(issue=7))
        text = output.getvalue()
        self.assertIn("profile_schema=2", text)
        self.assertIn("runtime_host=macos/arm64", text)
        self.assertIn("affected_components=desktop,api", text)
        self.assertIn("component.desktop.roots=apps/desktop", text)
        self.assertIn("component.api.application_types=server", text)
        self.assertIn("application_profile=docs/standards/application-profiles/desktop-gui.md", text)
        self.assertIn("application_profile=docs/standards/application-profiles/mobile.md", text)
        self.assertIn("application_profile=docs/standards/application-profiles/server.md", text)
        self.assertNotIn("Private issue text", text)


if __name__ == "__main__":
    unittest.main()
