#!/usr/bin/env python3
"""Read-only PR metadata and public Self-review check for pull_request CI."""

import argparse
import json
import re

import agent_tool as agent


def validate_body_fields(body: str) -> None:
    verification = agent.parse_body_metadata(body, "Verification", {"Results"})
    untested = agent.parse_body_metadata(body, "Untested", {"Platforms/targets"})
    if not verification or not verification["Results"].strip() or verification["Results"].strip().lower() in {"todo", "tbd", "..."}:
        agent.fail("PR Verification Results must be completed")
    if not untested or not untested["Platforms/targets"].strip() or untested["Platforms/targets"].strip().lower() in {"todo", "tbd", "..."}:
        agent.fail("PR Untested Platforms/targets must be completed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr", type=int)
    args = parser.parse_args()

    agent.require("gh")
    repository, _host = agent.current_repository()
    pr = agent.gh_api(agent.pull_endpoint(repository, args.pr))
    if pr.get("state") != "open" or pr.get("draft"):
        agent.fail("PR metadata checks run only for an open, ready PR")
    body = str(pr.get("body", ""))
    issue_match = re.search(r"(?im)^\s*Closes\s+#([1-9][0-9]*)\b", body)
    if not issue_match:
        agent.fail("PR body must contain Closes #<issue>")
    issue_number = int(issue_match.group(1))
    agent.verify_pr_identity(repository, issue_number, args.pr, pr)
    issue = agent.gh_api(f"repos/{repository}/issues/{issue_number}")
    if agent.extract_phase(issue) != "phase:review":
        agent.fail("Issue must be in phase:review before PR metadata validation")
    validate_body_fields(body)
    config_path = agent.ROOT / ".agent" / "project.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    agent.validate_generic_rationale(str(issue.get("body", "")), body, config)

    pointer = agent.contract_pointer(str(issue.get("body", "")))
    if pointer is None:
        agent.fail("Issue has no approved Implementation Contract pointer for public review validation")
    agent.cmd_restore_contract(argparse.Namespace(issue=issue_number, replace_stale=False))
    agent.cmd_validate_public_review(argparse.Namespace(issue=issue_number, pr=args.pr, head=str(pr.get("head", {}).get("sha", ""))))
    print(f"pr_metadata=pass issue={issue_number} pr={args.pr}")


if __name__ == "__main__":
    main()
