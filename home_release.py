"""Homepage-only release. Existing product rendering stays unchanged."""
from html import escape as e
import json
import hashlib
from home_ui import render_home, HOME_STYLE
from product_ui import ui_icon, PRODUCT_STYLE
from catalogue_media import public_image_url
from category_catalog import category_navigation, category_href, render_category_index
from catalogue_ui import render_listing, LISTING_STYLE

def page(title: str, body: str, *, base: str, noindex: bool, home: bool = False, category_nav: str = "") -> str:
    css_name = "home-" + hashlib.sha256((PRODUCT_STYLE + HOME_STYLE + LISTING_STYLE).encode()).hexdigest()[:12] + ".css"
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    header_search = '' if home else (
        f'<form class="sp-search" role="search" action="{e(base)}search/" method="get">'
        f'{ui_icon("search")}<input name="q" aria-label="Søk etter produktnavn" placeholder="Søk etter produkter …" required>'
        f'<button type="submit" aria-label="Søk">{ui_icon("arrow")}</button></form>')
    # Keep homepage's existing search IDs separate from the shared header.
    return f"""<!doctype html>
<html lang="nb"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">{robots}<title>{e(title)}</title>
<link rel="stylesheet" href="{e(base)}{css_name}"></head><body>
<a class="sp-skip" href="#main">Hopp til innhold</a>
<header class="sp-header"><div class="sp-shell sp-topbar">
<a class="sp-brand" href="{e(base)}" aria-label="SjekkPris – forsiden"><span>S</span>jekkPris</a>
<p class="sp-tagline">Smartere valg. Mer for pengene.</p>
{header_search}
<details class="sp-menu"><summary>{ui_icon('menu')}<span>Meny</span></summary>
<nav aria-label="Hovedmeny"><a href="{e(base)}">Alle produkter</a><a href="{e(base)}search/">Søk etter produkter</a></nav></details>
</div>{category_nav}</header><main id="main" class="sp-shell">{body}</main>
<footer class="sp-footer"><div class="sp-shell"><strong>SjekkPris</strong><p>Uavhengig prissammenligning. Du handler hos butikken.</p><p>Vi kan motta provisjon når du handler via lenkene våre. Beta – innholdet er under utvikling.</p></div></footer>
</body></html>"""


def home_money(amount):
    if amount is None: return None
    major, cents = divmod(int(amount['minor']), 100)
    price = f"{major:,}".replace(',', '\u00a0')
    if cents: price += f",{cents:02d}"
    return price + (' kr' if amount['currency'] == 'NOK' else ' ' + str(amount['currency']))


def write_home(client_products, out, *, base, noindex, day, segment, categories=None):
    products = client_products
    categories = categories or {}
    navigation = category_navigation(categories,base)
    css = '* { box-sizing:border-box }\n' + PRODUCT_STYLE + HOME_STYLE + LISTING_STYLE
    (out / 'home.css').write_text(css, encoding='utf-8')
    css_name = 'home-' + hashlib.sha256((PRODUCT_STYLE + HOME_STYLE + LISTING_STYLE).encode()).hexdigest()[:12] + '.css'
    (out / css_name).write_text(css, encoding='utf-8')
    body = render_home(products, base=base, money=home_money, day=day, segment=segment, category_links=[(n['name'],category_href(n,base)) for n in sorted(categories.values(),key=lambda n:n['name']) if n['parent'] is None])
    (out / 'index.html').write_text(page('SjekkPris – sammenlign priser', body, base=base, noindex=noindex, home=True, category_nav=navigation), encoding='utf-8')
    index = [{'name':p.get('local_name') or p['local_slug'], 'url':f"{base}p/{segment(p['namespace'])}/{segment(p['local_slug'])}/", 'price':home_money(p.get('lowest_item_price')), 'image':(p.get('image') or {}).get('url') if public_image_url((p.get('image') or {}).get('url')) else None} for p in products]
    (out / 'search-index.json').write_text(json.dumps(index), encoding='utf-8')
    body = render_listing(products, base=base, money=home_money, day=day, segment=segment)
    (out / 'search').mkdir(exist_ok=True)
    (out / 'search' / 'index.html').write_text(page('Søk – SjekkPris',body,base=base,noindex=True,category_nav=navigation),encoding='utf-8')

    if categories:
        target = out / 'kategori'
        target.mkdir(exist_ok=True)
        (target / 'index.html').write_text(page('Kategorier – SjekkPris', render_category_index(categories,base), base=base, noindex=True, category_nav=navigation), encoding='utf-8')
        for node in categories.values():
            crumbs = [(categories[key]['name'],category_href(categories[key],base)) for key in node['ancestors']]
            children = [(categories[key]['name'],category_href(categories[key],base),len(categories[key]['products'])) for key in node['children']]
            content = render_listing(list(node['products'].values()),base=base,money=home_money,day=day,segment=segment,title=node['name'],category=True,breadcrumbs=crumbs,children=children)
            folder = target / node['slug']
            folder.mkdir(exist_ok=True)
            (folder / 'index.html').write_text(page(node['name']+' – SjekkPris',content,base=base,noindex=True,category_nav=navigation),encoding='utf-8')
