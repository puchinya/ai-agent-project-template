import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import test_doc_validation as support

module = support.module


class ContractDistributionTests(unittest.TestCase):
    def test_contract_comment_roundtrip_preserves_utf8_crlf_and_final_newline(self):
        data = "# Contract\r\n\r\nCrème brûlée\r\n".encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()
        body = module.contract_comment_body(5, data, sha)
        decoded, actual_sha = module.parse_contract_comment({
            "issue_url": "https://api.github.com/repos/example/template/issues/5",
            "body": body,
        }, "example/template", 5)
        self.assertEqual(decoded, data)
        self.assertEqual(actual_sha, sha)
        self.assertTrue(decoded.endswith(b"\r\n"))
        self.assertLessEqual(len(body), module.CONTRACT_COMMENT_MAX_CHARS)

    def test_contract_comment_rejects_tampering_and_wrong_issue(self):
        data = b"# approved contract\n"
        sha = hashlib.sha256(data).hexdigest()
        body = module.contract_comment_body(5, data, sha)
        cases = [
            {"issue_url": "https://api.github.com/repos/example/template/issues/6", "body": body},
            {"issue_url": "https://api.github.com/repos/other/template/issues/5", "body": body},
            {"issue_url": "https://api.github.com/repos/example/template/issues/5", "body": body + "changed"},
        ]
        for comment in cases:
            with self.subTest(comment=comment["issue_url"]), self.assertRaises(SystemExit):
                module.parse_contract_comment(comment, "example/template", 5)

    def test_payload_limits_and_credential_rejection(self):
        self.assertEqual(module.validate_contract_payload(b"line\r\n", 1), hashlib.sha256(b"line\r\n").hexdigest())
        for payload in [b"", b"\xff", b"a\x00b", b"token=ghp_" + b"A" * 24, b"x" * (module.CONTRACT_MAX_BYTES + 1)]:
            with self.subTest(payload_len=len(payload)), self.assertRaises(SystemExit):
                module.validate_contract_payload(payload, 1)

    def test_oversized_rendered_comment_is_rejected_before_remote_or_mirror_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "oversized.md"
            source.write_bytes(b"x" * module.CONTRACT_MAX_BYTES)
            state = root / "issues"
            issue_dir = state / "5"
            original = b"# existing exact mirror\r\n"
            module.write_contract_mirror(issue_dir, original)
            calls = []
            with patch.object(module, "require"), \
                 patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=lambda *args, **kwargs: calls.append((args, kwargs))), \
                 patch.object(module, "STATE", state), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                module.cmd_publish_contract(Namespace(issue=5, source=source, supersede=False))
            self.assertEqual(calls, [])
            self.assertEqual((issue_dir / "implementation-contract.md").read_bytes(), original)
            self.assertEqual(
                (issue_dir / "implementation-contract.sha256").read_text(encoding="utf-8").strip().split()[0],
                hashlib.sha256(original).hexdigest(),
            )

    def test_local_mirror_collision_is_non_mutating_and_replace_keeps_sha_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            previous = b"# old\r\n"
            current = b"# new\n"
            module.write_contract_mirror(base, previous)
            old_sha_file = (base / "implementation-contract.sha256").read_bytes()
            with self.assertRaises(SystemExit):
                module.write_contract_mirror(base, current)
            self.assertEqual((base / "implementation-contract.md").read_bytes(), previous)
            self.assertEqual((base / "implementation-contract.sha256").read_bytes(), old_sha_file)
            previous_sha = hashlib.sha256(previous).hexdigest()
            module.write_contract_mirror(base, current, replace_stale=True)
            self.assertEqual((base / "implementation-contract.md").read_bytes(), current)
            self.assertEqual((base / f"implementation-contract.{previous_sha}.bak").read_bytes(), previous)

    def test_legacy_save_contract_keeps_exact_source_bytes(self):
        data = "# Legacy mirror\r\n\r\nbyte exact\r\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "contract.txt"
            source.write_bytes(data)
            state = root / "issues"
            with patch.object(module, "require"), patch.object(module, "issue_exists"), patch.object(module, "ROOT", root), patch.object(module, "STATE", state), contextlib.redirect_stdout(io.StringIO()):
                module.cmd_save_contract(Namespace(issue=5, path=source))
            self.assertEqual((state / "5" / "implementation-contract.md").read_bytes(), data)
            self.assertEqual((state / "5" / "implementation-contract.sha256").read_text().split()[0], hashlib.sha256(data).hexdigest())

    def test_github_mutations_use_json_temp_files_and_remove_them(self):
        seen = {}
        def fake_run(command, **_kwargs):
            seen["command"] = command
            seen["json"] = json.loads(Path(command[command.index("--input") + 1]).read_text(encoding="utf-8"))
            seen["temp"] = Path(command[command.index("--input") + 1])
            return '{"id":1}'
        with patch.object(module, "require"), patch.object(module, "run", side_effect=fake_run):
            response = module.gh_api("repos/example/template/issues/5/comments", method="POST", payload={"body": "private body"})
        self.assertEqual(response, {"id": 1})
        self.assertEqual(seen["json"], {"body": "private body"})
        self.assertNotIn("private body", seen["command"])
        self.assertFalse(seen["temp"].exists())

    def test_publish_reuses_verified_pending_comment_after_pointer_failure(self):
        data = b"# Workflow contract\r\n\r\nExact bytes.\r\n"
        comment_id = 42
        calls = []
        issue = {"number": 5, "body": ""}
        comment = {
            "issue_url": "https://api.github.com/repos/example/template/issues/5",
            "body": module.contract_comment_body(5, data, hashlib.sha256(data).hexdigest()),
        }
        def fake_api(endpoint, *, method="GET", payload=None):
            calls.append((endpoint, method))
            if endpoint == "repos/example/template/issues/5" and method == "GET":
                return dict(issue)
            if endpoint == "repos/example/template/issues/5/comments" and method == "POST":
                return {"id": comment_id}
            if endpoint == f"repos/example/template/issues/comments/{comment_id}":
                return comment
            raise AssertionError(f"unexpected API call: {endpoint} {method}")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_bytes(data)
            state = root / "issues"
            args = Namespace(issue=5, source=source, supersede=False)
            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=fake_api), patch.object(module, "STATE", state), \
                 patch.object(module, "update_issue_contract_pointer", side_effect=SystemExit(1)), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    module.cmd_publish_contract(args)
            pending = state / "5" / "implementation-contract-pending.json"
            self.assertTrue(pending.is_file())

            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=fake_api), patch.object(module, "STATE", state), \
                 patch.object(module, "update_issue_contract_pointer") as update, contextlib.redirect_stdout(io.StringIO()):
                module.cmd_publish_contract(args)
            update.assert_called_once_with("example/template", 5, None, (comment_id, hashlib.sha256(data).hexdigest(), "approved"))
            self.assertFalse(pending.exists())
            self.assertEqual(calls.count(("repos/example/template/issues/5/comments", "POST")), 1)

    def test_publish_same_sha_is_idempotent_and_fetches_only_pointed_comment(self):
        data = b"# contract\r\n"
        sha = hashlib.sha256(data).hexdigest()
        pointer_body = f"## Implementation Contract\n\nComment ID: 55\nSHA-256: {sha}\nState: approved\n"
        comment = {
            "issue_url": "https://api.github.com/repos/example/template/issues/5",
            "body": module.contract_comment_body(5, data, sha),
        }
        calls = []
        def api(endpoint, **_kwargs):
            calls.append(endpoint)
            if endpoint == "repos/example/template/issues/5":
                return {"number": 5, "body": pointer_body}
            if endpoint == "repos/example/template/issues/comments/55":
                return comment
            raise AssertionError(f"same-SHA publish fetched unexpected endpoint: {endpoint}")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "contract.md"
            source.write_bytes(data)
            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=api), patch.object(module, "STATE", root / "issues"), contextlib.redirect_stdout(io.StringIO()):
                module.cmd_publish_contract(Namespace(issue=5, source=source, supersede=False))
        self.assertEqual(calls, ["repos/example/template/issues/5", "repos/example/template/issues/comments/55"])

    def test_verify_contract_compares_remote_bytes_with_local_hash_mirror(self):
        data = b"# verified\r\n"
        sha = hashlib.sha256(data).hexdigest()
        pointer_body = f"## Implementation Contract\n\nComment ID: 55\nSHA-256: {sha}\nState: approved\n"
        comment = {"issue_url": "https://api.github.com/repos/example/template/issues/5", "body": module.contract_comment_body(5, data, sha)}
        calls = []
        def api(endpoint, **_kwargs):
            calls.append(endpoint)
            if endpoint == "repos/example/template/issues/5":
                return {"number": 5, "body": pointer_body}
            if endpoint == "repos/example/template/issues/comments/55":
                return comment
            raise AssertionError(f"verify fetched unexpected endpoint: {endpoint}")
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "issues"
            module.write_contract_mirror(state / "5", data)
            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=api), patch.object(module, "STATE", state), contextlib.redirect_stdout(io.StringIO()):
                module.cmd_verify_contract(Namespace(issue=5))
        self.assertEqual(calls, ["repos/example/template/issues/5", "repos/example/template/issues/comments/55"])

    def test_restore_fetches_only_pointer_comment_and_preserves_old_version_backup(self):
        old = b"# prior approved contract\r\n"
        data = b"# current approved contract\r\n\r\nKeep CRLF.\r\n"
        sha = hashlib.sha256(data).hexdigest()
        pointer_body = f"## Implementation Contract\n\nComment ID: 55\nSHA-256: {sha}\nState: approved\n"
        comment = {
            "issue_url": "https://api.github.com/repos/example/template/issues/5",
            "body": module.contract_comment_body(5, data, sha),
        }
        calls = []
        def api(endpoint, **_kwargs):
            calls.append(endpoint)
            if endpoint == "repos/example/template/issues/5":
                return {"number": 5, "body": pointer_body}
            if endpoint == "repos/example/template/issues/comments/55":
                return comment
            raise AssertionError(f"restore requested a non-pointer endpoint: {endpoint}")
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "issues"
            issue_dir = state / "5"
            module.write_contract_mirror(issue_dir, old)
            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=api), patch.object(module, "STATE", state), contextlib.redirect_stdout(io.StringIO()):
                module.cmd_restore_contract(Namespace(issue=5, replace_stale=True))
            old_sha = hashlib.sha256(old).hexdigest()
            self.assertEqual((issue_dir / "implementation-contract.md").read_bytes(), data)
            self.assertEqual((issue_dir / f"implementation-contract.{old_sha}.bak").read_bytes(), old)
            self.assertEqual(calls, ["repos/example/template/issues/5", "repos/example/template/issues/comments/55"])

    def test_restore_sha_mismatch_leaves_existing_mirror_unchanged(self):
        old = b"# local version stays\n"
        remote = b"# remote altered after approval\n"
        expected_sha = hashlib.sha256(b"# approved version\n").hexdigest()
        remote_sha = hashlib.sha256(remote).hexdigest()
        pointer_body = f"## Implementation Contract\n\nComment ID: 55\nSHA-256: {expected_sha}\nState: approved\n"
        comment = {
            "issue_url": "https://api.github.com/repos/example/template/issues/5",
            "body": module.contract_comment_body(5, remote, remote_sha),
        }
        def api(endpoint, **_kwargs):
            if endpoint.endswith("/issues/5"):
                return {"number": 5, "body": pointer_body}
            return comment
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "issues"
            issue_dir = state / "5"
            module.write_contract_mirror(issue_dir, old)
            before_contract = (issue_dir / "implementation-contract.md").read_bytes()
            before_sha = (issue_dir / "implementation-contract.sha256").read_bytes()
            with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=api), patch.object(module, "STATE", state), self.assertRaises(SystemExit):
                module.cmd_restore_contract(Namespace(issue=5, replace_stale=True))
            self.assertEqual((issue_dir / "implementation-contract.md").read_bytes(), before_contract)
            self.assertEqual((issue_dir / "implementation-contract.sha256").read_bytes(), before_sha)


if __name__ == "__main__":
    unittest.main()
