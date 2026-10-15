"""Capture the real API build for visual review; never publishes or opens clickouts."""
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright


def main():
    root = Path('_preview').resolve()
    shots = root / 'review'
    shots.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(SimpleHTTPRequestHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            paths = sorted(root.glob('p/*/*/index.html'))
            assert paths, 'No real product pages generated'
            # Include products with and without images; bounded review set.
            selected = [f for f in paths if 'sp-image-empty' not in f.read_text()][:3]
            selected += [f for f in paths if 'sp-image-empty' in f.read_text()][:1]
            for target in selected:
                for width in (390, 1280):
                    page.set_viewport_size({'width': width, 'height': 900})
                    page.goto(origin + '/' + target.relative_to(root).as_posix(), wait_until='networkidle')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (target, width, 'overflow')
                    images = page.locator('.sp-image img')
                    if images.count():
                        images.evaluate('(e) => e.decode()')
                        assert images.evaluate('(e) => e.naturalWidth > 0')
                    slug = target.parent.name
                    page.screenshot(path=str(shots / f'{slug}_{width}_off.png'), full_page=True)
                    toggle = page.locator('#include-shipping')
                    if toggle.count():
                        toggle.check()
                        assert page.locator('.sp-product').get_attribute('data-price-basis') == 'total'
                        page.screenshot(path=str(shots / f'{slug}_{width}_on.png'), full_page=True)
                    results.append({'product': slug, 'width': width, 'image_loaded': bool(images.count())})
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    (shots / 'checks.json').write_text(json.dumps(results, indent=2))
    print(f'Captured {len(results)} real product/viewport combinations.')


if __name__ == '__main__':
    main()
