import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("agent_tool", ROOT / "scripts/agent/agent_tool.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def document(doc_type, schema=1, *, omit=None, extra=""):
    if doc_type == "specification":
        headings = module.SPEC_REQUIRED_V2 if schema == 2 else module.SPEC_REQUIRED_V1
        type_marker = "<!-- agent-doc-type: specification -->"
    else:
        headings = module.DESIGN_REQUIRED_V2 if schema == 2 else module.DESIGN_REQUIRED_V1
        type_marker = "<!-- agent-doc-type: design -->"
    marker = module.DOCUMENTATION_SCHEMA_2_MARKER + "\n" if schema == 2 else ""
    sections = [f"## {heading}\n\nContent." for heading in headings if heading != omit]
    return f"{type_marker}\n{marker}# Example\n\n" + "\n\n".join(sections) + "\n\n" + extra


def write_doc(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_manifest(path, version=1, *, missing=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": 1, "template_id": "fixture", "template_version": "0.4.0", "files": []}
    if not missing:
        data["documentation_schema_version"] = version
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class DocumentationSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.root_patch = patch.object(module, "ROOT", self.root)
        self.files_patch = patch.object(module, "TEMPLATE_FILES", self.root / ".agent/template-files.json")
        self.state_patch = patch.object(module, "TEMPLATE_STATE", self.root / ".agent/template-state.json")
        self.root_patch.start()
        self.files_patch.start()
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.addCleanup(self.files_patch.stop)
        self.addCleanup(self.root_patch.stop)
        self.set_manifest(1)

    def set_manifest(self, version=1, *, missing=False):
        return write_manifest(module.TEMPLATE_FILES, version, missing=missing)

    def capture(self, call):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = call()
        return result, stdout.getvalue(), stderr.getvalue()

    def capture_exit(self, call):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                call()
            except SystemExit as exc:
                return exc.code, stdout.getvalue(), stderr.getvalue()
        return 0, stdout.getvalue(), stderr.getvalue()

    def test_v1_documents_remain_valid_under_v1_manifest(self):
        write_doc(self.root, "docs/specs/item.md", document("specification", 1))
        write_doc(self.root, "docs/design/item.md", document("design", None))
        _, stdout, _ = self.capture(lambda: module.cmd_validate_docs(Namespace()))
        self.assertIn("docs_validation=pass", stdout)

    def test_v1_manifest_also_accepts_schema2_documents_and_keeps_warnings_nonfatal(self):
        path = write_doc(self.root, "docs/specs/item.md", document("specification", 2, extra="x" * 52_000))
        _, stdout, _ = self.capture(lambda: module.cmd_validate_docs(Namespace()))
        self.assertTrue(path.is_file())
        self.assertIn("warning: docs/specs/item.md: exceeds 50 KiB", stdout)
        self.assertIn("warning: docs/specs/item.md: add a link from a README ownership index", stdout)
        self.assertIn("docs_validation=pass", stdout)

    def test_schema1_document_is_rejected_by_schema2_manifest(self):
        self.set_manifest(2)
        write_doc(self.root, "docs/specs/item.md", document("specification", 1))
        with self.assertRaises(SystemExit) as exc:
            self.capture(lambda: module.cmd_validate_docs(Namespace()))
        self.assertEqual(exc.exception.code, 1)

    def test_valid_schema2_spec_and_design_accept_links_and_nested_indexes(self):
        self.set_manifest(2)
        write_doc(self.root, "docs/specs/related.md", document("specification", 2))
        write_doc(self.root, "docs/specs/item.md", document("specification", 2, extra="[Related](related.md#scope)\n"))
        write_doc(self.root, "docs/specs/nested/README.md", "[Item](../item.md)\n")
        write_doc(self.root, "docs/design/related.md", document("design", 2))
        write_doc(self.root, "docs/design/item.md", document("design", 2, extra="[Related](related.md#scope)\n"))
        write_doc(self.root, "docs/design/nested/README.md", "[Item](../item.md)\n")
        _, stdout, _ = self.capture(lambda: module.cmd_validate_docs(Namespace()))
        self.assertIn("docs_validation=pass", stdout)

    def test_missing_required_heading_is_reported(self):
        missing_headings = [
            ("specification", "Overview"),
            ("specification", "Semantic ownership"),
            ("specification", "Quality attributes"),
            ("design", "Architecture invariants"),
            ("design", "Quality attributes and operations"),
        ]
        for doc_type, heading in missing_headings:
            with self.subTest(doc_type=doc_type, heading=heading):
                path = write_doc(
                    self.root, f"docs/{'specs' if doc_type == 'specification' else 'design'}/item.md",
                    document(doc_type, 2, omit=heading),
                )
                errors = module.validate_doc(path, doc_type, 2)
                self.assertTrue(any(f"missing section '## {heading}'" in error for error in errors))

    def test_schema2_missing_heading_is_not_migration_and_fails_validate_docs(self):
        self.set_manifest(2)
        path = write_doc(
            self.root, "docs/specs/item.md", document("specification", 2, omit="Purpose")
        )
        self.assertEqual(module.documentation_migrations(2), [])
        code, _, stderr = self.capture_exit(lambda: module.cmd_validate_docs(Namespace()))
        self.assertEqual(code, 1)
        self.assertIn(f"{path.relative_to(self.root)}: missing section '## Purpose'", stderr)

    def test_schema2_broken_link_is_not_migration_and_fails_validate_docs(self):
        self.set_manifest(2)
        path = write_doc(
            self.root, "docs/specs/item.md",
            document("specification", 2, extra="[Missing](missing.md)\n"),
        )
        self.assertEqual(module.documentation_migrations(2), [])
        code, _, stderr = self.capture_exit(lambda: module.cmd_validate_docs(Namespace()))
        self.assertEqual(code, 1)
        self.assertIn("broken local Markdown link 'missing.md'", stderr)

    def test_schema1_document_is_migration_when_schema2_is_required(self):
        explicit_schema = write_doc(
            self.root, "docs/specs/item.md", document("specification", 1)
        )
        missing_marker = write_doc(
            self.root, "docs/design/legacy-design.md", document("design", None)
        )
        self.assertEqual(module.documentation_migrations(2), [
            str(missing_marker.relative_to(self.root)),
            str(explicit_schema.relative_to(self.root)),
        ])

    def test_invalid_schema_markers_are_not_migrations_and_fail_validate_docs(self):
        self.set_manifest(2)
        cases = [
            ("<!-- agent-doc-schema two -->", "malformed"),
            ("<!-- agent-doc-schema: 2 -->\n<!-- agent-doc-schema: 2 -->", "duplicate"),
            ("<!-- agent-doc-schema: 9 -->", "unsupported"),
        ]
        for index, (marker, expected_error) in enumerate(cases):
            with self.subTest(expected_error=expected_error):
                write_doc(
                    self.root, f"docs/specs/item-{index}-spec.md",
                    document("specification", None).replace("# Example", marker + "\n# Example"),
                )
                self.assertEqual(module.documentation_migrations(2), [])
                code, _, stderr = self.capture_exit(lambda: module.cmd_validate_docs(Namespace()))
                self.assertEqual(code, 1)
                self.assertIn(expected_error, stderr)

    def test_bad_document_markers_are_rejected(self):
        cases = [
            ("<!-- agent-doc-schema two -->", "malformed"),
            ("<!-- agent-doc-schema: 2 -->\n<!-- agent-doc-schema: 2 -->", "duplicate"),
            ("<!-- agent-doc-schema: 1 -->", "unsupported"),
            ("<!-- agent-doc-schema: 9 -->", "unsupported"),
        ]
        for marker, expected in cases:
            with self.subTest(expected=expected):
                path = write_doc(
                    self.root, "docs/specs/item.md",
                    document("specification", None).replace("# Example", marker + "\n# Example"),
                )
                _, errors = module.parse_document_schema(path.read_text(encoding="utf-8"), path)
                self.assertTrue(any(expected in error for error in errors))

    def test_invalid_manifest_schema_values_are_rejected(self):
        for version in (0, 3, True, "2", None):
            with self.subTest(version=version):
                path = write_manifest(self.root / "manifest.json", version)
                _, errors = module.read_documentation_schema(path)
                self.assertTrue(errors and "documentation_schema_version" in errors[0])

    def test_old_manifest_without_schema_defaults_to_v1(self):
        path = write_manifest(self.root / "manifest.json", missing=True)
        self.assertEqual(module.read_documentation_schema(path), (1, []))

    def test_inline_links_distinguish_local_markdown_targets(self):
        (self.root / "docs/specs/related.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "docs/specs/related.md").write_text("# Related", encoding="utf-8")
        cases = [
            ("related.md", False), ("missing.md#section", True), ("asset.pdf#page=2", False),
            ("https://example.com/guide.md", False), ("mailto:docs@example.com", False),
            ("#local-section", False),
        ]
        for target, has_error in cases:
            with self.subTest(target=target):
                path = write_doc(self.root, "docs/specs/item.md", f"[Related]({target})\n")
                errors = module.validate_markdown_links(path, path.read_text(encoding="utf-8"))
                self.assertEqual(bool(errors), has_error)

        path = write_doc(self.root, "docs/specs/item.md", "![Image](missing.md)\n")
        self.assertEqual(module.validate_markdown_links(path, path.read_text(encoding="utf-8")), [])

    def test_fenced_links_are_ignored_and_reference_links_are_checked(self):
        path = write_doc(
            self.root, "docs/specs/item.md",
            "```md\n[Ignored](missing.md)\n```\n[Related][guide]\n\n[guide]: related.md\n",
        )
        (self.root / "docs/specs/related.md").write_text("# Related", encoding="utf-8")
        self.assertEqual(module.validate_markdown_links(path, path.read_text(encoding="utf-8")), [])
        path.write_text(path.read_text(encoding="utf-8").replace("related.md", "missing.md"), encoding="utf-8")
        self.assertTrue(module.validate_markdown_links(path, path.read_text(encoding="utf-8")))

    def test_size_warning_and_nested_index_warning_behavior(self):
        path = write_doc(self.root, "docs/specs/nested/item.md", document("specification", 2, extra="x" * 52_000))
        text = path.read_text(encoding="utf-8")
        warnings = module.documentation_warnings(path, text, "specification", 2)
        self.assertTrue(any("exceeds 50 KiB" in warning and "size alone does not require splitting" in warning for warning in warnings))
        self.assertTrue(any("README ownership index" in warning for warning in warnings))
        write_doc(self.root, "docs/specs/README.md", "[Item](nested/item.md)\n")
        warnings = module.documentation_warnings(path, text, "specification", 2)
        self.assertFalse(any("README ownership index" in warning for warning in warnings))

    def test_new_doc_uses_schema2_template(self):
        template = document("specification", 2).replace(
            "# Example", "# <Feature / Contract>\n\n- Owning Issue: #<issue>"
        )
        write_doc(self.root, "docs/templates/spec-template.md", template)
        module.cmd_new_doc(Namespace(kind="specification", slug="sample", title="Sample", issue=42))
        generated = (self.root / "docs/specs/sample-spec.md").read_text(encoding="utf-8")
        self.assertIn("<!-- agent-doc-schema: 2 -->", generated)
        self.assertIn("Owning Issue: #42", generated)

    def test_new_doc_design_uses_schema2_and_nonbroken_related_spec_placeholder(self):
        source_template = (ROOT / "docs/templates/design-template.md").read_text(encoding="utf-8")
        write_doc(self.root, "docs/templates/design-template.md", source_template)
        _, output, _ = self.capture(
            lambda: module.cmd_new_doc(
                Namespace(kind="design", slug="sample", title="Sample", issue=42)
            )
        )
        generated_path = self.root / "docs/design/sample-design.md"
        generated = generated_path.read_text(encoding="utf-8")
        self.assertIn("docs/design/sample-design.md", output)
        self.assertIn("<!-- agent-doc-schema: 2 -->", generated)
        self.assertFalse(set(module.DESIGN_REQUIRED_V2) - module.markdown_headings(generated))
        for target in module.markdown_link_targets(generated):
            resolved = module.local_markdown_target(generated_path, target)
            self.assertTrue(resolved is None or resolved.is_file(), target)
        self.assertNotIn("TBD", module.markdown_link_targets(generated))

    def test_templates_match_v2_heading_contract(self):
        spec_text = (ROOT / "docs/templates/spec-template.md").read_text(encoding="utf-8")
        design_text = (ROOT / "docs/templates/design-template.md").read_text(encoding="utf-8")
        self.assertFalse(set(module.SPEC_REQUIRED_V2) - module.markdown_headings(spec_text))
        self.assertFalse(set(module.DESIGN_REQUIRED_V2) - module.markdown_headings(design_text))

    def test_manifest_refresh_defaults_to_060_and_schema2(self):
        for directory in (
            "docs/agent-workflow", "docs/standards", "docs/templates", "docs/specs",
            "docs/design", "scripts/agent", ".agent", ".github/workflows",
        ):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / "docs/standards/application-profiles").mkdir(parents=True, exist_ok=True)
        write_doc(self.root, "docs/specs/agent-tooling-spec.md", "shared contract\n")
        write_doc(self.root, "docs/specs/project-profile-spec.md", "shared profile contract\n")
        write_doc(self.root, "docs/specs/agent-workflow-assurance-spec.md", "shared assurance contract\n")
        write_doc(self.root, "docs/design/agent-workflow-assurance-design.md", "shared assurance design\n")
        write_doc(self.root, ".github/workflows/template-ci.yml", "name: Template CI\n")
        write_doc(self.root, "docs/specs/product-feature-spec.md", "project spec\n")
        write_doc(self.root, "docs/design/product-feature-design.md", "project design\n")
        write_doc(self.root, "docs/standards/application-profiles/desktop-gui.md", "conditional standard\n")
        write_doc(self.root, "docs/specs/README.md", "spec index\n")
        write_doc(self.root, "docs/design/README.md", "design index\n")
        args = Namespace(version=module.build_parser().parse_args(["refresh-template-manifest"]).version)
        module.cmd_refresh_template_manifest(args)
        data = json.loads(module.TEMPLATE_FILES.read_text(encoding="utf-8"))
        self.assertEqual(data["template_version"], "0.6.0")
        self.assertEqual(data["documentation_schema_version"], 2)
        self.assertIn("docs/specs/agent-tooling-spec.md", data["files"])
        self.assertIn("docs/specs/project-profile-spec.md", data["files"])
        self.assertIn("docs/specs/agent-workflow-assurance-spec.md", data["files"])
        self.assertIn("docs/design/agent-workflow-assurance-design.md", data["files"])
        self.assertIn(".github/workflows/template-ci.yml", data["files"])
        self.assertIn("docs/standards/application-profiles/desktop-gui.md", data["files"])
        self.assertNotIn("docs/specs/product-feature-spec.md", data["files"])
        self.assertNotIn("docs/design/product-feature-design.md", data["files"])
        self.assertNotIn("docs/design/project-profile-context-design.md", data["files"])
        self.assertNotIn("docs/specs/README.md", data["files"])
        self.assertNotIn("docs/design/README.md", data["files"])

    def updater_fixture(self, required_schema=2, doc_schema=1, *, state=True):
        source, destination = self.root / "source", self.root / "destination"
        write_doc(source, "managed.md", "new template content\n")
        source_manifest = source / ".agent/template-files.json"
        source_manifest.parent.mkdir(parents=True, exist_ok=True)
        data = {"template_id": "fixture", "template_version": "0.4.0", "files": ["managed.md"]}
        if required_schema is not ...:
            data["documentation_schema_version"] = required_schema
        source_manifest.write_text(json.dumps(data), encoding="utf-8")
        write_doc(destination, "managed.md", "old template content\n")
        write_doc(destination, "docs/specs/item.md", document("specification", doc_schema))
        state_path = destination / ".agent/template-state.json"
        if state:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            old_hash = hashlib.sha256(b"old template content\n").hexdigest()
            state_path.write_text(json.dumps({"files": {"managed.md": {"source_sha256": old_hash}}}), encoding="utf-8")
        return source, destination, state_path

    def run_update(self, source, destination, state_path, *, check=True):
        with patch.object(module, "ROOT", destination), patch.object(module, "TEMPLATE_STATE", state_path):
            return module.cmd_update_template(Namespace(source=str(source), check=check, adopt=False))

    def shared_spec_update_fixture(self, *, previous_shared=None, local_shared=None):
        source, destination = self.root / "shared-source", self.root / "shared-destination"
        shared_path = "docs/specs/agent-tooling-spec.md"
        standard_path = "docs/standards/template-update.md"
        source_spec = (ROOT / shared_path).read_bytes()
        source_standard = (ROOT / standard_path).read_bytes()
        (source / ".agent").mkdir(parents=True, exist_ok=True)
        write_doc(source, shared_path, source_spec.decode("utf-8"))
        write_doc(source, standard_path, source_standard.decode("utf-8"))
        manifest = {
            "schema_version": 1,
            "template_id": "ai-agent-project-template",
            "template_version": "0.4.0",
            "documentation_schema_version": 2,
            "files": [shared_path, standard_path],
        }
        (source / ".agent/template-files.json").write_text(json.dumps(manifest), encoding="utf-8")
        project_spec = document("specification", 2, extra="Project-owned content.\n")
        project_design = document("design", 2, extra="Project-owned content.\n")
        project_spec_path = write_doc(destination, "docs/specs/product-feature-spec.md", project_spec)
        project_design_path = write_doc(destination, "docs/design/product-feature-design.md", project_design)
        if local_shared is not None:
            write_doc(destination, shared_path, local_shared.decode("utf-8"))
        state_path = destination / ".agent/template-state.json"
        state_files = {}
        if previous_shared is not None:
            state_files[shared_path] = {
                "source_sha256": hashlib.sha256(previous_shared).hexdigest(),
            }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"files": state_files}), encoding="utf-8")
        return {
            "source": source,
            "destination": destination,
            "state": state_path,
            "shared_path": shared_path,
            "standard_path": standard_path,
            "source_spec": source_spec,
            "source_standard": source_standard,
            "project_spec_path": project_spec_path,
            "project_spec": project_spec.encode("utf-8"),
            "project_design_path": project_design_path,
            "project_design": project_design.encode("utf-8"),
        }

    def test_update_check_preserves_project_specific_documents_and_writes_nothing(self):
        fixture = self.shared_spec_update_fixture()
        state_before = fixture["state"].read_bytes()
        project_spec_before = fixture["project_spec_path"].read_bytes()
        project_design_before = fixture["project_design_path"].read_bytes()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.run_update(fixture["source"], fixture["destination"], fixture["state"], check=True)
        self.assertFalse((fixture["destination"] / fixture["shared_path"]).exists())
        self.assertFalse((fixture["destination"] / fixture["standard_path"]).exists())
        self.assertEqual(fixture["state"].read_bytes(), state_before)
        self.assertEqual(fixture["project_spec_path"].read_bytes(), project_spec_before)
        self.assertEqual(fixture["project_design_path"].read_bytes(), project_design_before)

    def test_update_copies_shared_spec_and_preserves_project_specific_documents(self):
        fixture = self.shared_spec_update_fixture()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.run_update(fixture["source"], fixture["destination"], fixture["state"], check=False)
        shared = fixture["destination"] / fixture["shared_path"]
        standard = fixture["destination"] / fixture["standard_path"]
        self.assertEqual(shared.read_bytes(), fixture["source_spec"])
        self.assertEqual(standard.read_bytes(), fixture["source_standard"])
        self.assertEqual(fixture["project_spec_path"].read_bytes(), fixture["project_spec"])
        self.assertEqual(fixture["project_design_path"].read_bytes(), fixture["project_design"])
        target = module.local_markdown_target(standard, "../specs/agent-tooling-spec.md")
        self.assertEqual(target, shared.resolve())
        self.assertTrue(target.is_file())
        self.assertIn("applied=2", stdout.getvalue().splitlines())
        state_files = json.loads(fixture["state"].read_text(encoding="utf-8"))["files"]
        self.assertEqual(set(state_files), {fixture["shared_path"], fixture["standard_path"]})
        unchanged_stdout = io.StringIO()
        with contextlib.redirect_stdout(unchanged_stdout):
            self.run_update(fixture["source"], fixture["destination"], fixture["state"], check=False)
        self.assertIn("unchanged=2", unchanged_stdout.getvalue().splitlines())
        self.assertIn("applied=0", unchanged_stdout.getvalue().splitlines())

    def test_downstream_update_copies_profile_spec_without_unmanaged_design_and_validates(self):
        destination = self.root / "downstream"
        state_path = destination / ".agent/template-state.json"
        manifest_path = destination / ".agent/template-files.json"
        args = Namespace(source=str(ROOT), check=False, adopt=False)
        stdout = io.StringIO()
        with patch.object(module, "ROOT", destination), patch.object(module, "TEMPLATE_STATE", state_path), patch.object(module, "TEMPLATE_FILES", manifest_path), contextlib.redirect_stdout(stdout):
            module.cmd_update_template(args)
            shared_spec = destination / "docs/specs/project-profile-spec.md"
            design = destination / "docs/design/project-profile-context-design.md"
            assurance_spec = destination / "docs/specs/agent-workflow-assurance-spec.md"
            assurance_design = destination / "docs/design/agent-workflow-assurance-design.md"
            status = destination / "docs/status/agent-workflow-assurance-status.md"
            workflow = destination / ".github/workflows/template-ci.yml"
            contract_wrapper = destination / "scripts/agent/publish-implementation-contract.sh"
            pr_template = destination / ".github/pull_request_template.md"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(shared_spec.is_file())
            self.assertTrue(assurance_spec.is_file())
            self.assertTrue(assurance_design.is_file())
            self.assertTrue(workflow.is_file())
            self.assertTrue(contract_wrapper.is_file())
            self.assertTrue(pr_template.is_file())
            self.assertNotIn("docs/status/agent-workflow-assurance-status.md", manifest["files"])
            self.assertFalse(status.exists())
            self.assertNotIn("docs/design/project-profile-context-design.md", manifest["files"])
            self.assertFalse(design.exists())
            module.cmd_validate_docs(Namespace())
        self.assertIn("docs_validation=pass", stdout.getvalue())

    def test_update_conflicts_on_modified_shared_spec_and_preserves_project_documents(self):
        previous_shared = (ROOT / "docs/specs/agent-tooling-spec.md").read_bytes()
        previous_shared += b"\nPrevious template wording.\n"
        local_shared = previous_shared + b"\nLocal clarification.\n"
        fixture = self.shared_spec_update_fixture(
            previous_shared=previous_shared,
            local_shared=local_shared,
        )
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as exc, contextlib.redirect_stdout(stdout):
            self.run_update(fixture["source"], fixture["destination"], fixture["state"], check=False)
        self.assertEqual(exc.exception.code, 2)
        lines = stdout.getvalue().splitlines()
        self.assertIn(f"CONFLICT {fixture['shared_path']}", lines)
        shared = fixture["destination"] / fixture["shared_path"]
        incoming = shared.with_name(shared.name + ".incoming-template")
        standard = fixture["destination"] / fixture["standard_path"]
        self.assertEqual(shared.read_bytes(), local_shared)
        self.assertEqual(incoming.read_bytes(), fixture["source_spec"])
        self.assertEqual(standard.read_bytes(), fixture["source_standard"])
        self.assertEqual(fixture["project_spec_path"].read_bytes(), fixture["project_spec"])
        self.assertEqual(fixture["project_design_path"].read_bytes(), fixture["project_design"])
        self.assertTrue(module.local_markdown_target(standard, "../specs/agent-tooling-spec.md").is_file())

    def test_update_check_reports_migration_without_writes(self):
        source, destination, state = self.updater_fixture()
        before_state = state.read_bytes()
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as exc, contextlib.redirect_stdout(stdout):
            self.run_update(source, destination, state)
        self.assertEqual(exc.exception.code, 3)
        self.assert_migration_report(stdout.getvalue(), ["docs/specs/item.md"])
        self.assertEqual((destination / "managed.md").read_text(encoding="utf-8"), "old template content\n")
        self.assertEqual(state.read_bytes(), before_state)

    def test_update_apply_reports_migration_without_rewriting_project_docs(self):
        source, destination, state = self.updater_fixture()
        before_doc = (destination / "docs/specs/item.md").read_bytes()
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as exc, contextlib.redirect_stdout(stdout):
            self.run_update(source, destination, state, check=False)
        self.assertEqual(exc.exception.code, 3)
        self.assert_migration_report(stdout.getvalue(), ["docs/specs/item.md"])
        self.assertEqual((destination / "managed.md").read_text(encoding="utf-8"), "new template content\n")
        self.assertEqual((destination / "docs/specs/item.md").read_bytes(), before_doc)
        self.assertTrue(state.exists())

    def test_schema2_content_defects_do_not_exit_as_migration(self):
        for defect in ("missing-heading", "broken-link"):
            with self.subTest(defect=defect):
                source, destination, state = self.updater_fixture(doc_schema=2)
                document_path = destination / "docs/specs/item.md"
                text = document_path.read_text(encoding="utf-8")
                if defect == "missing-heading":
                    text = text.replace("## Purpose\n\nContent.\n\n", "")
                else:
                    text += "\n[Missing](missing.md)\n"
                document_path.write_text(text, encoding="utf-8")
                code, stdout, _ = self.capture_exit(lambda: self.run_update(source, destination, state))
                self.assertEqual(code, 0)
                self.assert_migration_report(stdout, [])

    def assert_migration_report(self, output, paths):
        lines = output.splitlines()
        self.assertIn("documentation_schema_required=2", lines)
        self.assertIn(f"documentation_migration_required={len(paths)}", lines)
        actual_paths = [line for line in lines if line.startswith("MIGRATION_REQUIRED ")]
        self.assertEqual(actual_paths, [f"MIGRATION_REQUIRED {path}" for path in paths])

    def test_update_check_reports_multiple_migrations_in_sorted_order(self):
        source, destination, state = self.updater_fixture(doc_schema=2)
        write_doc(destination, "docs/design/b-design.md", document("design", 1))
        write_doc(destination, "docs/specs/a-spec.md", document("specification", 1))
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as exc, contextlib.redirect_stdout(stdout):
            self.run_update(source, destination, state)
        self.assertEqual(exc.exception.code, 3)
        self.assert_migration_report(stdout.getvalue(), [
            "docs/design/b-design.md", "docs/specs/a-spec.md",
        ])

    def test_update_succeeds_when_migration_is_resolved(self):
        source, destination, state = self.updater_fixture(doc_schema=2)
        write_doc(destination, "docs/specs/README.md", "[Item](item.md)\n")
        self.run_update(source, destination, state)

    def test_conflict_exit_code_precedes_migration_exit_code(self):
        source, destination, state = self.updater_fixture(state=False)
        write_doc(destination, "managed.md", "local content\n")
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as exc, contextlib.redirect_stdout(stdout):
            self.run_update(source, destination, state)
        self.assertEqual(exc.exception.code, 2)
        self.assert_migration_report(stdout.getvalue(), ["docs/specs/item.md"])
        self.assertIn("CONFLICT managed.md", stdout.getvalue().splitlines())

    def test_old_source_manifest_defaults_to_schema1(self):
        source, destination, state = self.updater_fixture(required_schema=..., doc_schema=1)
        self.run_update(source, destination, state)


if __name__ == "__main__":
    unittest.main()
