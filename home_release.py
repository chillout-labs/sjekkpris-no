"""Homepage-only release. Existing product rendering stays unchanged."""
from html import escape as e
import json
from home_ui import render_home, HOME_STYLE
from product_ui import ui_icon, PRODUCT_STYLE

def page(title: str, body: str, *, base: str, noindex: bool, home: bool = False) -> str:
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
<link rel="stylesheet" href="{e(base)}home.css"></head><body>
<a class="sp-skip" href="#main">Hopp til innhold</a>
<header class="sp-header"><div class="sp-shell sp-topbar">
<a class="sp-brand" href="{e(base)}" aria-label="SjekkPris – forsiden"><span>S</span>jekkPris</a>
<p class="sp-tagline">Smartere valg. Mer for pengene.</p>
{header_search}
<details class="sp-menu"><summary>{ui_icon('menu')}<span>Meny</span></summary>
<nav aria-label="Hovedmeny"><a href="{e(base)}">Alle produkter</a><a href="{e(base)}search/">Søk etter produkter</a></nav></details>
</div></header><main id="main" class="sp-shell">{body}</main>
<footer class="sp-footer"><div class="sp-shell"><strong>SjekkPris</strong><p>Uavhengig prissammenligning. Du handler hos butikken.</p><p>Vi kan motta provisjon når du handler via lenkene våre. Beta – innholdet er under utvikling.</p></div></footer>
</body></html>"""


def home_money(amount):
    if amount is None: return None
    major, cents = divmod(int(amount['minor']), 100)
    price = f"{major:,}".replace(',', '\u00a0')
    if cents: price += f",{cents:02d}"
    return price + (' kr' if amount['currency'] == 'NOK' else ' ' + str(amount['currency']))


def write_home(client_products, out, *, base, noindex, day, segment):
    products = client_products
    css = '* { box-sizing:border-box }\n' + PRODUCT_STYLE + HOME_STYLE
    (out / 'home.css').write_text(css, encoding='utf-8')
    body = render_home(products, base=base, money=home_money, day=day, segment=segment)
    (out / 'index.html').write_text(page('SjekkPris – sammenlign priser', body, base=base, noindex=noindex, home=True), encoding='utf-8')
    index = [{'name':p.get('local_name') or p['local_slug'], 'url':f"{base}p/{segment(p['namespace'])}/{segment(p['local_slug'])}/"} for p in products]
    (out / 'search-index.json').write_text(json.dumps(index), encoding='utf-8')
    links = ''.join(f'<li data-result><a href="{e(p["url"], quote=True)}">{e(p["name"])}</a></li>' for p in index)
    body = '<section class="sp-home" style="padding:32px 0"><h1>Søk etter produkter</h1><p id="result-status" role="status"></p><ul id="search-results">'+links+'</ul><noscript>Her vises alle tilgjengelige produkter.</noscript></section>'
    body += """<script>(()=>{
      const form=document.querySelector('.sp-search'), input=form.querySelector('input');
      const rows=Array.from(document.querySelectorAll('[data-result]'));
      input.value=new URLSearchParams(location.search).get('q')||'';
      function filter(){let n=0;const q=input.value.trim().toLocaleLowerCase('nb');
        rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase('nb').includes(q);if(!row.hidden)n++;});
        document.getElementById('result-status').textContent=n ? n+' produkter funnet' : 'Ingen produkter funnet. Prøv et annet produktnavn.';
      }
      form.addEventListener('submit',e=>{e.preventDefault();filter();});input.addEventListener('input',filter);filter();
    })();</script>"""
    (out / 'search').mkdir(exist_ok=True)
    (out / 'search' / 'index.html').write_text(page('Søk – SjekkPris',body,base=base,noindex=True),encoding='utf-8')
