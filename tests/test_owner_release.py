import copy
import unittest
from datetime import UTC, datetime, timedelta

from tools.owner_release import assets, validate


class OwnerReleaseTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 31, tzinfo=UTC)
        self.plan = dict(
            release_id=1,
            baseline_deployment_id=2,
            site_sha256="a" * 64,
            site_tree_sha256="b" * 64,
            rollback_sha256="c" * 64,
            rollback_tree_sha256="d" * 64,
            reviewed_at=self.now.isoformat(),
            valid_until=(self.now + timedelta(hours=2)).isoformat(),
        )

    def test_explicit_bounded_review(self):
        self.assertEqual(validate(self.plan, self.now), self.plan)
        for change in [
            dict(valid_until=self.now.isoformat()),
            dict(valid_until=(self.now + timedelta(days=2)).isoformat()),
            dict(reviewed_at=(self.now + timedelta(seconds=1)).isoformat()),
            dict(site_sha256="bad"),
            dict(release_id=True),
            dict(extra="field"),
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(self.plan | change, self.now)

    def test_only_exact_private_assets(self):
        import json

        release = dict(
            id=1,
            draft=True,
            body=json.dumps(self.plan),
            assets=[
                dict(
                    id=3,
                    name="pages-site.tar",
                    digest="sha256:" + "a" * 64,
                    state="uploaded",
                    size=100,
                ),
                dict(
                    id=4,
                    name="pages-rollback.tar",
                    digest="sha256:" + "c" * 64,
                    state="uploaded",
                    size=100,
                ),
            ],
        )
        self.assertEqual(assets(release, self.plan), {"pages-site.tar": 3, "pages-rollback.tar": 4})
        for case in ["public", "wrong-body", "wrong-hash", "missing-rollback", "extra"]:
            changed = copy.deepcopy(release)
            if case == "public":
                changed["draft"] = False
            if case == "wrong-body":
                changed["body"] = json.dumps(self.plan | dict(release_id=99))
            if case == "wrong-hash":
                changed["assets"][0]["digest"] = "sha256:" + "f" * 64
            if case == "missing-rollback":
                changed["assets"].pop()
            if case == "extra":
                changed["assets"].append(dict(name="private-input.json"))
            with self.subTest(case=case), self.assertRaises(ValueError):
                assets(changed, self.plan)


class ReadOnlyPreflight(unittest.TestCase):
    def test_no_draft_access_before_owner_approval(self):
        import json
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from tools import owner_release as release

        plan = {"reviewed": "synthetic"}
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "GITHUB_EVENT_NAME": "workflow_dispatch",
                        "GITHUB_REF": "refs/heads/main",
                        "GITHUB_RUN_ATTEMPT": "1",
                        "GITHUB_REPOSITORY": "example/property",
                        "OWNER_RELEASE_PLAN": json.dumps(plan),
                        "OWNER_RELEASE_STAGE": "preflight",
                        "GITHUB_STEP_SUMMARY": str(Path(tmp) / "summary"),
                    },
                ),
                patch.object(release, "validate", return_value={"baseline_deployment_id": 1}),
                patch.object(release, "baseline") as baseline,
                patch.object(
                    release, "api", side_effect=AssertionError("draft read before approval")
                ),
            ):
                release.main()
                baseline.assert_called_once_with("example/property", 1)
