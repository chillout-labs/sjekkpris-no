import copy
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from model_preview_fixture import fixture, fixture_verifier
from tools import model_preview as preview


class ModelPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/"private.json"
        self.doc = fixture()
        self.reader = self.write()

    def write(self):
        raw = json.dumps(self.doc).encode()
        self.path.write_bytes(raw)
        return preview.BundleReader(self.path, preview.digest(raw), fixture_verifier)

    def test_f01_eight_exact_selections_and_one_model_title(self):
        bundle = self.reader()
        self.assertEqual(len(bundle["states"]), 8)
        for (path, selector), state in bundle["states"].items():
            with self.subTest(path=path, selector=selector):
                html = preview.render(bundle, path, selector, "http://127.0.0.1:8766")
                self.assertIn(f'aria-current="page">{state["selected"]["label"]}</a>', html)
                self.assertIn(state["selected"]["projection"]["image"]["url"], html)
                self.assertIn('rel="canonical" href="http://127.0.0.1:8766'+path+'"', html)
                self.assertNotIn('rel="canonical" href="http://127.0.0.1:8766'+path+'?', html)
                self.assertNotIn(state["selected"]["product_id"], html)

    def test_f02_unknown_does_not_select_first_color(self):
        with self.assertRaises(KeyError):
            preview.render(self.reader(), "/p/fixture-model-0/", "unknown", "http://127.0.0.1:1")

    def test_f03_missing_color_has_no_offers_or_image(self):
        html = preview.render(self.reader(), "/p/fixture-model-0/", None, "http://127.0.0.1:1")
        self.assertIn("Velg farge", html)
        self.assertNotIn("FIXTURE Shop", html)
        self.assertNotIn('aria-current="page"', html)
        self.assertNotIn('assets/fixture', html)

    def test_f04_missing_item_evidence_hides_entire_projection(self):
        self.doc["snapshots"][0]["value"]["selected"]["projection"] = None
        html = preview.render(self.write()(), "/p/fixture-model-0/", "svart", "http://127.0.0.1:1")
        self.assertIn("ikke dokumentert", html)
        self.assertNotIn("FIXTURE Shop", html)
        self.assertNotIn("assets/fixture", html)

    def test_f05_no_tracking_or_commercial_target_and_input_unchanged(self):
        bundle = self.reader()
        before = copy.deepcopy(bundle)
        html = preview.render(bundle, "/p/fixture-model-0/", "svart", "http://127.0.0.1:1")
        self.assertIn('href="/butikk/"', html)
        self.assertIn('<summary aria-label="Meny">', html)
        for value in ("googletagmanager", "tgt_", "/go/", "dataLayer", "GTM-"):
            self.assertNotIn(value, html)
        self.assertEqual(before, bundle)

    def test_f06_hash_change_revokes_existing_reader(self):
        self.path.write_text("{}")
        with self.assertRaises(ValueError): self.reader()

    def test_f07_removal_revokes_existing_reader(self):
        self.path.unlink()
        with self.assertRaises(OSError): self.reader()

    def test_f08_expired_inactive_or_overlong_review_refused(self):
        for change in ({"active": False}, {"expires_at": (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()},
                       {"expires_at": (datetime.now(timezone.utc)+timedelta(days=3)).isoformat()}):
            with self.subTest(change=change):
                self.doc = fixture() | change
                with self.assertRaises(ValueError): self.write()()

    def test_f09_valid_foreign_scope_refused(self):
        for key, other in (("property_id", "another-property"), ("environment", "production"), ("locale", "en")):
            with self.subTest(key=key):
                self.doc = fixture()
                self.doc["snapshots"][0]["value"]["request"][key] = other
                with self.assertRaises(ValueError): self.write()()

    def test_f10_mixed_revision_and_missing_or_duplicate_member_refused(self):
        for mutate in (lambda d: d["snapshots"][1]["value"]["source"].update(revision=2),
                       lambda d: d["snapshots"].pop(),
                       lambda d: d["snapshots"].__setitem__(1, copy.deepcopy(d["snapshots"][0]))):
            with self.subTest(mutate=mutate):
                self.doc = fixture(); mutate(self.doc)
                with self.assertRaises(ValueError): self.write()()

    def test_f11_pending_product_and_sibling_image_refused(self):
        self.doc["snapshots"][0]["value"]["request"]["pending_product_ids"].append("fixture-product-0-0")
        with self.assertRaises(ValueError): self.write()()
        self.doc = fixture()
        self.doc["snapshots"][0]["identity"]["image"] = self.doc["snapshots"][1]["identity"]["image"]
        with self.assertRaises(ValueError): self.write()()

    def test_f12_failures_leave_bytes_unchanged(self):
        before = self.path.read_bytes()
        with self.assertRaises(KeyError): preview.render(self.reader(), "/p/fixture-model-0/", "bad", "http://127.0.0.1:1")
        self.assertEqual(before, self.path.read_bytes())

    def test_f13_http_errors_security_and_revocation(self):
        server = preview.make_server(self.reader)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            client = http.client.HTTPConnection("127.0.0.1", server.server_port)
            for path, expected in (("/", 200), ("/p/fixture-model-0/?farge=svart", 200),
                                   ("/p/fixture-model-0/?farge=svart&farge=hvit", 404),
                                   ("/p/fixture-model-0/?farge=", 404), ("/p/fixture-model-0/?color=svart", 404),
                                   ("/p/fixture-model-0/?farge=unknown", 404), ("/../private.json", 404),
                                   ("/sitemap.xml", 404), ("/robots.txt", 200)):
                client.request("GET", path); response = client.getresponse(); response.read()
                self.assertEqual(response.status, expected, path)
                self.assertIn("noindex", response.getheader("X-Robots-Tag"))
                self.assertEqual(response.getheader("Cache-Control"), "no-store")
                self.assertIn("connect-src 'self'", response.getheader("Content-Security-Policy"))
            client.request("GET", "/", headers={"Host": "outside.example"})
            response = client.getresponse(); response.read(); self.assertEqual(response.status, 503)
            self.path.write_text("{}")
            client.request("GET", "/p/fixture-model-0/?farge=svart")
            response = client.getresponse(); text = response.read().decode()
            self.assertEqual(response.status, 503); self.assertNotIn("FIXTURE Shop", text)
            client.close()
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_f13_contract_refusal_is_atomic_503_without_diagnostics(self):
        class Refusal(Exception): pass
        def refuse(): raise Refusal("PRIVATE_DIAGNOSTIC_MUST_NOT_LEAK")
        server = preview.make_server(refuse)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            client = http.client.HTTPConnection("127.0.0.1",server.server_port)
            client.request("GET","/p/fixture-model-0/?farge=svart")
            response = client.getresponse(); body = response.read().decode()
            self.assertEqual(response.status,503)
            self.assertNotIn("PRIVATE_DIAGNOSTIC",body)
            self.assertNotIn("FIXTURE Shop",body)
            client.close()
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__": unittest.main()
