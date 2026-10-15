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
    build.build(Fixtures(),out,base='/',noindex=True)
    shutil.copyfile(ROOT/'tools/design_assets/tv-illustration.webp',out/'assets/tv-illustration.webp')
    category=out/'kategori'/'tv';category.mkdir(parents=True,exist_ok=True)
    content=render_listing(products,base='/',money=home_money,day=build.day,segment=build.segment,title='TV',category=True)
    (category/'index.html').write_text(page('TV – designforhåndsvisning',content,base='/',noindex=True),encoding='utf-8')
    shop=out/'butikk';shop.mkdir(exist_ok=True)
    (shop/'index.html').write_text(page('Butikklenke – forhåndsvisning','<section class="sp-home" style="padding:32px 0"><h1>Her går kunden til butikken</h1><p>Dette er slutten på eksempelreisen. Ingen ekte butikk åpnes.</p><p><a href="/">Til startsiden</a></p></section>',base='/',noindex=True),encoding='utf-8')
    banner='<aside style="padding:12px 16px;background:#fff3d6;color:#10203b;text-align:center;font:13px Arial,sans-serif">Designforhåndsvisning · eksempelprodukter, illustrasjonsbilde og eksempelpriser. <a href="/">Startside</a> · <a href="/search/?q=OLED">Søk</a> · <a href="/kategori/tv/">TV-kategori</a></aside>'
    for target in out.rglob('*.html'):
        html=target.read_text(encoding='utf-8').replace('<body>','<body>'+banner)
        html=html.replace('https://sjekkpris.no/assets/', '/assets/')
        html=re.sub(r'https://[^"\s]+/go/tgt_[A-Z0-9]+','/butikk/',html)
        target.write_text(html,encoding='utf-8')
    (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n',encoding='utf-8')
    print(f'Design preview ready: {out}\nServe with: python -m http.server 8765 --directory .design-preview')

if __name__=='__main__':main()
