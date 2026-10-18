"""Browser acceptance for isolated additional page designs."""
from extended_pages import PAGES


def capture_extended(page, origin, shots):
    pages=PAGES+[('guider','Guider'),('merker/nord','Nord'),('merker/fjord','Fjord'),('butikker/eksempel-a','Butikk'),('butikker/babybrezza','Baby Brezza')]
    for width in [360,390,430,768,1024,1280]:
        page.set_viewport_size({'width':width,'height':900})
        for slug,title in pages:
            page.goto(origin+'/'+slug+'/',wait_until='networkidle')
            assert page.get_by_role('heading',level=1).count()==1,slug
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(slug,width)
            assert page.locator('meta[name="robots"]').get_attribute('content')=='noindex'
            assert all(page.locator('.sp-extra .sp-guide-back,.sp-extra button,.sp-extra select,.sp-extra input:not([type=checkbox])').evaluate_all('(es)=>es.filter(e=>e.getBoundingClientRect().width).map(e=>e.getBoundingClientRect().height>=44)')), (slug,width,'control size')
            if slug in ['om','slik-fungerer-det','kontakt','personvern','konto','favoritter','prisvarsler','sammenlign']:
                nav=page.get_by_role('navigation',name='Relaterte sider')
                assert nav.locator('[aria-current="page"]').count()==1
                assert all(nav.locator('a').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().height>=44)'))
            if slug=='butikker/babybrezza':
                assert page.locator('.store-card').count()==15
                assert page.locator('.store-card:visible').count()==6
                assert page.locator('.store-facts dd').all_text_contents()==['15','4','1']
                assert 'fiktive produkter' not in page.locator('.sp-beta-notice').inner_text()
                assert all(page.locator('.store-card a').evaluate_all('(es)=>es.map(e=>e.href.startsWith("https://sjekkpris.no/p/catalogue/"))'))
                assert all(page.locator('.sp-store img:visible').evaluate_all('(es)=>es.map(e=>e.complete && e.naturalWidth>0)'))
                assert all(page.locator('.sp-store button:visible,.sp-store input,.sp-store select,.sp-store .store-link').evaluate_all('(es)=>es.filter(e=>e.getBoundingClientRect().width).map(e=>e.getBoundingClientRect().height>=44)'))
                page.locator('#store-query').fill('instant')
                assert page.locator('.store-card:visible').count()==1
                page.locator('#store-query').fill('ingen-treff')
                assert page.locator('#store-empty').is_visible()
                page.locator('#store-reset').click()
                assert page.locator('#store-query').evaluate('(e)=>e===document.activeElement')
                page.locator('[data-store-filter="Matlagere"]').click()
                assert page.locator('.store-card:visible').count()==1
                page.locator('[data-store-filter=""]').click()
                page.locator('#store-sort').select_option('price')
                assert 'Instant Warmer' in page.locator('.store-card:visible').first.inner_text()
                page.locator('#store-more').click()
                assert page.locator('.store-card:visible').count()==15
                assert page.locator('.store-card:visible').nth(6).locator('h3 a').evaluate('(e)=>e===document.activeElement')
                page.locator('#store-sort').select_option('name')
                page.locator('.store-sources summary').click()
                assert page.locator('.store-sources[open]').count()==1
                page.locator('.store-sources summary').click()
                page.evaluate('window.scrollTo(0,0)')
            if slug=='guider':
                assert page.locator('.sp-extra a[href="/guide/velg-tv/"]').count()==1
            if slug=='favoritter':
                assert page.locator('[data-favorite]').count()==2
                page.locator('[data-remove]').first.click();page.locator('[data-remove]').first.click()
                assert page.locator('#favorites-empty').is_visible()
                page.locator('#favorites-reset').click()
                assert page.locator('[data-favorite]').count()==2
            if slug=='prisvarsler':
                page.locator('#target-price').fill('0')
                assert page.locator('#target-price').evaluate('(e)=>!e.checkValidity()')
                page.locator('#target-price').fill('9000')
                page.get_by_role('button',name='Forhåndsvis prisvarsel').click()
                assert 'Ingen varsling' in page.locator('#alert-status').inner_text()
            if slug=='spor':
                page.get_by_role('button',name='Vis OLED-TV-er',exact=True).click()
                assert page.locator('#demo-answer a').count()==3
                assert page.locator('#demo-answer').evaluate('(e)=>e===document.activeElement')
                page.locator('#question').fill('ukjent spørsmål')
                page.get_by_role('button',name='Prøv eksempelsvar').click()
                assert 'ikke et svar' in page.locator('#answer-body').inner_text()
                page.get_by_role('button',name='Er frakt inkludert?',exact=True).click()
                assert page.locator('#demo-answer a').get_attribute('href').endswith('/demo-tv-2/#prices')
            if slug=='sammenlign':
                assert page.locator('#compare-body tr').count()==3
                page.locator('#differences').check()
                assert page.locator('#compare-body tr').count()==2
                page.locator('#compare-b').select_option('0')
                assert 'samme produkt' in page.locator('#compare-status').inner_text()
                assert 'Ingen forskjeller' in page.locator('#compare-body').inner_text()
                page.locator('#compare-b').select_option('2')
                assert page.locator('#compare-body tr').count()==3
                page.locator('#compare-a').select_option('4')
                assert '77' in page.locator('#compare-name-a').inner_text()
            if slug=='kontakt':
                page.locator('textarea').fill('Eksempel: feil bilde på produktet.')
                page.get_by_role('button',name='Prøv tilbakemelding').click()
                assert 'Ingenting er sendt' in page.locator('#feedback-status').inner_text()
            if slug=='konto':
                assert page.get_by_role('button',name='Innlogging kommer senere').is_disabled()
            page.screenshot(path=str(shots/f'extended_{slug.replace("/","_")}_{width}.png'),full_page=True)
