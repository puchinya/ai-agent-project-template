import contextlib
import hashlib
import io
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import test_doc_validation as support

module = support.module
ISSUE = 5
PR = 7
HEAD = "a" * 40
CHECKLIST = "b" * 64
ENTRIES = [("C01", "contract", "Preserve the approved workflow invariants")]


def review_text(*, checklist=CHECKLIST, head=HEAD, status="PASS", detail="Evidence: unit test output and committed diff"):
    return (
        "# Self-review\n\n"
        f"Issue: #{ISSUE}\n"
        f"Checklist-SHA256: {checklist}\n"
        f"Reviewed-HEAD: {head}\n\n"
        f"- C01 | {status} | {detail}\n"
    )


def pr_body(*, closes=True, review_pointer=True, verification="all required tests passed", untested="Windows PowerShell wrapper"):
    body = ("Closes #5\n" if closes else "Fixes nothing\n")
    body += f"\n## Verification\n\nResults: {verification}\n"
    body += f"\n## Untested\n\nPlatforms/targets: {untested}\n"
    body += "\n## Generic profile rationale\n\nGeneric profile rationale: N/A\n"
    if review_pointer:
        body += f"\n## Self-review\n\nComment ID: 22\nSHA-256: {'c' * 64}\nReviewed-HEAD: {HEAD}\n"
    return body


def pull_request(*, state="open", draft=False, body=None, head=HEAD, merged_at=None):
    return {
        "number": PR,
        "state": state,
        "draft": draft,
        "merged_at": merged_at,
        "body": body if body is not None else pr_body(),
        "head": {"sha": head},
        "base": {"ref": "main", "repo": {"full_name": "example/template"}},
    }


def issue(*, phase="phase:review", state="open", body="## Affected components\n\n- `root`\n"):
    return {"number": ISSUE, "state": state, "body": body, "labels": [{"name": phase}, {"name": "triage"}] if phase else [{"name": "triage"}]}


class PublicReviewTests(unittest.TestCase):
    def test_pr_template_placeholder_is_an_unpublished_review_pointer(self):
        body = (
            "## Self-review\n\n"
            "Comment ID: <public comment ID>\n"
            "SHA-256: <64 hex characters>\n"
            "Reviewed-HEAD: <40 hex characters>\n"
        )
        self.assertIsNone(module.pull_review_pointer(body))

    def test_publish_self_review_replaces_template_pointer_and_is_idempotent(self):
        text = review_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        body = (
            "## Verification\n\nResults: all required tests passed\n\n"
            "## Untested\n\nPlatforms/targets: Windows wrapper runtime\n\n"
            "## Generic profile rationale\n\nGeneric profile rationale: N/A\n\n"
            "## Self-review\n\nComment ID: <public comment ID>\n"
            "SHA-256: <64 hex characters>\nReviewed-HEAD: <40 hex characters>\n"
        )
        pr = pull_request(body=body)
        state = {"pr": pr}
        created_comment = {}
        posts = []
        def api(endpoint, *, method="GET", payload=None):
            if endpoint == "repos/example/template/pulls/7" and method == "GET":
                return dict(state["pr"])
            if endpoint == "repos/example/template/pulls/7" and method == "PATCH":
                state["pr"]["body"] = payload["body"]
                return dict(state["pr"])
            if endpoint == "repos/example/template/issues/7/comments" and method == "POST":
                posts.append(payload["body"])
                created_comment.update({"id": 22, "issue_url": "https://api.github.com/repos/example/template/issues/7", "body": payload["body"]})
                return {"id": 22}
            if endpoint == "repos/example/template/issues/comments/22" and method == "GET":
                return dict(created_comment)
            raise AssertionError(f"unexpected API call: {method} {endpoint}")

        with tempfile.TemporaryDirectory() as temp:
            state_root = Path(temp) / "issues"
            issue_dir = state_root / str(ISSUE)
            issue_dir.mkdir(parents=True)
            (issue_dir / "self-review.md").write_text(text, encoding="utf-8")
            (issue_dir / "reviewer-checklist.sha256").write_text(CHECKLIST + "\n", encoding="utf-8")
            args = Namespace(issue=ISSUE, pr=PR)
            output = io.StringIO()
            with patch.object(module, "require"), patch.object(module, "effective_checklist", return_value=(ENTRIES, CHECKLIST)), \
                 patch.object(module, "run", side_effect=lambda command, **_kwargs: HEAD if command[:3] == ["git", "rev-parse", "HEAD"] else ""), \
                 patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
                 patch.object(module, "gh_api", side_effect=api), patch.object(module, "STATE", state_root), contextlib.redirect_stdout(output):
                module.cmd_publish_self_review(args)
                module.cmd_publish_self_review(args)
        pointer = module.pull_review_pointer(state["pr"]["body"])
        self.assertEqual(pointer, (22, sha, HEAD))
        self.assertEqual(len(posts), 1)
        self.assertIn("self_review_publish=already_current", output.getvalue())

    def test_public_review_comment_is_independently_bound_to_pr_issue_head_and_checklist(self):
        text = review_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        body = module.self_review_comment_body(ISSUE, PR, text, sha, HEAD, CHECKLIST)
        parsed, actual_sha, head, checklist = module.parse_self_review_comment({
            "issue_url": f"https://api.github.com/repos/example/template/issues/{PR}",
            "body": body,
        }, "example/template", ISSUE, PR)
        self.assertEqual((parsed, actual_sha, head, checklist), (text, sha, HEAD, CHECKLIST))
        module.validate_review_text(parsed, ISSUE, ENTRIES, CHECKLIST, HEAD)

    def test_public_review_rejects_tampered_hash_wrong_pr_and_changed_checklist(self):
        text = review_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        valid = {
            "issue_url": f"https://api.github.com/repos/example/template/issues/{PR}",
            "body": module.self_review_comment_body(ISSUE, PR, text, sha, HEAD, CHECKLIST),
        }
        tampered = dict(valid, body=valid["body"] + "tampered")
        foreign = dict(valid, issue_url="https://api.github.com/repos/example/template/issues/8")
        stale = module.self_review_comment_body(ISSUE, PR, review_text(checklist="d" * 64), sha, HEAD, "d" * 64)
        cases = [tampered, foreign, dict(valid, body=stale)]
        for comment in cases:
            with self.subTest(body=comment["body"][-12:]), self.assertRaises(SystemExit):
                module.parse_self_review_comment(comment, "example/template", ISSUE, PR)

    def test_validate_public_review_rejects_stale_head_and_checklist(self):
        old_checklist = "d" * 64
        text = review_text(checklist=old_checklist)
        sha = hashlib.sha256(text.encode()).hexdigest()
        pointer = (22, sha, HEAD)
        pr = pull_request(body=pr_body())
        comment = {
            "issue_url": f"https://api.github.com/repos/example/template/issues/{PR}",
            "body": module.self_review_comment_body(ISSUE, PR, text, sha, HEAD, old_checklist),
        }
        with patch.object(module, "effective_checklist", return_value=(ENTRIES, CHECKLIST)), \
             patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
             patch.object(module, "gh_api", side_effect=[pr, comment]), self.assertRaises(SystemExit):
            module.cmd_validate_public_review(Namespace(issue=ISSUE, pr=PR, head=None))

        text = review_text()
        sha = hashlib.sha256(text.encode()).hexdigest()
        pr = pull_request(body=pr_body(), head="e" * 40)
        comment = {
            "issue_url": f"https://api.github.com/repos/example/template/issues/{PR}",
            "body": module.self_review_comment_body(ISSUE, PR, text, sha, HEAD, CHECKLIST),
        }
        with patch.object(module, "effective_checklist", return_value=(ENTRIES, CHECKLIST)), \
             patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
             patch.object(module, "gh_api", side_effect=[pr, comment]), self.assertRaises(SystemExit):
            module.cmd_validate_public_review(Namespace(issue=ISSUE, pr=PR, head=None))

    def test_review_result_requires_evidence_and_complete_checklist(self):
        with self.assertRaises(SystemExit):
            module.validate_review_text(review_text(detail="Evidence:"), ISSUE, ENTRIES, CHECKLIST, HEAD)
        with self.assertRaises(SystemExit):
            module.validate_review_text(review_text(status="PENDING", detail=""), ISSUE, ENTRIES, CHECKLIST, HEAD)
        with self.assertRaises(SystemExit):
            module.validate_review_text(review_text().replace("- C01", "- OTHER"), ISSUE, ENTRIES, CHECKLIST, HEAD)


class DeliveryGateTests(unittest.TestCase):
    def _run_handoff(self, pr, issue_data, affected=None):
        responses = {
            "repos/example/template/pulls/7": pr,
            "repos/example/template/issues/5": issue_data,
        }
        def api(endpoint, **_kwargs):
            return responses[endpoint]
        with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), \
             patch.object(module, "gh_api", side_effect=api), \
             patch.object(module, "cmd_validate_public_review"), \
             patch.object(module, "required_checks_green") as checks, \
             patch.object(module, "load_config", return_value={}), \
             patch.object(module, "context_profile_components", return_value=(2, affected or [{"application_types": ["cli"]}], ["root"])):
            module.cmd_delivery_check(Namespace(issue=ISSUE, pr=PR, stage="handoff"))
        return checks

    def test_valid_handoff_requires_phase_review_and_required_checks(self):
        checks = self._run_handoff(pull_request(), issue(), affected=[{"application_types": ["cli"]}])
        checks.assert_called_once_with("example/template", "main", HEAD)

    def test_handoff_rejects_draft_closes_missing_and_wrong_phase(self):
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(draft=True), issue())
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(body=pr_body(closes=False)), issue())
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(), issue(phase="phase:implementation"))

    def test_generic_affected_component_requires_specific_pr_rationale(self):
        generic = [{"application_types": ["generic"]}]
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(), issue(), affected=generic)
        body = pr_body().replace("Generic profile rationale: N/A", "Generic profile rationale: this is a language-neutral starter with no product-specific runtime.")
        checks = self._run_handoff(pull_request(body=body), issue(), affected=generic)
        checks.assert_called_once()

    def test_verification_and_untested_fields_must_be_filled(self):
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(body=pr_body(verification="TODO")), issue())
        with self.assertRaises(SystemExit):
            self._run_handoff(pull_request(body=pr_body(untested="...")), issue())

    def test_required_checks_must_be_configured_and_green(self):
        def run_gate(check_runs, required):
            def api(endpoint, **_kwargs):
                if "required_status_checks" in endpoint:
                    return required
                if endpoint.endswith("check-runs?per_page=100"):
                    return {"check_runs": check_runs}
                return {"statuses": []}
            with patch.object(module, "gh_api", side_effect=api):
                module.required_checks_green("example/template", "main", HEAD)
        with self.assertRaises(SystemExit):
            run_gate([], {"checks": [], "contexts": []})
        for status, conclusion in [("queued", None), ("completed", "failure")]:
            with self.subTest(status=status, conclusion=conclusion), self.assertRaises(SystemExit):
                run_gate([{"name": "Template CI", "status": status, "conclusion": conclusion, "app": {"id": 5}}], {"checks": [{"context": "Template CI", "app_id": 5}]})
        run_gate([{"name": "Template CI", "status": "completed", "conclusion": "success", "app": {"id": 5}}], {"checks": [{"context": "Template CI", "app_id": 5}]})

    def test_merged_issue_phase_label_cleanup_is_idempotent(self):
        state = {"labels": [{"name": "phase:review"}, {"name": "triage"}]}
        merged_pr = pull_request(state="closed", merged_at="2026-10-01T00:00:00Z")
        def api(endpoint, *, method="GET", **_kwargs):
            if endpoint == "repos/example/template/pulls/7":
                return merged_pr
            if endpoint == "repos/example/template/issues/5":
                return {"state": "closed", "labels": list(state["labels"])}
            if endpoint.endswith("/labels/phase%3Areview") and method == "DELETE":
                state["labels"] = [label for label in state["labels"] if label["name"] != "phase:review"]
                return None
            raise AssertionError(f"unexpected API call {method} {endpoint}")
        with patch.object(module, "require"), patch.object(module, "current_repository", return_value=("example/template", "github.com")), patch.object(module, "gh_api", side_effect=api), contextlib.redirect_stdout(io.StringIO()):
            module.cmd_finalize_merged_issue(Namespace(issue=ISSUE, pr=PR))
            module.cmd_finalize_merged_issue(Namespace(issue=ISSUE, pr=PR))
        self.assertEqual(state["labels"], [{"name": "triage"}])


if __name__ == "__main__":
    unittest.main()
