"""Capture and check the isolated design journey. Requires Playwright Chromium."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent

def main():
    out=ROOT/'.design-preview'
    shots=out/'screenshots';shots.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SimpleHTTPRequestHandler,directory=str(out)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch()
            page=browser.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin+'/') else route.abort())
            for width in [360,390,768,1280]:
                page.set_viewport_size({'width':width,'height':900})
                for name,path in [('home','/'),('search','/search/?q=OLED'),('category','/kategori/tv/'),('product','/p/catalogue/demo-tv-2/'),('empty','/p/catalogue/demo-tv-6/')]:
                    page.goto(origin+path,wait_until='networkidle')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,path,'overflow')
                    if name in ['home','search','category']:
                        page.locator('.sp-card-photo img:visible').evaluate_all("async images=>{await Promise.all(images.map(async e=>{e.loading='eager';await e.decode();}));}")
                        assert page.locator('.sp-card-photo img:visible').first.evaluate('(e)=>e.complete&&e.naturalWidth>0')
                    if name=='product':
                        assert page.locator('.sp-image img:visible').evaluate('(e)=>e.complete&&e.naturalWidth>0')
                        page.locator('[data-gallery-index="1"]').click()
                        assert page.locator('[data-gallery-slide]:visible').count()==1
                        page.locator('[data-gallery-index="0"]').click()
                        page.locator('.sp-faq summary').first.click()
                        assert page.locator('.sp-faq details').first.get_attribute('open') is not None
                    if name=='search':
                        assert page.locator('[data-result]:visible').count()==3
                    page.screenshot(path=str(shots/f'{name}_{width}.png'),full_page=True)
                page.goto(origin+'/search/?q=OLED',wait_until='networkidle')
                if width<768:page.locator('#filter-open').click()
                page.locator('#listing-max').fill('10000')
                assert page.locator('[data-result]:visible').count()==1
                page.locator('#listing-max').fill('1')
                assert page.locator('#listing-empty').is_visible()
                if width<768:page.locator('#filter-apply').click()
                page.locator('#listing-show-all').click()
                assert page.locator('[data-result]:visible').count()==6
                page.locator('#listing-sort').select_option('price')
                assert page.locator('[data-result]').first.get_attribute('data-price')=='649000'
                assert page.locator('[data-result]').last.get_attribute('data-price')==''
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
    print('Design journey checks passed; responsive screenshots captured.')

if __name__=='__main__':main()
