"""F14–F20: actual browser checks on all 8 states at 390 and 1280 pixels.

Default is synthetic and starts its own loopback server. Real runs require the
same independently pinned private bundle and Core verifier as the preview.
Screenshots/results must stay outside Git when using private catalogue data.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from tools import model_preview as preview

# An invented fixture image, no provider image or real data in CI.
PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZ1EAAAAASUVORK5CYII=")


def check(reader, out, *, synthetic, axe=None):
    from playwright.sync_api import sync_playwright
    bundle = reader()
    before = reader.path.read_bytes()
    out.mkdir(parents=True, exist_ok=True)
    server = preview.make_server(reader)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    results, outgoing = [], []
    allowed_images = {img["url"] for state in bundle["states"].values()
                      if (p := state["selected"]["projection"]) and (image := p["image"])
                      for img in [image] + image.get("variants", [])}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width in (390, 1280):
                    context = browser.new_context(viewport={"width": width, "height": 900})
                    # Existing browser consent must never re-enable analytics here.
                    context.add_init_script("localStorage.setItem('sp-analytics-consent-v1','accepted')")
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))

                    def route(request_route):
                        url = request_route.request.url
                        if url.startswith(origin + "/"):
                            request_route.continue_()
                        elif url in allowed_images and request_route.request.resource_type == "image":
                            if synthetic:
                                request_route.fulfill(status=200, content_type="image/png", body=PIXEL)
                            else:
                                request_route.continue_()
                        else:
                            outgoing.append(url)
                            request_route.abort()
                    page.route("**/*", route)

                    def assert_state(path, selector, state):
                        model = next(m for m in bundle["models"] if m["desired_path"] == path)
                        selected = state["selected"]
                        assert page.locator("h1").count() == 1
                        assert page.locator("h1").inner_text() == model["name"]
                        assert page.locator("html").get_attribute("lang") == "nb"
                        assert page.locator('.sp-variants a[aria-current="page"]').inner_text() == selected["label"]
                        assert page.locator('.sp-variants a[aria-current="page"]').get_attribute("href") == path + "?farge=" + selector
                        assert page.locator('link[rel="canonical"]').count() == 1
                        assert page.locator('link[rel="canonical"]').get_attribute("href") == origin + path
                        assert "noindex" in page.locator('meta[name="robots"]').get_attribute("content")
                        assert page.locator('script[src],iframe').count() == 0
                        assert page.locator('a[href*="/go/"]').count() == 0
                        assert page.locator('.sp-variants a').evaluate_all("es=>es.every(e=>e.getBoundingClientRect().height>=44)")
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "horizontal overflow"
                        projection = selected["projection"]
                        if projection is not None:
                            image = projection["image"]
                            imgs = page.locator('.sp-gallery img')
                            if image:
                                assert imgs.count() > 0
                                assert imgs.first.get_attribute('src') == image['url']
                                page.wait_for_function("Array.from(document.querySelectorAll('.sp-gallery img')).every(e=>e.complete&&e.naturalWidth>0)")
                                assert imgs.first.get_attribute("alt")
                            else:
                                assert imgs.count() == 0
                            comparison = projection["comparison"]
                            rows = page.locator('#price-rows tr')
                            assert rows.count() == len(comparison["offers"])
                            ordered = preview.build.price_display_order(comparison["offers"], include_shipping=False)
                            for n, offer_index in enumerate(ordered):
                                offer = comparison["offers"][offer_index]
                                assert rows.nth(n).locator('td').first.locator('strong').inner_text() == offer['advertiser']
                                assert preview.build.money(offer["item_price"]) in rows.nth(n).inner_text() if offer["item_price"] else "Ingen pris" in rows.nth(n).inner_text()
                            assert page.locator('.sp-excluded-offers tbody tr').count() == len(comparison["excluded"])
                        else:
                            assert page.locator('.sp-gallery img,#price-rows tr').count() == 0
                            assert "ikke dokumentert" in page.locator('.sp-product-summary').inner_text()

                    for number, ((path, selector), state) in enumerate(bundle["states"].items()):
                        url = origin + path + "?farge=" + selector
                        response = page.goto(url, wait_until="networkidle")
                        assert response.status == 200
                        assert "noindex" in response.headers["x-robots-tag"]
                        assert response.headers["cache-control"] == "no-store"
                        assert_state(path, selector, state)
                        page.reload(wait_until="networkidle")
                        assert_state(path, selector, state)
                        if axe:
                            page.add_script_tag(path=str(axe))
                            audit = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
                            if audit["violations"]:
                                (out / "accessibility-findings.json").write_text(json.dumps(audit["violations"],ensure_ascii=False,indent=2),encoding="utf-8")
                            assert not audit["violations"], json.dumps([{k:v[k] for k in ('id','impact','description')} for v in audit['violations']])
                        # Native keyboard activation changes the entire document.
                        other = page.locator('.sp-variants a:not([aria-current])')
                        href = other.get_attribute("href")
                        other.press("Tab")
                        other.focus()
                        assert other.evaluate("e=>getComputedStyle(e).outlineStyle!=='none'")
                        other.press("Enter")
                        page.wait_for_url(origin + href)
                        page.wait_for_load_state("networkidle")
                        other_selector = href.split("?farge=")[1]
                        assert_state(path, other_selector, bundle["states"][(path, other_selector)])
                        page.go_back(wait_until="networkidle")
                        assert_state(path, selector, state)
                        # Both source price modes remain variant-specific.
                        switch = page.locator('#include-shipping')
                        if switch.count():
                            switch.check()
                            assert page.locator('[data-price-mode="total"]:visible').count() > 0
                            switch.uncheck()
                        shot = f"model-{number+1:02}-{width}.png"
                        page.screenshot(path=str(out / shot), full_page=True)
                        results.append({"model": path, "color": selector, "width": width, "direct_reload_keyboard_back": "passed",
                                        "canonical_noindex_accessibility": "passed", "image_and_complete_comparison": "passed",
                                        "axe": "passed" if axe else "not_run", "screenshot": shot})
                    for model in bundle["models"]:
                        page.goto(origin+model["desired_path"], wait_until="networkidle")
                        assert page.locator('.sp-variants a[aria-current="page"],#price-rows tr,.sp-gallery img').count() == 0
                        response = page.goto(origin+model["desired_path"]+"?farge=unknown", wait_until="networkidle")
                        assert response.status == 404
                    # Clickouts end locally and never visit a merchant.
                    path, selector = next(iter(bundle['states']))
                    page.goto(origin + path + '?farge=' + selector, wait_until="networkidle")
                    cta = page.locator('.sp-hero-cta a')
                    if cta.count():
                        cta.click(); page.wait_for_url(origin+'/butikk/')
                        assert 'deaktivert' in page.locator('h1').inner_text()
                    assert not errors, errors
                    context.close()
            finally:
                browser.close()
        assert not outgoing, outgoing
        assert reader.path.read_bytes() == before
        report = {"checked_at": datetime.now(timezone.utc).isoformat(), "synthetic": synthetic,
                  "bundle_sha256": preview.digest(before), "source_unchanged": True,
                  "unexpected_outgoing_requests": len(outgoing), "selections": results}
        (out / "browser-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding="utf-8")
        print(f"16/16 browser states passed; screenshots/results: {out}")
    finally:
        server.shutdown(); server.server_close(); thread.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--sha256")
    parser.add_argument("--core-checkout", type=Path)
    parser.add_argument("--image-origin")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--axe", type=Path)
    args = parser.parse_args()
    if args.bundle:
        if not all((args.sha256, args.core_checkout, args.image_origin)):
            parser.error("real run requires independent hash, pinned Core and image origin")
        if args.bundle.resolve().is_relative_to(ROOT) or args.out.resolve().is_relative_to(ROOT):
            parser.error("real input, results and screenshots must remain outside the repository")
        os.environ["CHILLOUT_ORIGIN"] = args.image_origin
        check(preview.BundleReader(args.bundle,args.sha256,preview.core_verifier(args.core_checkout)),args.out,synthetic=False,axe=args.axe)
    else:
        from model_preview_fixture import fixture, fixture_verifier
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"synthetic.json"
            raw = json.dumps(fixture()).encode(); path.write_bytes(raw)
            check(preview.BundleReader(path,preview.digest(raw),fixture_verifier),args.out,synthetic=True,axe=args.axe)


if __name__ == "__main__": main()
