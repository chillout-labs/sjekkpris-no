"""Acceptance checks for shareable retailer state and keyboard error recovery."""

def capture_store_state(page, origin):
    url=origin+'/butikker/babybrezza/'
    def ready():
        page.wait_for_function("!document.querySelector('.store-products').hasAttribute('aria-busy')")
    for width in [390,1280]:
        page.set_viewport_size({'width':width,'height':900})
        page.goto(url,wait_until='networkidle');ready()
        page.locator('#store-next').click();ready()
        assert 'side=2' in page.url
        assert page.locator('.store-card').count()==3
        page.go_back();ready()
        assert page.locator('.store-card').count()==12
        page.go_forward();ready()
        assert page.locator('.store-card').count()==3
        page.reload(wait_until='networkidle');ready()
        assert page.locator('#store-page-number').inner_text()=='Side 2 av 2'
        page.locator('#store-sort').select_option('price');ready()
        assert 'sort=pris' in page.url and 'side=' not in page.url
        assert 'Instant Warmer' in page.locator('.store-card').first.inner_text()
        page.locator('[data-store-filter="Matlagere"]').click();ready()
        assert 'gruppe=Matlagere' in page.url
        page.reload(wait_until='networkidle');ready()
        assert page.locator('[data-store-filter="Matlagere"]').get_attribute('aria-pressed')=='true'
        assert page.locator('.store-card').count()==1
        page.locator('[data-store-filter=""]').click();ready()
        page.locator('#store-query').fill('instant');ready()
        page.reload(wait_until='networkidle');ready()
        assert page.locator('#store-query').input_value()=='instant'
        assert page.locator('.store-card').count()==1
        # Unsupported and huge page/filter values are normalized, never trusted.
        page.goto(url+'?side=999999&gruppe=ukjent&sort=ukjent',wait_until='networkidle');ready()
        assert 'side=2' in page.url and 'gruppe=' not in page.url and 'sort=' not in page.url
        page.goto(url+'?side=-1',wait_until='networkidle');ready()
        assert page.locator('.store-card').count()==12 and 'side=' not in page.url
        # Hash-only history must not force users away from the information section.
        page.locator('a[href="#store-about"]').click()
        page.locator('a[href="#store-insights"]').click()
        page.go_back()
        assert page.url.endswith('#store-about')
        assert page.locator('#store-about').bounding_box()['y']>=-5
        # An error must not leave focus on a hidden Next button.
        page.goto(url,wait_until='networkidle');ready()
        page.route('**/kort/*.json',lambda route:route.abort())
        page.locator('#store-next').click();ready()
        assert page.locator('#store-retry').evaluate('(e)=>e===document.activeElement')
        page.unroute('**/kort/*.json')
        page.locator('#store-retry').click();ready()
        assert page.locator('#store-products-title').evaluate('(e)=>e===document.activeElement')
        assert page.locator('.store-card').count()==3
