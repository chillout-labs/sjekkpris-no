"""Render actual product pages with isolated fixtures; never publish this output.
Run: python tools/preview_product.py
Requires the local Python Playwright package and Chromium.
"""
from pathlib import Path
import copy
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import build
from test_build import INDEX, COMPARISONS, offer, TOKEN_WINNER, TOKEN_OOS


def main():
    from playwright.sync_api import sync_playwright
    product = copy.deepcopy(INDEX['products'][0])
    product['local_name'] = 'Testprodukt – lokal forhåndsvisning'
    a = offer('a', 'Butikk A', 149900, shipping_state='known_amount', total={'minor':159800,'currency':'NOK'}, token=TOKEN_WINNER)
    a['shipping']['amount'] = {'minor':9900,'currency':'NOK'}
    b = offer('b', 'Butikk B', 154900, shipping_state='confirmed_free', total={'minor':154900,'currency':'NOK'}, token=TOKEN_OOS)
    c = offer('c', 'Butikk C', 169900)
    for item in [a,b]: item['ranking']['total_price']['ranking_eligible'] = True
    body = copy.deepcopy(COMPARISONS['fixture-lamp'])
    body.update(offers=[a,b,c], excluded=[], lowest_item_price='a', lowest_known_total_price='b')
    class Fixtures:
        def get(self, path):
            return {'products':[product]} if path.endswith('/catalogue') else body
    shots = ROOT / '.screenshots-product-review'
    shots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sjekkpris-preview-') as tmp:
        out = Path(tmp) / 'site'
        build.build(Fixtures(), out, base='/', noindex=True)
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(out))
        server = ThreadingHTTPServer(('127.0.0.1',0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    page = browser.new_page()
                    page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin+'/') else route.abort())
                    for width in [390,1280]:
                        page.set_viewport_size({'width':width,'height':900})
                        page.goto(f"{origin}/p/{product['namespace']}/{product['local_slug']}/", wait_until='networkidle')
                        assert page.locator('.sp-header form').count() == 1
                        assert page.locator('#price-winner a:visible').count() == 1
                        assert page.locator('.sp-product').evaluate("e=>getComputedStyle(e).fontFamily").startswith('Arial')
                        for mode in ['off','on']:
                            page.locator('#include-shipping').set_checked(mode=='on')
                            page.screenshot(path=str(shots/f'product_{width}_{mode}.png'),full_page=True)
                finally: browser.close()
        finally:
            server.shutdown()
            server.server_close()
    print(f'Screenshots: {shots}')

if __name__ == '__main__': main()
