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
