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
            from capture_store_state import capture_store_state
            capture_store_state(page, origin)
            from capture_extended import capture_extended
            capture_extended(page, origin, shots)
            for width in [360,390,430,768,1024,1280]:
                page.set_viewport_size({'width':width,'height':900})
                for name,path in [('oled','/kategori/tv/oled/'),('led','/kategori/tv/led/'),('not_found','/404.html'),('directory','/kategori/'),('types','/produkttyper/'),('portrait','/p/catalogue/demo-hoy/'),('square','/p/catalogue/demo-pakning/'),('wide','/p/catalogue/demo-bred/'),('many','/p/catalogue/demo-mange-tilbud/'),('cards','/korteksempler/'),('guide','/guide/velg-tv/'),('home_catalogue','/home-catalogue.html'),('states','/design-states/'),('intent','/behovssok/'),('home','/'),('search','/search/?q=OLED'),('category','/kategori/tv/'),('product','/p/catalogue/demo-tv-2/'),('empty','/p/catalogue/demo-tv-6/')]:
                    page.goto(origin+path,wait_until='networkidle')
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,path,'overflow')
                    assert page.get_by_role('heading',level=1).count()==1,(width,path,'primary heading')
                    if name in ['category','oled','led']:
                        nav=page.get_by_role('navigation',name='TV-utvalg',exact=True)
                        assert nav.locator('a').count()==3
                        assert nav.locator('a[aria-current="page"]').count()==1
                        assert nav.locator('span').all_text_contents()==['6','3','3']
                        assert all(nav.locator('a').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().height>=44)'))
                        nav.locator('a').last.focus()
                        assert nav.locator('a').last.evaluate('(e)=>e===document.activeElement')
                        assert nav.bounding_box()['y'] < page.locator('#search-results').bounding_box()['y']
                        insight=page.locator('.sp-insights')
                        assert insight.count()==1
                        assert insight.bounding_box()['y']>=page.locator('.sp-listing').bounding_box()['y']+page.locator('.sp-listing').bounding_box()['height']
                        assert insight.locator('nav a').count()==3
                        assert insight.locator('a[aria-current="page"]').count()==1
                        insight.locator('summary').click()
                        assert insight.locator('details[open]').count()==1
                        insight.screenshot(path=str(shots/f'insights_{name}_{width}.png'))
                        insight.locator('summary').click()
                        if name in ['oled','led']:
                            assert page.locator('#search-results>li').count()==3
                            assert insight.locator('dd').all_text_contents()==(['3','9 990 kr','21 990 kr'] if name=='oled' else ['3','6 490 kr','8 990 kr'])
                        page.evaluate('window.scrollTo(0,0)')
                    if name=='not_found':
                        assert page.get_by_role('heading',level=1).inner_text()=='La oss finne veien videre'
                        assert page.locator('.sp-recovery-actions a').count()==2
                        assert page.locator('.sp-recovery-actions .sp-cta').evaluate('(e)=>getComputedStyle(e).color!==getComputedStyle(e).backgroundColor')
                        assert all(page.locator('.sp-recovery-actions a').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().height>=44)'))
                    if name=='directory':
                        assert page.locator('.sp-category-tree a').count()>=2
                        page.locator('.sp-category-tree a').last.focus()
                    if name in ['portrait','square','wide']:
                        for index in range(3):
                            page.locator(f'[data-gallery-index="{index}"]').click()
                            img=page.locator('[data-gallery-slide]:visible img')
                            img.evaluate('async e=>await e.decode()')
                            assert img.evaluate('(e)=>e.naturalWidth>0 && getComputedStyle(e).objectFit==="contain"')
                            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                        page.locator('[data-gallery-index="0"]').click()
                        page.locator('.sp-image-expand').click()
                        page.locator('.sp-image-dialog img').evaluate('async e=>await e.decode()')
                        assert page.locator('.sp-image-close').is_visible()
                        page.keyboard.press('Escape')
                    if name=='many':
                        assert page.locator('#price-rows tr').count()==12
                        assert page.locator('#price-rows tr:visible').count()==6
                        page.get_by_role('button',name='Vis alle 12 tilbud',exact=True).click()
                        assert page.locator('#price-rows tr:visible').count()==12
                        assert page.locator('#price-rows .sp-cta').count()==9
                        assert page.locator('.sp-excluded-title + table .sp-cta').count()==0
                        page.locator('#include-shipping').check()
                        assert page.locator('.sp-product').get_attribute('data-price-basis')=='total'
                        assert 'Totalpris ukjent' in page.locator('#price-rows tr').last.inner_text()
                        page.locator('#prices').screenshot(path=str(shots/f'many_total_{width}.png'))
                        page.locator('#include-shipping').uncheck()
                        page.get_by_role('button',name='Vis færre tilbud',exact=True).click()
                        assert page.locator('#price-rows tr:visible').count()==6
                        assert page.locator('#offer-more').get_attribute('aria-expanded')=='false'
                        page.locator('#include-shipping').check()
                        assert page.locator('#price-rows tr:visible [data-total-order]').evaluate_all('(es)=>es.map(e=>Number(e.dataset.totalOrder))')==list(range(6))
                        page.locator('#include-shipping').uncheck()
                        assert all(page.locator('.sp-variants a').evaluate_all('(es)=>es.map(e=>e.scrollWidth<=e.clientWidth)'))
                    if name=='cards':
                        assert page.locator('.sp-card-no-price').count()==2
                        assert all(page.locator('.sp-product-card').evaluate_all('(es)=>es.map(e=>e.scrollWidth<=e.clientWidth)'))
                    if name=='guide':
                        page.get_by_role('link',name='2. Sammenlign egenskapene',exact=True).click()
                        assert page.locator('#egenskaper').is_visible()
                        page.get_by_text('Er dette en ferdig kjøpsguide?',exact=True).click()
                        assert page.locator('.sp-guide details[open]').count()==1
                        page.evaluate('window.scrollTo(0,0)')
                    if name=='home_catalogue':
                        assert page.locator('.sp-home-categories .sp-see-all').get_attribute('href')=='/kategori/'
                        for selector in ['.sp-home-categories nav', '.sp-home-hero .sp-examples>div']:
                            row=page.locator(selector)
                            links=row.locator('a')
                            if links.count():
                                links.last.focus()
                                page.wait_for_function('(selector)=>{const e=document.querySelector(selector).querySelector("a:last-child");const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}',arg=selector)
                                links.first.focus()
                        rail=page.locator('.sp-catalogue .sp-product-grid')
                        assert rail.evaluate('(e)=>e.scrollWidth>e.clientWidth')
                        assert page.locator('.sp-catalogue .sp-see-all').get_attribute('href')=='/search/'
                        page.locator('.sp-catalogue .sp-product-card a').last.focus()
                        assert rail.evaluate('(e)=>e.scrollLeft>0')
                        page.locator('.sp-catalogue .sp-product-card a').first.focus()
                    if name in ['search','category']:
                        assert page.get_by_label('Sorter etter',exact=True).count()==1
                        if width<768:
                            assert page.locator('#filter-open').bounding_box()['height']>=44
                            assert page.locator('#listing-sort').bounding_box()['height']>=44
                        if name=='category':
                            assert page.locator('.sp-product-category:visible').count()==0
                            assert page.locator('.sp-card-attributes').count()==5
                            assert all(page.locator('.sp-card-attributes').evaluate_all('(es)=>es.map(e=>e.scrollWidth<=e.clientWidth)'))
                            if width<768:page.locator('#filter-open').click()
                            page.get_by_label('Skjermstørrelse: 65 tommer',exact=True).check()
                            assert page.locator('#result-status').inner_text()=='2 produkter'
                            page.get_by_label('Paneltype: OLED',exact=True).check()
                            assert page.locator('#result-status').inner_text()=='1 produkt'
                            page.get_by_label('Skjermstørrelse: 55 tommer',exact=True).check()
                            assert page.locator('#result-status').inner_text()=='2 produkter'
                            page.screenshot(path=str(shots/f'category_facets_{width}.png'))
                            active=page.locator('#mobile-active-filters' if width<768 else '#active-filters')
                            active.get_by_role('button',name='Fjern filter: Skjermstørrelse: 55 tommer',exact=True).click()
                            assert not page.get_by_label('Skjermstørrelse: 55 tommer',exact=True).is_checked()
                            assert page.locator('#result-status').inner_text()=='1 produkt'
                            page.get_by_label('Skjermstørrelse: 65 tommer',exact=True).uncheck()
                            page.get_by_label('Skjermstørrelse: 43 tommer',exact=True).check()
                            assert page.locator('#result-status').inner_text()=='0 produkter'
                            page.locator('#listing-reset').click()
                            assert page.locator('#result-status').inner_text()=='6 produkter'
                            if width<768:page.locator('#filter-apply').click()
                            help=page.locator('.sp-category-help')
                            assert help.is_visible()
                            page.get_by_text('Er frakt med i prisen på produktkortene?',exact=True).click()
                            assert help.locator('details[open]').count()==1
                            page.get_by_text('Er frakt med i prisen på produktkortene?',exact=True).click()
                            help.screenshot(path=str(shots/f'category_help_{width}.png'))
                            page.evaluate('window.scrollTo(0,0)')
                    if name in ['home','search','category']:
                        page.locator('.sp-card-photo img:visible').evaluate_all("async images=>{await Promise.all(images.map(async e=>{e.loading='eager';await e.decode();}));}")
                        assert page.locator('.sp-card-photo img:visible').first.evaluate('(e)=>e.complete&&e.naturalWidth>0')
                    if name=='product':
                        if width<768:
                            assert not page.locator('#home-query').is_visible()
                            assert not page.locator('.sp-category-nav').is_visible()
                            assert page.locator('.sp-breadcrumb a:visible').count()==1
                            assert not page.locator('.sp-meta [data-product-meta=category]').is_visible()
                            assert page.locator('.sp-topbar').bounding_box()['height']<=64
                        else:
                            assert page.locator('#home-query').is_visible()
                        page.screenshot(path=str(shots/f'product_compact_top_{width}.png'))
                        page.locator('.sp-image-expand').click()
                        assert page.locator('.sp-image-dialog').is_visible()
                        page.locator('.sp-image-dialog img').evaluate('async e=>{await e.decode();}')
                        assert page.locator('.sp-image-dialog img').evaluate('(e)=>e.complete&&e.naturalWidth>0')
                        first_source=page.locator('.sp-image-dialog img').get_attribute('src')
                        page.get_by_role('button',name='Neste bilde',exact=True).click()
                        assert page.locator('.sp-image-dialog img').get_attribute('src')!=first_source
                        assert page.locator('.sp-image-controls [role=status]').inner_text()=='Bilde 2 av 2'
                        page.keyboard.press('ArrowLeft')
                        assert page.locator('.sp-image-dialog img').get_attribute('src')==first_source
                        page.screenshot(path=str(shots/f'product_zoom_{width}.png'))
                        page.keyboard.press('Escape')
                        assert not page.locator('.sp-image-dialog').is_visible()
                        assert page.locator('.sp-image-expand').evaluate('(e)=>document.activeElement===e')
                        page.locator('.sp-tabs a[href="#specifications"]').click()
                        assert page.locator('.sp-tabs a[aria-current]').get_attribute('href')=='#specifications'
                        assert page.locator('#specifications').evaluate('(e)=>document.activeElement===e')
                        page.locator('.sp-tabs a[href="#prices"]').click()
                        assert page.locator('.sp-image img:visible').evaluate('(e)=>e.complete&&e.naturalWidth>0')
                        page.locator('[data-gallery-index="1"]').click()
                        assert page.locator('[data-gallery-slide]:visible').count()==1
                        page.locator('[data-gallery-index="1"]').press('ArrowLeft')
                        assert page.locator('[data-gallery-index="0"]').get_attribute('aria-pressed')=='true'
                        assert page.locator('[data-gallery-index="0"]').evaluate('(e)=>document.activeElement===e')
                        page.locator('.sp-faq summary').first.click()
                        assert page.locator('.sp-faq details').first.get_attribute('open') is not None
                        history=page.locator('.sp-history-control input')
                        history.fill('0')
                        assert '16 990 kr' in page.locator('.sp-history-control output').inner_text()
                        history.press('End')
                        assert '14 990 kr' in page.locator('.sp-history-control output').inner_text()
                    if name=='product':
                        if width<768:
                            page.locator('.sp-mobile-search-toggle').click()
                            assert page.locator('#home-query').evaluate('(e)=>document.activeElement===e')
                        page.locator('#home-query').scroll_into_view_if_needed()
                        page.locator('#home-query').fill('Nord')
                        page.locator('#home-suggestions [role=option]').first.wait_for()
                        page.locator('#home-query').press('ArrowDown')
                        assert page.locator('#home-query').get_attribute('aria-activedescendant')=='home-option-0'
                        page.screenshot(path=str(shots/f'product_autocomplete_{width}.png'))
                        page.locator('#home-query').press('Escape')
                        assert not page.locator('#home-suggestions').is_visible()
                        if width<768:
                            assert not page.locator('#home-query').is_visible()
                            assert page.locator('.sp-mobile-search-toggle').evaluate('(e)=>document.activeElement===e')
                        else:
                            page.locator('#home-query').fill('')
                    if name=='empty':
                        assert page.locator('.sp-image-expand').count()==0
                    if name=='search':
                        assert page.locator('[data-result]:visible').count()==3
                    page.locator('.sp-menu summary').click()
                    assert page.locator('.sp-menu nav').is_visible()
                    page.locator('.sp-menu nav a').first.focus()
                    page.keyboard.press('Escape')
                    assert not page.locator('.sp-menu nav').is_visible()
                    assert page.locator('.sp-menu summary').evaluate('(e)=>document.activeElement===e')
                    page.screenshot(path=str(shots/f'{name}_{width}.png'),full_page=True)
                page.goto(origin+'/p/catalogue/demo-tv-2/',wait_until='networkidle')
                page.locator('#product-title').evaluate("e=>e.textContent='Eksempelprodukt med ekstra langt norsk modellnavn og variantbeskrivelse – spesialutgave for store rom'")
                page.locator('.sp-specs dt').first.evaluate("e=>e.textContent='EkstraordinærtLangtSammenhengendeSpesifikasjonsnavn'")
                page.locator('.sp-key-attributes dd').first.evaluate("e=>e.textContent='EkstraLangAttributtverdiUtenMellomrom'")
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,'long content overflow')
                page.screenshot(path=str(shots/f'product_long_content_{width}.png'),full_page=True)
                page.goto(origin+'/search/?q=OLED',wait_until='networkidle')
                if width<768:page.locator('#filter-open').click()
                page.locator('#listing-max').fill('10000')
                assert page.locator('[data-result]:visible').count()==1
                page.locator('#listing-max').fill('1')
                assert page.locator('#listing-empty').is_visible()
                if width<768:page.locator('#filter-apply').click()
                page.screenshot(path=str(shots/f'search_no_results_{width}.png'),full_page=True)
                page.locator('#listing-clear-filters').click()
                assert page.locator('[data-result]:visible').count()==3
                assert page.locator('#home-query').input_value()=='OLED'
                if width<768:page.locator('#filter-open').click()
                page.locator('#listing-min').fill('20000')
                page.locator('#listing-max').fill('10000')
                assert page.locator('#listing-price-help').is_visible()
                assert page.locator('#listing-max').get_attribute('aria-invalid')=='true'
                page.screenshot(path=str(shots/f'filter_invalid_range_{width}.png'),full_page=True)
                if width<768:page.locator('#filter-apply').click()
                page.locator('#listing-show-all').click()
                assert page.locator('[data-result]:visible').count()==9
                page.locator('#listing-sort').select_option('price')
                assert page.locator('[data-result]').first.get_attribute('data-price')=='24900'
                assert page.locator('[data-result]').last.get_attribute('data-price')==''
            page.goto(origin+'/search/?q=kontaktlinse',wait_until='networkidle')
            assert page.locator('[data-result]:visible').count()==1
            assert page.locator('[data-result]:visible a').get_attribute('href')=='/p/catalogue/demo-pakning/'
            # A short viewport must retain the close/apply controls, allow the
            # fields to scroll, and restore focus when rotating to desktop.
            page.set_viewport_size({'width':667,'height':375})
            page.goto(origin+'/search/?q=OLED',wait_until='networkidle')
            page.locator('#filter-open').click()
            page.locator('#listing-min').fill('20000')
            page.locator('#listing-max').fill('10000')
            for control in ['#filter-close','#filter-apply']:
                assert page.locator(control).evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}')
            page.locator('#listing-reset').scroll_into_view_if_needed()
            page.screenshot(path=str(shots/'filter_short_viewport.png'))
            page.locator('#listing-reset').click()
            page.set_viewport_size({'width':1280,'height':720})
            page.wait_for_function("!document.querySelector('#filter-dialog').open && document.activeElement===document.querySelector('.sp-listing-filters summary')")
            assert page.locator('#listing-max').input_value()==''
            page.set_viewport_size({'width':390,'height':720})
            page.locator('#filter-open').click()
            page.keyboard.press('Escape')
            assert page.locator('#filter-open').evaluate('(e)=>document.activeElement===e')
            page.set_viewport_size({'width':667,'height':375})
            page.goto(origin+'/kategori/tv/',wait_until='networkidle')
            page.locator('#filter-open').click()
            for choice in page.locator('[data-facet]').all():choice.check()
            assert page.locator('#mobile-active-filters button').count()==7
            for control in ['#filter-close','#filter-apply']:
                assert page.locator(control).evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}')
            page.screenshot(path=str(shots/'facets_short_viewport.png'))
            page.locator('#listing-reset').scroll_into_view_if_needed()
            page.locator('#listing-reset').click()
            assert page.locator('#mobile-active-filters button').count()==0
            page.keyboard.press('Escape')
            page.set_viewport_size({'width':1024,'height':600})
            page.goto(origin+'/kategori/tv/',wait_until='networkidle')
            page.locator('#listing-reset').scroll_into_view_if_needed()
            assert page.locator('#listing-reset').evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}')
            for width in [390,1280]:
                page.set_viewport_size({'width':width,'height':900})
                page.route('**/search-index.json',lambda route:route.fulfill(status=503,body='Unavailable'))
                page.goto(origin+'/search/',wait_until='networkidle')
                page.locator('#home-query').fill('Nord')
                page.wait_for_function("document.querySelector('#home-search-status').textContent.includes('kunne ikke lastes')")
                assert page.locator('#home-search-status').get_attribute('class')=='sp-search-feedback'
                assert page.locator('#home-query').get_attribute('aria-busy') is None
                page.screenshot(path=str(shots/f'search_error_{width}.png'))
                page.unroute('**/search-index.json')
                page.locator('#home-query').fill('Nord OLED')
                page.locator('#home-suggestions [role=option]').first.wait_for()
                assert page.locator('#home-search-status').get_attribute('class')=='sp-sr'
                page.locator('#home-query').fill('zzzznomatch')
                page.wait_for_function("document.querySelector('#home-search-status').textContent.includes('Ingen produktforslag')")
                page.screenshot(path=str(shots/f'search_no_suggestions_{width}.png'))
                page.locator('#home-query').press('Escape')
                assert page.locator('#home-search-status').inner_text()==''
            nojs=browser.new_page(java_script_enabled=False)
            nojs.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin+'/') else route.abort())
            nojs.goto(origin+'/p/catalogue/demo-mange-tilbud/',wait_until='networkidle')
            assert nojs.locator('#price-rows tr:visible').count()==12
            assert not nojs.locator('#offer-more').is_visible()
            nojs.close()
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
    print('Design journey checks passed; responsive screenshots captured.')

if __name__=='__main__':main()
