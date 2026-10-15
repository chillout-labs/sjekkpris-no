"""Check and capture real category pages without publishing."""
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path('_preview').resolve()
shots=root/'category-review';shots.mkdir(exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f'http://127.0.0.1:{server.server_port}'
results=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page()
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        paths=list(root.glob('kategori/*/index.html'))
        assert paths,'No category data returned'
        # Largest real group makes desktop grid and mobile filter behavior reviewable.
        paths.sort(key=lambda f:f.read_text().count('data-result'),reverse=True)
        selected=paths[:1]+paths[-1:]
        for target in selected:
            path='/'+target.relative_to(root).as_posix()
            for width in (360,390,430,1280):
                page.set_viewport_size({'width':width,'height':900})
                page.goto(origin+path,wait_until='networkidle')
                page.mouse.move(0,0)
                page.locator('.sp-card-photo img').evaluate_all("async images=>{await Promise.all(images.map(async img=>{img.loading='eager';await img.decode();}));}")
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(path,width)
                count=page.locator('[data-result]:visible').count()
                assert count>0
                if width in (390,1280):page.screenshot(path=str(shots/f'{target.parent.name}_{width}.png'),full_page=True)
                if width<768:page.locator('#filter-open').click()
                page.locator('#listing-min').fill('99999999')
                assert page.locator('[data-result]:visible').count()==0
                page.locator('#listing-reset').click()
                assert page.locator('[data-result]:visible').count()==count
                if width==390:page.screenshot(path=str(shots/f'{target.parent.name}_filters_390.png'),full_page=False)
                if width<768:
                    page.keyboard.press('Escape')
                    assert not page.locator('#filter-dialog').is_visible()
                    assert page.locator('#filter-open').evaluate('(el)=>el===document.activeElement')
                page.locator('#listing-sort').select_option('price')
                prices=page.locator('[data-result]').evaluate_all("rows=>rows.map(r=>r.dataset.price===''?Infinity:Number(r.dataset.price))")
                assert prices==sorted(prices)
                page.locator('[data-result] a').first.click()
                assert page.locator('.sp-product').count()==1
                assert page.locator('.sp-breadcrumb a[href*="/kategori/"]').count()>0
                results.append({'category':target.parent.name,'width':width,'products':count,'navigation_filters_sort':'pass'})
        page.goto(origin+'/kategori/',wait_until='networkidle')
        page.set_viewport_size({'width':360,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'category index overflow'
        page.screenshot(path=str(shots/'all-categories_360.png'),full_page=True)
        page.set_viewport_size({'width':1280,'height':900})
        page.screenshot(path=str(shots/'all-categories_1280.png'),full_page=True)
        assert not errors,errors
        browser.close()
finally:
    server.shutdown();server.server_close()
(shots/'checks.json').write_text(json.dumps(results,indent=2))
print(f'{len(results)} real category/viewport checks passed')
