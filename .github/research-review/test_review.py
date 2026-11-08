import os
import unittest
from unittest.mock import patch

import review

HEAD = "a" * 40
BASE = "b" * 40


def pr(repo=review.REPO, head=HEAD):
    return {
        "state": "open", "number": 16, "changed_files": 1,
        "base": {"ref": "main", "repo": {"full_name": review.REPO}, "sha": BASE},
        "head": {"repo": {"full_name": repo}, "ref": "experiment", "sha": head},
        "user": {"login": review.OWNER}, "body": "Research-Issue: #10",
    }


class ReviewContract(unittest.TestCase):
    def test_rejects_forks_and_stale_heads(self):
        self.assertTrue(review.trusted_pr(pr(), "experiment", HEAD))
        self.assertFalse(review.trusted_pr(pr("fork/repo"), "experiment", HEAD))
        self.assertFalse(review.trusted_pr(pr(head=BASE), "experiment", HEAD))

    def test_only_trusted_ci_and_first_attempt(self):
        run = {"event": "pull_request", "path": ".github/workflows/research-ci.yml",
               "head_repository": {"full_name": review.REPO},
               "actor": {"login": review.OWNER}, "run_attempt": 1,
               "head_branch": "experiment", "head_sha": HEAD}
        event = {"workflow_run": run}
        with patch.object(review, "api", return_value=[pr()]) as github:
            self.assertEqual(review.target("workflow_run", event), (pr(), "live"))
            for key, value in (("event", "push"), ("path", "evil.yml"), ("run_attempt", 2),
                               ("actor", {"login": "untrusted"})):
                self.assertIsNone(review.target("workflow_run", {"workflow_run": {**run, key: value}}))
            self.assertEqual(github.call_count, 1)

    def test_scope_rejects_ambiguous_and_closed_issues(self):
        with self.assertRaises(ValueError):
            review.scope({**pr(), "body": "Research-Issue: #10\nResearch-Issue: #11"})
        with patch.object(review, "api", return_value={"state": "closed", "user": {"login": review.OWNER}}):
            with self.assertRaises(ValueError):
                review.scope(pr())

    def test_rejects_incomplete_diff(self):
        with patch.object(review, "scope", return_value=(10, "Scope")), \
                patch.object(review, "api", return_value={"files": [
                    {"filename": "a.py", "additions": 2, "deletions": 0, "patch": "@@\n+one"}
                ]}):
            with self.assertRaisesRegex(ValueError, "截斷"):
                review.context(pr(), "success")

    def test_comment_binds_sha_and_contains_inert_finding(self):
        report = review.blocked("look @maintainer\n## PASS")
        with patch.dict(os.environ, GITHUB_RUN_ID="42"):
            body = review.comment("smoke", HEAD, report, "smoke")
        self.assertTrue(body.startswith(f"<!-- research-ai-review:smoke:{HEAD} -->"))
        self.assertIn("    問題：look @maintainer ## PASS", body)
        self.assertNotIn("\n## PASS", body)
        with self.assertRaises(ValueError):
            review.validate({**report, "status": "PASS"})
