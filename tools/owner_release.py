"""Explicit owner release of existing bytes. No Core impersonation or renderer."""

import json
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from check_output import check
from tools.pages_release import receive


def validate(plan, now=None):
    if set(plan) != {
        "release_id",
        "baseline_deployment_id",
        "site_sha256",
        "site_tree_sha256",
        "rollback_sha256",
        "rollback_tree_sha256",
        "reviewed_at",
        "valid_until",
    }:
        raise ValueError("owner_release_fields")
    for key in ("release_id", "baseline_deployment_id"):
        if type(plan[key]) is not int or plan[key] <= 0:
            raise ValueError("owner_release_identity")
    for key in ("site_sha256", "site_tree_sha256", "rollback_sha256", "rollback_tree_sha256"):
        if not isinstance(plan[key], str) or not re.fullmatch("[0-9a-f]{64}", plan[key]):
            raise ValueError("owner_release_digest")
    start, end = (datetime.fromisoformat(plan[k]) for k in ("reviewed_at", "valid_until"))
    now = now or datetime.now(UTC)
    if (
        start.utcoffset() is None
        or end.utcoffset() is None
        or not start <= now < end
        or not end <= start + timedelta(hours=24)
    ):
        raise ValueError("owner_release_review_expired")
    return plan


def api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError("github_read_failed")
    return json.loads(r.stdout)


def baseline(repo, expected):
    for dep in api(f"repos/{repo}/deployments?environment=github-pages&per_page=30"):
        status = api(f"repos/{repo}/deployments/{dep['id']}/statuses?per_page=1")
        if status and status[0]["state"] == "success":
            if dep["id"] != expected:
                raise ValueError("public_baseline_changed")
            return
    raise ValueError("public_baseline_unverified")


def assets(release, plan):
    if release.get("id") != plan["release_id"] or release.get("draft") is not True:
        raise ValueError("private_staging_release_required")
    if json.loads(release["body"]) != plan:
        raise ValueError("owner_release_binding_changed")
    rows = release["assets"]
    hashes = {"pages-site.tar": plan["site_sha256"], "pages-rollback.tar": plan["rollback_sha256"]}
    if len(rows) != 2 or {r["name"] for r in rows} != set(hashes):
        raise ValueError("owner_release_assets")
    for row in rows:
        if (
            row.get("state") != "uploaded"
            or type(row.get("id")) is not int
            or not 0 < row.get("size", 0) <= 576 * 1024 * 1024
            or row.get("digest") != "sha256:" + hashes[row["name"]]
        ):
            raise ValueError("owner_release_asset_digest")
    return {r["name"]: r["id"] for r in rows}


def main():
    if (
        os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or os.environ.get("GITHUB_REF") != "refs/heads/main"
        or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"
    ):
        raise ValueError("explicit_main_first_attempt_required")
    repo = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("repository")
    plan = validate(json.loads(os.environ["OWNER_RELEASE_PLAN"]))
    prefix = f"repos/{repo}"
    baseline(repo, plan["baseline_deployment_id"])
    stage = os.environ.get("OWNER_RELEASE_STAGE")
    if stage not in {"preflight", "publish"}:
        raise ValueError("owner_release_stage_required")
    if stage == "preflight":
        # Draft access requires push permission. The ungated job stays read-only.
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write(
                "## Owner review: exact plan and unchanged public baseline\n\n"
                "Archive bytes were verified during preparation; the gated job "
                "must download and verify them again before any Pages upload.\n\n```json\n"
                + json.dumps(plan, indent=2)
                + "\n```\n"
            )
        return
    ids = assets(api(f"{prefix}/releases/{plan['release_id']}"), plan)
    root = Path(os.environ["RUNNER_TEMP"]) / "owner-release"
    root.mkdir(exist_ok=False)
    results = {}
    for name, stem, destination in [
        ("pages-site.tar", "site", Path("_site")),
        ("pages-rollback.tar", "rollback", root / "rollback"),
    ]:
        local = root / name
        with local.open("xb") as out:
            r = subprocess.run(
                [
                    "gh",
                    "api",
                    f"{prefix}/releases/assets/{ids[name]}",
                    "-H",
                    "Accept: application/octet-stream",
                ],
                stdout=out,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        if r.returncode:
            raise RuntimeError("private_asset_read_failed")
        results[stem] = receive(
            local,
            destination,
            archive_sha256=plan[stem + "_sha256"],
            tree_sha256=plan[stem + "_tree_sha256"],
        )
        if check(destination):
            raise ValueError("site_output_check_failed")
    validate(plan)  # Download/verification time consumes the review window.
    baseline(repo, plan["baseline_deployment_id"])
    report = {
        "authority": "explicit-owner-release-not-core-service",
        "workflow_commit": os.environ["GITHUB_SHA"],
        "plan": plan,
        "verified": results,
        "public_release_created": False,
    }
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
        out.write(
            "## Exact owner release — approval required before publication\n\n```json\n"
            + json.dumps(report, indent=2)
            + "\n```\n"
        )
    print("Exact site and rollback verified; no rendering or public release performed.")


if __name__ == "__main__":
    main()
