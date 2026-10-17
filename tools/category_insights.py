"""Isolated category insight preview. Never used as production or AI evidence."""
from html import escape

STYLE = '''<style>
.sp-insights{margin:32px 0;padding:24px;border:1px solid #dce3ea;border-radius:12px;background:#f7f9fb;color:#10203b}.sp-insights h2{font-size:24px;margin:0 0 12px}.sp-insights p{line-height:1.65;max-width:760px}.sp-insights-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:24px 0}.sp-insights-grid div{background:white;padding:20px;border-radius:8px}.sp-insights dt{font-size:14px}.sp-insights dd{font-size:24px;font-weight:700;margin:8px 0 0;overflow-wrap:anywhere}.sp-insights nav{display:flex;flex-wrap:wrap;gap:12px}.sp-insights a{color:#006b5e;min-height:44px;display:inline-flex;align-items:center;text-decoration:underline}.sp-insights summary::after{content:"+";margin-left:auto;font-size:22px;padding-left:12px}.sp-insights details[open] summary::after{content:"−"}.sp-insights summary{cursor:pointer;min-height:44px;display:flex;align-items:center;font-weight:600}.sp-insights :focus-visible{outline:3px solid #177fc5;outline-offset:3px}@media(max-width:600px){.sp-insights{padding:20px}.sp-insights-grid{grid-template-columns:1fr;gap:8px}.sp-insights-grid div{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:16px}.sp-insights dd{font-size:21px;margin:0}}
.sp-tv-nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.sp-tv-nav a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 12px;box-sizing:border-box;border:1px solid var(--sp-line);border-radius:8px;color:var(--sp-ink);text-decoration:none;font-size:14px}.sp-tv-nav a[aria-current="page"]{background:var(--sp-mint);border-color:var(--sp-green);font-weight:700}.sp-tv-nav a:hover{background:var(--sp-mint)}.sp-tv-nav span{font-size:12px;color:var(--sp-muted)}.sp-tv-nav :focus-visible{outline:3px solid #177fc5;outline-offset:3px}.sp-insights a[aria-current="page"]{font-weight:700;text-decoration-thickness:2px}
</style>'''


TV_GROUPS = (
    ('tv', 'Alle TV-er', '/kategori/tv/', None),
    ('oled', 'OLED-TV-er', '/kategori/tv/oled/', {'demo-tv-1', 'demo-tv-2', 'demo-tv-5'}),
    ('led', 'LED-TV-er', '/kategori/tv/led/', {'demo-tv-3', 'demo-tv-4', 'demo-tv-6'}),
)


def category_links(products, current, *, compact=False):
    links=[]
    for key,label,url,slugs in TV_GROUPS:
        count=sum(slugs is None or p['local_slug'] in slugs for p in products)
        selected=' aria-current="page"' if key==current else ''
        suffix=f'<span aria-label="{count} modeller">{count}</span>' if compact else ''
        links.append(f'<a href="{url}"{selected}>{label}{suffix}</a>')
    label='TV-utvalg' if compact else 'Relaterte TV-utvalg'
    css=' class="sp-tv-nav"' if compact else ''
    return f'<nav{css} aria-label="{label}">'+''.join(links)+'</nav>'


def insights(products, title, current="tv"):
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
{category_links(products, current)}
</section>'''


def build_category_insights(out, products, render_listing, page, args):
    """Create only subsets supported by the explicit synthetic fixture labels."""
    path = out / 'kategori/tv/index.html'
    html = path.read_text(encoding='utf-8')
    html = html.replace('<div class="sp-listing-layout">', category_links(products, 'tv', compact=True)+'<div class="sp-listing-layout">', 1)
    marker = '<section class="sp-category-help"'
    # Place insights immediately before buying help; keep its existing style block.
    html = html.replace(marker, insights(products, 'TV-er') + marker, 1)
    path.write_text(html, encoding='utf-8')
    for kind, label, url, slugs in TV_GROUPS[1:]:
        subset = [p for p in products if p['local_slug'] in slugs]
        body = render_listing(subset, title=label, category=True,
                              breadcrumbs=[('TV', '/kategori/tv/')], **args)
        body = body.replace('<div class="sp-listing-layout">',
                            category_links(products, kind, compact=True)+'<div class="sp-listing-layout">', 1)
        body += insights(subset, label, kind)
        target = out / url.lstrip('/')
        target.mkdir(parents=True, exist_ok=True)
        (target / 'index.html').write_text(page(label + ' – designeksempel', body, base='/', noindex=True), encoding='utf-8')
