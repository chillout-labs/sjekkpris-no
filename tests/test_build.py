"""The build against a stub of Chillout's read API.

FIXTURE DATA. Every product, advertiser and price below is invented for these
tests and never reaches the published site; the stub runs on localhost.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import ClassVar
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build
import check_output

KEY = "apk_FIXTURE-synthetic-not-a-real-key"


def offer(offer_id, advertiser, minor, *, availability="in_stock", stale=False,
          shipping_state="not_provided", total=None, status="sorted_last_unknown_total",
          last_confirmed="2026-10-11T04:15:00+00:00"):
    return {
        "offer_id": offer_id,
        "advertiser": advertiser,
        "provider": "Tradedoubler",
        "item_price": None if minor is None else {"minor": minor, "currency": "NOK"},
        "known_total_price": total,
        "comparison_status": status,
        "shipping": {"state": shipping_state, "amount": None, "imported_amount": None,
                     "terms": None},
        "availability": {"status": availability, "raw_value": None},
        "last_confirmed_at": last_confirmed,
        "stale": stale,
        "withdrawn": False,
        "deselected": False,
        # The contract carries a link block; the site must render nothing of it.
        "link": {"clickout_available": True, "clickout_url": "/go/FIXTURE-token"},
    }


INDEX = {
    "property_id": "sjekkpris-no",
    "products": [
        {"namespace": "catalogue", "local_slug": "fixture-lamp",
         "local_name": "FIXTURE Lamp <b>", "lowest_item_price": {"minor": 129900, "currency": "NOK"},
         "offer_count": 3, "lowest_item_price_confirmed_at": "2026-10-11T04:15:00+00:00"},
        {"namespace": "catalogue", "local_slug": "fixture-empty",
         "local_name": "FIXTURE Nothing priced", "lowest_item_price": None,
         "offer_count": 1, "lowest_item_price_confirmed_at": None},
    ],
}

COMPARISONS = {
    "fixture-lamp": {
        "property_id": "sjekkpris-no", "product_id": "prd_FIXTURE",
        "offers": [
            offer("o-cheap-stale", "FIXTURE Stale Shop", 99900, stale=True,
                  last_confirmed="2026-10-01T04:15:00+00:00"),
            offer("o-winner", "FIXTURE Winner Shop", 129900),
            offer("o-oos", "FIXTURE Empty Shelf", 89900, availability="out_of_stock"),
        ],
        "excluded": [],
        "lowest_item_price": "o-winner",
        "lowest_known_total_price": None,
        "identity": {"local_name": "FIXTURE Lamp <b>"},
    },
    "fixture-empty": {
        "property_id": "sjekkpris-no", "product_id": "prd_FIXTURE2",
        "offers": [offer("o-null", "FIXTURE No Price Shop", None, availability="unknown")],
        "excluded": [],
        "lowest_item_price": None,
        "lowest_known_total_price": None,
        "identity": {"local_name": "FIXTURE Nothing priced"},
    },
}


class Stub(BaseHTTPRequestHandler):
    seen_paths: ClassVar[list[str]] = []

    def do_GET(self):
        Stub.seen_paths.append(self.path)
        if self.headers.get("Authorization") != f"Bearer {KEY}":
            return self._send(401, {})
        if self.path == "/api/v1/properties/sjekkpris-no/catalogue":
            return self._send(200, INDEX)
        prefix = "/api/v1/properties/sjekkpris-no/catalogue/catalogue/"
        if self.path.startswith(prefix) and self.path.endswith("/offers"):
            slug = self.path[len(prefix):-len("/offers")]
            if slug in COMPARISONS:
                return self._send(200, COMPARISONS[slug])
        return self._send(404, {})

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Stub)
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "_site"
        client = build.Chillout(self.origin, KEY)
        build.build(client, self.out, base="/sjekkpris-no/", noindex=True)
        self.index = (self.out / "index.html").read_text(encoding="utf-8")
        self.lamp = (self.out / "p/catalogue/fixture-lamp/index.html").read_text(encoding="utf-8")
        self.empty = (self.out / "p/catalogue/fixture-empty/index.html").read_text(
            encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nok_renders_with_comma_dash_and_a_non_breaking_separator(self):
        self.assertIn("NOK 1 299,-", self.index)
        self.assertEqual(build.money({"minor": 31050, "currency": "NOK"}), "NOK 310,50")

    def test_a_null_price_is_no_price_never_zero(self):
        self.assertIn("Ingen pris", self.index)
        self.assertIn("Ingen pris", self.empty)
        self.assertNotIn("NOK 0", self.index + self.empty)

    def test_lowest_price_badge_only_on_the_offer_the_api_names(self):
        winner_row = next(r for r in self.lamp.split("<tr>") if "FIXTURE Winner Shop" in r)
        self.assertIn("Laveste pris", winner_row)
        for other in ("FIXTURE Stale Shop", "FIXTURE Empty Shelf"):
            row = next(r for r in self.lamp.split("<tr>") if other in r)
            self.assertNotIn("Laveste pris", row, other)
        self.assertNotIn("Laveste pris</span>", self.empty)

    def test_stale_and_out_of_stock_are_stated(self):
        stale_row = next(r for r in self.lamp.split("<tr>") if "FIXTURE Stale Shop" in r)
        self.assertIn("Ikke bekreftet nylig (sist 01.10.2026)", stale_row)
        oos_row = next(r for r in self.lamp.split("<tr>") if "FIXTURE Empty Shelf" in r)
        self.assertIn("Ikke på lager", oos_row)
        self.assertNotIn("På lager", oos_row.replace("Ikke på lager", ""))

    def test_unknown_availability_is_never_in_stock(self):
        self.assertIn("Lagerstatus ukjent", self.empty)
        self.assertNotIn("På lager", self.empty.replace("Ikke på lager", ""))

    def test_unknown_shipping_gives_an_unknown_total(self):
        self.assertIn("Frakt ukjent", self.lamp)
        self.assertIn("Totalpris ukjent", self.lamp)

    def test_names_are_escaped(self):
        self.assertIn("FIXTURE Lamp &lt;b&gt;", self.index)
        self.assertNotIn("FIXTURE Lamp <b>", self.index)

    def test_base_path_prefixes_links(self):
        self.assertIn('href="/sjekkpris-no/p/catalogue/fixture-lamp/"', self.index)
        self.assertIn('href="/sjekkpris-no/style.css"', self.lamp)
        self.assertEqual(build.normalise_base("/"), "/")
        self.assertEqual(build.normalise_base("sjekkpris-no"), "/sjekkpris-no/")

    def test_the_key_travels_only_as_a_header(self):
        # The stub answers 401 without the header, so every page rendering at
        # all proves the header; this proves the key never rode in a URL.
        self.assertTrue(Stub.seen_paths)
        self.assertFalse(any("apk_" in path for path in Stub.seen_paths))

    def test_built_output_passes_the_guard(self):
        env = {"CHILLOUT_READ_KEY": KEY, "CHILLOUT_ORIGIN": self.origin}
        with mock.patch.dict(os.environ, env):
            self.assertEqual(check_output.check(self.out), [])

    def test_the_guard_catches_each_forbidden_thing(self):
        env = {"CHILLOUT_READ_KEY": KEY, "CHILLOUT_ORIGIN": "https://chillout.example.test"}
        for leak, rule in [
            ("apk_something", "read key prefix"),
            (KEY, "read key"),
            ("https://chillout.example.test/api", "Chillout origin hostname"),
            ("prd_01ABC", "platform product id"),
            ('<a href="/go/tok">', "clickout path"),
        ]:
            (self.out / "leak.html").write_text(leak, encoding="utf-8")
            with mock.patch.dict(os.environ, env):
                problems = check_output.check(self.out)
            self.assertTrue(any(rule in p for p in problems), (leak, problems))

    def test_a_refused_key_fails_the_build_without_echoing_it(self):
        client = build.Chillout(self.origin, "apk_FIXTURE-wrong")
        with self.assertRaises(build.BuildError) as raised:
            build.build(client, Path(self.tmp.name) / "other", base="/", noindex=True)
        self.assertIn("401", str(raised.exception))
        self.assertNotIn("apk_", str(raised.exception))
        self.assertNotIn("127.0.0.1", str(raised.exception))

    def test_a_missing_key_fails_before_any_request(self):
        with self.assertRaises(build.BuildError):
            build.Chillout(self.origin, "")


if __name__ == "__main__":
    unittest.main()
