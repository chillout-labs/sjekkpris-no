"""Isolated category insight preview. Never used as production or AI evidence."""
from html import escape

STYLE = '''<style>
.sp-insights{margin:32px 0;padding:24px;border:1px solid #dce3ea;border-radius:12px;background:#f7f9fb;color:#10203b}.sp-insights h2{font-size:24px;margin:0 0 12px}.sp-insights p{line-height:1.65;max-width:760px}.sp-insights-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:24px 0}.sp-insights-grid div{background:white;padding:20px;border-radius:8px}.sp-insights dt{font-size:14px}.sp-insights dd{font-size:24px;font-weight:700;margin:8px 0 0;overflow-wrap:anywhere}.sp-insights nav{display:flex;flex-wrap:wrap;gap:12px}.sp-insights a{color:#006b5e;min-height:44px;display:inline-flex;align-items:center;text-decoration:underline}.sp-insights summary{cursor:pointer;min-height:44px;display:flex;align-items:center;font-weight:600}.sp-insights :focus-visible{outline:3px solid #177fc5;outline-offset:3px}@media(max-width:600px){.sp-insights{padding:20px}.sp-insights-grid{grid-template-columns:1fr;gap:8px}.sp-insights-grid div{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:16px}.sp-insights dd{font-size:21px;margin:0}}
</style>'''


def insights(products, title):
    prices = [p['lowest_item_price']['minor'] for p in products if p.get('lowest_item_price')]
    def money(value):
        return f'{value / 100:,.0f}'.replace(',', ' ') + ' kr'
    stats = [('Modeller i eksemplet', str(len(products))),
             ('Laveste eksempelpris', money(min(prices)) if prices else 'Ingen pris'),
             ('Høyeste eksempelpris', money(max(prices)) if prices else 'Ingen pris')]
    cards = ''.join(f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>' for label,value in stats)
    return STYLE + f'''<section class="sp-insights" aria-labelledby="insights-title">
<h2 id="insights-title">Pris og utvalg: {escape(title)}</h2>
<p><strong>Designeksempel med fiktive tall.</strong> Slik kan innsikt fra produktutvalget vises under produktene. Tallene nedenfor er beregnet fra betaens eksempelprodukter.</p>
<dl class="sp-insights-grid">{cards}</dl>
<details><summary>Hva bygger tallene på?</summary><p>Vi teller hver eksempelmodell én gang og bruker laveste oppgitte varepris per modell, uten frakt. {len(prices)} av {len(products)} modeller har pris. Tallene gjelder hele dette kategoriutvalget, uavhengig av filtre du velger ovenfor. De viser ikke det norske markedet eller prisutvikling over tid. Eksempeldataene har ingen reell observasjonsdato.</p></details>
<h3>Utforsk TV-typene</h3><p>Se produktutvalget for hver type. Samme produkt beholder den samme produktsiden uansett hvilken kategori du kommer fra.</p>
<nav aria-label="Relaterte TV-utvalg"><a href="/kategori/tv/">Alle TV-er</a><a href="/kategori/tv/oled/">OLED-TV-er</a><a href="/kategori/tv/led/">LED-TV-er</a></nav>
</section>'''


def build_category_insights(out, products, render_listing, page, args):
    """Create only subsets supported by the explicit synthetic fixture labels."""
    path = out / 'kategori/tv/index.html'
    html = path.read_text(encoding='utf-8')
    marker = '<section class="sp-category-help"'
    # Place insights immediately before buying help; keep its existing style block.
    html = html.replace(marker, insights(products, 'TV-er') + marker, 1)
    path.write_text(html, encoding='utf-8')
    for kind, label in [('oled', 'OLED-TV-er'), ('led', 'LED-TV-er')]:
        subset = [p for p in products if ('OLED' in p['local_name']) == (kind == 'oled')]
        body = '<nav aria-label="Tilbake til hovedkategori"><a href="/kategori/tv/">← Alle TV-er</a></nav>'
        body += render_listing(subset, title=label, category=True, **args)
        body += insights(subset, label)
        target = out / 'kategori/tv' / kind
        target.mkdir(parents=True, exist_ok=True)
        (target / 'index.html').write_text(page(label + ' – designeksempel', body, base='/', noindex=True), encoding='utf-8')
