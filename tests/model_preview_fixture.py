"""Synthetic renderer inputs, NOT a substitute for Core contract acceptance."""
import copy
from datetime import datetime, timedelta, timezone

from test_build import offer, TOKEN_WINNER
from tools.model_preview import CORE_COMMIT


def fixture():
    models = []
    for i in range(4):
        models.append({"reference": f"fixture-model-{i}", "name": f"FIXTURE Model {i}",
                       "desired_path": f"/p/fixture-model-{i}/", "permanent_owner": None,
                       "members": [{"product_id": f"fixture-product-{i}-{j}", "selector": c,
                                    "label": c.title()} for j, c in enumerate(("svart", "hvit"))]})
    entries = []
    for i, m in enumerate(models):
        for j, member in enumerate(m["members"]):
            pid = member["product_id"]
            image = {"url": f"https://sjekkpris.no/assets/fixture-{i}-{j}.png", "variants": []}
            first = offer(f"fixture-{i}-{j}-a", f"FIXTURE Shop {i}-{j}", (i+1)*10000+j*1000, token=TOKEN_WINNER)
            second = offer(f"fixture-{i}-{j}-b", "FIXTURE Other", (i+1)*10000+j*1000+500)
            excluded = offer(f"fixture-{i}-{j}-x", "FIXTURE Excluded", 100, stale=True, eligible=False)
            projection = {"image": image, "comparison": {"property_id": "sjekkpris-no", "offers": [first, second],
                          "excluded": [excluded], "lowest_item_price": first["offer_id"], "lowest_known_total_price": None}}
            entries.append({"value": {"contract_version": "chillout.model-presentation.v1",
                "visibility": "private", "reserved": False, "runtime_integrated": False,
                "published": None, "build_ready": False, "models": models, "source": {"revision": 1},
                "specification": {"revision": 1},
                "request": {"property_id": "sjekkpris-no", "environment": "test", "locale": "nb", "pending_product_ids": ["fixture-pending"]},
                "selected": dict(model_reference=m["reference"], **member, projection=projection)},
                "identity": {"local_name": pid, "image": image, "local_brand": "FIXTURE"}})
    now = datetime.now(timezone.utc)
    return {"active": True, "observed_at": now.isoformat(), "expires_at": (now+timedelta(hours=1)).isoformat(),
            "core_commit": CORE_COMMIT, "snapshots": copy.deepcopy(entries), "artifact": {}}


def fixture_verifier(entry, _artifact):
    # Deliberate renderer seam. Real CLI ALWAYS uses pinned Core verify instead.
    return copy.deepcopy(entry["value"]), copy.deepcopy(entry["identity"])
