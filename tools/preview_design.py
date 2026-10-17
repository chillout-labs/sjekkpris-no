"""Build the launch design journey without credentials or publishing.

Run: python tools/preview_design.py
Then: python -m http.server 8765 --directory .design-preview
Open: http://localhost:8765/
All prices, stores and product specifications in this preview are illustrative.
"""
from pathlib import Path
import copy
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import build
import home_release
from design_fixtures import product_presentation, homepage_sections, category_help
from home_release import page, home_money
from catalogue_ui import render_listing
from test_build import offer, TOKEN_WINNER, TOKEN_OOS


def main():
    products, comparisons = [], {}
    for i, (name, brand, minor) in enumerate([
        ('Nord OLED 55 tommer', 'Nord', 999000),
        ('Nord OLED 65 tommer', 'Nord', 1499000),
        ('Fjord LED 50 tommer', 'Fjord', 649000),
        ('Fjord LED 65 tommer', 'Fjord', 899000),
        ('Nord OLED 77 tommer', 'Nord', 2199000),
        ('Fjord LED 43 tommer – uten bilde', 'Fjord', None),
    ]):
        slug=f'demo-tv-{i+1}'
        image={'url':'https://sjekkpris.no/assets/tv-illustration.webp'} if i<5 else None
        product={'namespace':'catalogue','local_slug':slug,'local_name':name,
                 'local_brand':brand,'local_category':'TV', 'image':image,
                 'categories':{'primary':{'id':'demo-tv','display_name':'TV','active':True,'path':[{'id':'demo-electronics','display_name':'Elektronikk'},{'id':'demo-tv','display_name':'TV'}]}},
                 'lowest_item_price':{'minor':minor,'currency':'NOK'} if minor else None,
                 'offer_count':3 if minor else 0,'lowest_item_price_confirmed_at':None}
        products.append(product)
        offers=[]
        if minor:
            a=offer('a','Eksempelbutikk A',minor,shipping_state='known_amount',total={'minor':minor+9900,'currency':'NOK'},token=TOKEN_WINNER)
            a['shipping']['amount']={'minor':9900,'currency':'NOK'}
            b=offer('b','Eksempelbutikk B',minor+5000,shipping_state='confirmed_free',total={'minor':minor+5000,'currency':'NOK'},token=TOKEN_OOS)
            c=offer('c','Eksempelbutikk C',minor+12000)
            for o in [a,b]:o['ranking']['total_price']['ranking_eligible']=True
            offers=[a,b,c]
        comparisons[slug]={'identity':copy.deepcopy(product),'offers':offers,'excluded':[],
                           'lowest_item_price':'a' if offers else None,'lowest_known_total_price':'b' if offers else None}
    class Fixtures:
        def get(self,path):
            return {'products':products} if path.split('?')[0].endswith('/catalogue') else comparisons[path.split('/')[-2]]
    out=ROOT/'.design-preview'
    original_product=build.product_body
    original_home=home_release.render_home
    original_listing=home_release.render_listing
    def fixture_listing(items, **kwargs):
        if kwargs.get('category') and kwargs.get('title')=='TV':
            kwargs['facets']=[('size','Skjermstørrelse',[(str(n),str(n)+' tommer') for n in [43,50,55,65,77]]),('panel','Paneltype',[('OLED','OLED'),('LED','LED')])]
            kwargs['facet_values']={p['local_slug']:{'size':p['local_name'].split(' tommer')[0].split()[-1],'panel':'OLED' if 'OLED' in p['local_name'] else 'LED'} for p in products}
        return original_listing(items,**kwargs)
    def full_product(product,body,**kwargs):
        return original_product(product,body,**kwargs,presentation=product_presentation(product))
    def full_home(products,**kwargs):
        result=original_home(products,**kwargs)
        start=result.index('<section class="sp-catalogue"')
        end=result.index('</section>',start)+len('</section>')
        args={k:v for k,v in kwargs.items() if k!='category_links'}
        (out/'home-catalogue.html').write_text(page('Forside med katalogdata',result,base='/',noindex=True,home=True),encoding='utf-8')
        return result[:start]+homepage_sections(products,**args)+result[end:]
    home_release.render_listing=fixture_listing
    build.product_body=full_product
    home_release.render_home=full_home
    try:
        build.build(Fixtures(),out,base='/',noindex=True)
    finally:
        home_release.render_listing=original_listing
        build.product_body=original_product
        home_release.render_home=original_home
    shutil.copyfile(ROOT/'tools/design_assets/tv-illustration.webp',out/'assets/tv-illustration.webp')
    # A detail crop of the same known illustration, not an invented second product photo.
    from PIL import Image
    with Image.open(ROOT/'tools/design_assets/tv-illustration.webp') as im:
        im.crop((im.width//4,im.height//4,im.width*3//4,im.height*3//4)).save(out/'assets/tv-detail.webp')
    category_page=out/'kategori/tv/index.html'
    category_page.write_text(category_page.read_text(encoding='utf-8').replace('</main>',category_help()+'</main>'),encoding='utf-8')
    guide=out/'guide/velg-tv';guide.mkdir(parents=True,exist_ok=True)
    from guide_fixture import guide_example
    (guide/'index.html').write_text(page('Eksempelguide – SjekkPris',guide_example(),base='/',noindex=True),encoding='utf-8')
    from rich_ui import search_highlights, loading_state, error_state
    from home_ui import render_product_card
    args=dict(base='/',money=home_money,day=build.day,segment=build.segment)
    cards=[render_product_card(p,**args) for p in products[:3]]
    highlights=search_highlights('TV til film og serier','Eksempel på behovssøk. Kortene viser oppsettet; utvalget er ikke en beregnet anbefaling.',cards,[('Endre behov','/search/?q=TV'),('Endre pris','/search/?q=OLED')])
    listing=render_listing(products,**args,title='Alle eksempelprodukter')
    target=out/'behovssok';target.mkdir(exist_ok=True)
    (target/'index.html').write_text(page('Behovssøk – designeksempel',highlights+listing,base='/',noindex=True),encoding='utf-8')
    target=out/'design-states';target.mkdir(exist_ok=True)
    states='<section class="sp-home sp-state-gallery"><h1>Komponenttilstander</h1><p>Isolerte designeksempler. Lastetilstanden nedenfor er bevisst statisk.</p>'+loading_state()+error_state('/kategori/tv/')+'<section class="sp-panel"><h2>Manglende data</h2><p><a href="/p/catalogue/demo-tv-6/">Produkt uten bilde, tilbud eller prishistorikk</a></p><p><a href="/search/?q=ingen-treff">Søk uten treff</a></p><p><a href="/p/catalogue/demo-tv-2/">Tilbud med kjent og ukjent frakt</a></p></section></section>'
    (target/'index.html').write_text(page('Komponenttilstander',states,base='/',noindex=True),encoding='utf-8')
    shop=out/'butikk' ;shop.mkdir(exist_ok=True)
    (shop/'index.html').write_text(page('Butikklenke – forhåndsvisning','<section class="sp-home" style="padding:32px 0"><h1>Her går kunden til butikken</h1><p>Dette er slutten på eksempelreisen. Ingen ekte butikk åpnes.</p><p><a href="/">Til startsiden</a></p></section>',base='/',noindex=True),encoding='utf-8')
    target=out/'designoversikt';target.mkdir(exist_ok=True)
    overview='''<section class="sp-home sp-state-gallery"><h1>Beta: design med eksempeldata</h1><p>Alle produkter, priser, butikker og produktkoblinger her er fiktive. Dette er en separat designforhåndsvisning, ikke den ekte produktkatalogen.</p><div class="sp-details"><section class="sp-panel"><h2>Komplett produktside</h2><p>Bilder, varianter, tilbud, prishistorikk, spesifikasjoner, bruksområder, alternativer, tilbehør og spørsmål/svar.</p><a href="/p/catalogue/demo-tv-2/">Åpne komplett eksempel</a></section><section class="sp-panel"><h2>Når data mangler</h2><p>Kontroller hvordan siden fungerer uten bilde, tilbud og utvidet produktinnhold.</p><a href="/p/catalogue/demo-tv-6/">Åpne eksempel med manglende data</a></section><section class="sp-panel"><h2>Forside og søk</h2><p>Produktrekker og fremhevede resultater med eksempeldata. Popularitet og anbefalinger er ikke beregnet.</p><a href="/">Forside</a><br><a href="/behovssok/">Behovssøk</a></section><section class="sp-panel"><h2>Guidemal</h2><p>Lesemal med innholdsfortegnelse, tabell, spørsmål og produktlenker.</p><a href="/guide/velg-tv/">Åpne eksempelguide</a></section><section class="sp-panel"><h2>Hva venter på Chillout?</h2><p>Reelle spesifikasjoner, bildegallerier, varianter, prishistorikk og dokumenterte produktkoblinger må leveres og kvalitetssikres før de brukes på ekte produktsider.</p><a href="/design-states/">Se feil og tomme tilstander</a></section></div></section>'''
    (target/'index.html').write_text(page('Beta – designoversikt',overview,base='/',noindex=True),encoding='utf-8')
    banner='<aside style="padding:12px 16px;background:#fff3d6;color:#10203b;text-align:center;font:13px Arial,sans-serif"><a href="/designoversikt/">Beta / designoversikt</a> · eksempelprodukter, illustrasjonsbilde og eksempelpriser. <a href="/">Startside</a> · <a href="/search/?q=OLED">Søk</a> · <a href="/kategori/tv/">TV-kategori</a> · <a href="/behovssok/">Behovssøk</a> · <a href="/design-states/">Tilstander</a></aside>'
    for target in out.rglob('*.html'):
        html=re.sub(r'(<body\b[^>]*>)', lambda match: match.group(1)+banner, target.read_text(encoding='utf-8'), count=1)
        html=html.replace('https://sjekkpris.no/assets/', '/assets/')
        html=re.sub(r'https://[^"\s]+/go/tgt_[A-Z0-9]+','/butikk/',html)
        target.write_text(html,encoding='utf-8')
    (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n',encoding='utf-8')
    print(f'Design preview ready: {out}\nServe with: python -m http.server 8765 --directory .design-preview')

if __name__=='__main__':main()
