"""Data-supported homepage, following the locked homepage v1 reference.

No popularity, deal, editorial, account or AI capabilities are implied.
"""
from html import escape

from product_ui import ui_icon
from catalogue_media import image_markup, category_markup


def card_image(product):
    """Optional presentation image; catalogue enrichment remains an API concern."""
    image = image_markup(product.get('image'), product.get('local_name') or 'Produktbilde',
                         sizes='(max-width: 600px) 45vw, (max-width: 1024px) 30vw, 250px')
    if image:
        return f'<div class="sp-card-image sp-card-photo">{image}</div>'
    return f'<div class="sp-card-image">{ui_icon("image")}<span>Bilde mangler</span></div>'


def render_product_card(product, *, base, money, day, segment):
    slug = segment(product['local_slug'])
    namespace = segment(product['namespace'])
    name = product.get('local_name') or product['local_slug']
    href = escape(f'{base}p/{namespace}/{slug}/', quote=True)
    price = money(product.get('lowest_item_price'))
    confirmed = day(product.get('lowest_item_price_confirmed_at'))
    count = int(product.get('offer_count') or 0)
    offer_text = '1 tilbud' if count == 1 else f'{count} tilbud'
    return (
        f'<li data-result data-name="{escape(name, quote=True)}" data-price="{product.get("lowest_item_price", {}).get("minor", "") if product.get("lowest_item_price") else ""}" data-brand="{escape(product.get("local_brand") or "", quote=True)}"><article class="sp-product-card"><a href="{href}">'
        f'{card_image(product)}'
        f'<h3>{escape(name)}</h3>'
        + category_markup(product.get("categories"))
        + (f'<p class="sp-product-brand">{escape(product["local_brand"])}</p>' if product.get("local_brand") else "")
        + (f'<p class="sp-card-price-label">Laveste varepris</p><p class="sp-card-price">{escape(price)}</p><p class="sp-card-shipping">Frakt kan komme i tillegg</p>'
           if price else '<p class="sp-card-no-price">Ingen pris</p>')
        + f'<div class="sp-card-bottom"><span>{offer_text}</span>{ui_icon("arrow")}</div>'
        + (f'<p class="sp-card-confirmed">Pris bekreftet {escape(confirmed)}</p>' if price and confirmed else '')
        + '</a></article></li>'
    )


def render_home(products, *, base, money, day, segment, category_links=()):
    category_section = ('<section class="sp-home-categories" aria-labelledby="home-categories-title"><div class="sp-catalogue-heading"><h2 id="home-categories-title">Utforsk kategorier</h2><a class="sp-see-all" href="' + escape(base, quote=True) + 'kategori/">Se alle' + ui_icon("arrow") + '</a></div><nav aria-label="Utforsk kategorier">' + ''.join(f'<a href="{escape(url, quote=True)}"><span>{escape(name)}</span>{ui_icon("arrow")}</a>' for name, url in category_links) + '</nav></section>') if category_links else ''
    cards = [render_product_card(p, base=base, money=money, day=day, segment=segment) for p in products]
    examples = []
    if products:
        indices = list(dict.fromkeys([0, len(products) // 2, len(products) - 1]))
        for i in indices:
            p = products[i]
            href = escape(f'{base}p/{segment(p["namespace"])}/{segment(p["local_slug"])}/', quote=True)
            examples.append(f'<a class="sp-example" href="{href}">{ui_icon("search")}<span>{escape(p.get("local_name") or p["local_slug"])}</span></a>')
    examples_html = ('<div class="sp-examples"><p>Prøv for eksempel</p><div>' + ''.join(examples) + '</div></div>') if examples else ''
    catalogue = ('<ul class="sp-product-grid">' + ''.join(cards) + '</ul>') if cards else '<p class="sp-home-empty">Ingen produkter er publisert ennå.</p>'
    return f'''<div class="sp-home sp-home-front">
<section class="sp-home-hero" aria-labelledby="home-title">
<img class="sp-home-art" src="{escape(base)}assets/sjekkpris-startside.webp" alt="" width="1774" height="887" fetchpriority="high">
<div class="sp-home-hero-content">
<h1 id="home-title">Hva vil du sammenligne?</h1>
<p class="sp-home-intro">Finn produktet du ønsker, og sammenlign priser fra butikkene.</p>
<div class="sp-home-search-wrap">
<form id="home-search-form" class="sp-home-search" role="search" action="{escape(base)}search/" method="get" data-index="{escape(base)}search-index.json">
{ui_icon('search')}<input id="home-query" name="q" type="search" required autocomplete="off" placeholder="Søk etter produktnavn …" aria-label="Søk etter produktnavn" aria-describedby="home-search-help" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="home-suggestions">
<button type="submit" aria-label="Søk">{ui_icon('arrow')}</button></form>
<ul id="home-suggestions" class="sp-suggestions" role="listbox" aria-label="Produktforslag" hidden></ul>
</div>
<p id="home-search-help" class="sp-home-help">Søket finner foreløpig produkter etter navn.</p>
<p id="home-search-status" class="sp-sr" role="status" aria-live="polite"></p>
{examples_html}</div></section>
<section class="sp-home-trust" aria-label="Om SjekkPris">
<div>{ui_icon('search')}<p>Sammenlign priser<span>fra butikkene</span></p></div>
<div>{ui_icon('truck')}<p>Totalpris<span>når frakt er kjent</span></p></div>
<div>{ui_icon('shield')}<p>Uavhengig sammenligning<span>Du handler hos butikken</span></p></div>
</section>
<section class="sp-catalogue" id="products" aria-labelledby="catalogue-title">
<div class="sp-catalogue-heading"><h2 id="catalogue-title">Produkter</h2><a class="sp-see-all" href="{escape(base)}search/">Se alle <span class="sp-sr">{len(products)} {'produkt' if len(products) == 1 else 'produkter'}</span>{ui_icon('arrow')}</a></div>
{catalogue}</section>
{category_section}
<div class="sp-home-signoff">{ui_icon('shield')}<div><strong>Smartere valg. Mer for pengene.</strong><p>Uavhengig prissammenligning. Frakt vises når den er kjent.</p></div></div>
</div><script>{HOME_SEARCH_SCRIPT}</script>'''


HOME_SEARCH_SCRIPT = r"""
(() => {
  document.querySelectorAll('.sp-home-categories nav, .sp-home-hero .sp-examples>div').forEach(row => {
    row.addEventListener('focusin', event => {
      const link = event.target.closest('a');
      if (link) link.scrollIntoView({block:'nearest', inline:'nearest', behavior:'instant'});
    });
  });
  const form = document.getElementById('home-search-form');
  const input = document.getElementById('home-query');
  const list = document.getElementById('home-suggestions');
  const status = document.getElementById('home-search-status');
  let items = [], selected = -1, index = null, pending = null, version = 0;
  function feedback(message = '', visible = false) {
    status.textContent = message;
    status.className = visible ? 'sp-search-feedback' : 'sp-sr';
  }
  function close() {
    feedback();
    input.removeAttribute('aria-busy');
    list.hidden = true; selected = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }
  function choose(i) {
    selected = i;
    Array.from(list.children).forEach((el, j) => el.setAttribute('aria-selected', String(i === j)));
    if (i < 0) input.removeAttribute('aria-activedescendant');
    else {
      input.setAttribute('aria-activedescendant', list.children[i].id);
      list.children[i].scrollIntoView({block:'nearest'});
    }
  }
  async function suggest() {
    const request = ++version, query = input.value.trim().toLocaleLowerCase('nb');
    close(); list.replaceChildren(); items = [];
    if (!query) return;
    if (!index) { feedback('Henter produktforslag …', true); input.setAttribute('aria-busy', 'true'); }
    try {
      if (!pending) pending = fetch(form.dataset.index).then(r => {
        if (!r.ok) throw new Error('Search index unavailable');
        return r.json();
      }).then(data => {
        if (!Array.isArray(data)) throw new Error('Invalid search index');
        return data;
      }).catch(error => { pending = null; throw error; });
      index = index || await pending;
      if (request !== version || document.activeElement !== input) return;
      input.removeAttribute('aria-busy');
      items = index.filter(p => typeof p.name === 'string' && typeof p.url === 'string' &&
        p.url.startsWith('/') && !p.url.startsWith('//') && !p.url.includes('\\') &&
        p.name.toLocaleLowerCase('nb').includes(query)).slice(0, 8);
      items.forEach((p, i) => {
        const li = document.createElement('li');
        li.id = 'home-option-' + i; li.role = 'option';
        li.setAttribute('aria-selected', 'false');
        const picture=document.createElement('span');picture.className='sp-suggestion-image';picture.setAttribute('aria-hidden','true');
        const source=Array.from(document.querySelectorAll('.sp-product-card>a')).find(a=>a.getAttribute('href')===p.url)?.querySelector('img');
        if(source){const img=document.createElement('img');img.src=source.currentSrc||source.src;img.alt='';img.referrerPolicy='no-referrer';img.addEventListener('error',()=>img.remove());picture.append(img);}
        const text=document.createElement('span');text.className='sp-suggestion-copy';
        const name=document.createElement('span');name.textContent=p.name;text.append(name);
        if(p.price){const price=document.createElement('strong');price.textContent=p.price; text.append(price);}
        li.append(picture,text);
        li.addEventListener('mousedown', e => e.preventDefault());
        li.addEventListener('click', () => { window.location.href = p.url; });
        list.append(li);
      });
      list.hidden = !items.length;
      input.setAttribute('aria-expanded', String(items.length > 0));
      feedback(items.length ? items.length + ' produktforslag. Bruk piltastene for å velge.' : 'Ingen produktforslag. Prøv et annet produktnavn, eller trykk Søk.', !items.length);
    } catch (_) {
      if (request === version) {
        input.removeAttribute('aria-busy');
        feedback('Produktforslag kunne ikke lastes. Trykk Søk for å se treffene, eller skriv videre for å prøve igjen.', true);
      }
    }
  }
  input.addEventListener('input', suggest);
  input.addEventListener('focus', () => { if (input.value.trim()) suggest(); });
  input.addEventListener('blur', () => { ++version; close(); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { ++version; close(); return; }
    if (list.hidden || !items.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); choose(Math.min(selected + 1, items.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); choose(Math.max(selected - 1, -1)); }
    if (e.key === 'Enter' && selected >= 0) { e.preventDefault(); window.location.href = items[selected].url; }
  });
  form.addEventListener('submit', e => { if (!input.value.trim()) { e.preventDefault(); input.focus(); } });
})();
"""


HOME_STYLE = r"""
.sp-home { color:var(--sp-ink); font:15px/1.55 Arial,Helvetica,sans-serif }
.sp-home h1,.sp-home h2,.sp-home h3,.sp-home p { margin:0 }
.sp-home-hero { position:relative; isolation:isolate; text-align:left; background:#f1f5f6; padding:56px 32px; margin:0 -28px; min-height:420px }
.sp-home-art { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:center; z-index:-2 }
.sp-home-hero::before { content:""; position:absolute; inset:0; background:linear-gradient(90deg,#f3f7faed 0%,#f3f7fad9 33%,#f3f7fa00 62%); z-index:-1 }
.sp-home-hero-content { width:49%; max-width:570px }
.sp-home-hero .sp-examples>div { justify-content:flex-start }
.sp-home h1 { font-size:44px; line-height:1.13; letter-spacing:-1.5px; font-weight:750 }
.sp-home-intro { font-size:17px; margin-top:12px!important }
.sp-home-search-wrap { position:relative; max-width:800px; margin:26px auto 0; text-align:left }
.sp-home-search { display:flex; align-items:center; gap:14px; padding:7px 8px 7px 20px; border:1.5px solid var(--sp-green); border-radius:36px; background:#fff; box-shadow:0 3px 12px #00645412; min-height:66px }
.sp-home-search>svg { width:27px; height:27px; color:var(--sp-ink) }
.sp-home-search input { flex:1; width:100%; min-width:0; height:48px; padding:0; font:16px Arial,Helvetica,sans-serif; color:var(--sp-ink); background:none; border:0 }
.sp-home-search input:focus-visible { outline:0 }.sp-home-search:focus-within { outline:3px solid #177fc5; outline-offset:3px }
.sp-home-search button { display:flex; align-items:center; justify-content:center; flex-shrink:0; width:48px; height:48px; border-radius:50%; border:0; background:var(--sp-green); color:#fff; cursor:pointer }
.sp-home-search button:hover { background:#004c40 }
.sp-home .sp-home-help { margin-top:11px; font-size:12px; color:var(--sp-muted) }
.sp-examples { margin:18px auto 0; max-width:900px }.sp-examples>p { font-size:12px; color:var(--sp-muted); margin-bottom:8px }.sp-examples>div { display:flex; flex-wrap:wrap; justify-content:center; gap:8px }
a.sp-example { display:flex; align-items:center; gap:7px; min-height:44px; max-width:100%; padding:7px 13px; border:1px solid #dce9ef; border-radius:24px; background:#fff; color:var(--sp-ink); font-size:12px; text-decoration:none }
.sp-example span { overflow-wrap:anywhere }.sp-example svg { width:15px; height:15px }.sp-example:hover { border-color:var(--sp-green); background:var(--sp-mint) }
.sp-suggestions { position:absolute; top:calc(100% + 8px); left:0; right:0; z-index:20; max-height:360px; overflow-y:auto; background:#fff; border:1px solid var(--sp-line); border-radius:12px; padding:6px; margin:0; list-style:none; box-shadow:0 10px 30px #10203b14 }
.sp-search-feedback { margin:10px 0 0; padding:12px 16px; border:1px solid var(--sp-line); border-radius:12px; background:#fff; color:var(--sp-ink); font-size:14px; line-height:1.5; text-align:left; overflow-wrap:anywhere }
.sp-suggestions[hidden] { display:none }.sp-suggestions li { padding:13px 12px; min-height:44px; border-radius:7px; overflow-wrap:anywhere; cursor:pointer }.sp-suggestions li[aria-selected=true],.sp-suggestions li:hover { background:var(--sp-mint); color:var(--sp-green) }
.sp-home-trust { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:24px; padding:20px 26px; background:#f0faf8; border-radius:18px; margin:20px 0 32px }
.sp-home-trust>div { display:flex; align-items:center; gap:14px }.sp-home-trust svg { width:28px; height:28px; color:var(--sp-green) }.sp-home-trust p { font-size:13px }.sp-home-trust span { display:block; color:var(--sp-muted); font-size:12px }
.sp-catalogue-heading { display:flex; align-items:baseline; justify-content:space-between; gap:16px; margin-bottom:18px }.sp-catalogue-heading h2 { font-size:26px; letter-spacing:-.5px }.sp-catalogue-heading>span { font-size:13px; color:var(--sp-muted) }
.sp-product-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; list-style:none; margin:0; padding:0 }.sp-product-grid>li { min-width:0 }
.sp-product-card { height:100%; border:1px solid var(--sp-line); border-radius:12px; background:#fff; overflow:hidden; box-shadow:0 2px 5px #10203b03 }
.sp-product-card>a { display:flex; flex-direction:column; height:100%; padding:14px; color:var(--sp-ink); text-decoration:none }.sp-product-card:hover { border-color:#9bbeb5 }.sp-product-card>a:focus-visible { outline-offset:-4px }
.sp-card-image { aspect-ratio:1.45; background:var(--sp-surface); border-radius:8px; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:8px; color:var(--sp-muted); font-size:11px; margin-bottom:14px }.sp-card-image svg { width:35px; height:35px; color:#91a1b5 }
.sp-product-card h3 { font-size:16px; line-height:1.35; overflow-wrap:anywhere; margin-bottom:auto; padding-bottom:16px }.sp-home .sp-card-price-label { font-size:11px; color:var(--sp-muted) }.sp-home .sp-card-price { font-size:23px; line-height:1.3; font-weight:700; font-variant-numeric:tabular-nums }.sp-home .sp-card-shipping { font-size:11px; color:var(--sp-muted); margin-top:3px }.sp-card-no-price { font-size:18px; color:var(--sp-muted) }
.sp-card-bottom { display:flex; align-items:center; justify-content:space-between; color:var(--sp-green); font-size:13px; margin-top:15px }.sp-card-bottom svg { width:18px; height:18px }.sp-home .sp-card-confirmed { color:var(--sp-muted); font-size:10px; margin-top:7px }
.sp-home-empty { border:1px solid var(--sp-line); border-radius:12px; padding:32px; color:var(--sp-muted) }
.sp-home-signoff { display:flex; align-items:center; gap:18px; padding:22px 26px; margin:32px 0 8px; background:var(--sp-mint); border-radius:12px; color:var(--sp-green) }.sp-home-signoff>svg { width:32px; height:32px }.sp-home-signoff strong { font-size:16px }.sp-home-signoff p { font-size:12px; color:var(--sp-muted); margin-top:4px }
.sp-home :focus-visible { outline:3px solid #177fc5; outline-offset:3px }
@media(min-width:768px) and (max-width:999px) { .sp-product-grid { grid-template-columns:repeat(3,minmax(0,1fr)) }.sp-home h1 { font-size:38px }.sp-home-trust { gap:16px; padding:18px } }
@media(max-width:767px) {
 .sp-home-hero { display:flex; flex-direction:column; margin:0 -16px; padding:28px 16px 24px; text-align:left; min-height:0; background:#f3f7fa }
 .sp-home-hero::before { display:none }.sp-home-hero-content { width:100%; max-width:none }.sp-home-art { display:none; position:static; order:2; z-index:auto; width:calc(100% + 32px); max-width:none; height:150px; margin:20px -16px 0; object-position:right center }.sp-home h1 { font-size:32px; line-height:1.1; letter-spacing:-.9px; max-width:310px }.sp-home .sp-home-intro { font-size:14px; margin-top:10px!important; max-width:330px }
 .sp-home-search-wrap { margin-top:20px }.sp-home-search { gap:8px; min-height:58px; padding:5px 5px 5px 13px }.sp-home-search input { font-size:16px; height:44px }.sp-home-search>svg { width:21px; height:21px }.sp-home-search button { width:44px; height:44px }.sp-home .sp-home-help { font-size:11px }
 .sp-examples { margin-top:16px }.sp-examples>div { justify-content:flex-start; gap:7px }.sp-example { font-size:11px!important; padding:6px 10px!important }
 .sp-home-trust { display:none }.sp-catalogue { margin-top:24px }.sp-catalogue-heading { margin-bottom:14px }.sp-catalogue-heading h2 { font-size:23px }.sp-catalogue-heading>span { font-size:12px }
 .sp-product-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px }.sp-product-card>a { padding:10px }.sp-card-image { aspect-ratio:1.25; margin-bottom:11px }.sp-product-card h3 { font-size:14px; padding-bottom:12px }.sp-home .sp-card-price { font-size:20px }.sp-card-bottom { font-size:12px; margin-top:12px }
 .sp-home-signoff { padding:18px 14px; gap:12px; margin-top:24px }.sp-home-signoff strong { font-size:14px }.sp-home-signoff p { font-size:11px }
}
"""

HOME_STYLE += r"""
.sp-card-photo { background:white; padding:8px }
.sp-card-photo img { width:100%; height:100%; min-height:0; object-fit:contain }
.sp-product-grid>li[hidden] { display:none }
"""

HOME_STYLE += r"""
.sp-suggestions li { display:flex; gap:12px; align-items:center }
.sp-suggestion-image { width:48px; height:48px; flex-shrink:0; border-radius:6px; background:var(--sp-surface) }
.sp-suggestion-image img { width:100%; height:100%; object-fit:contain; background:white }
.sp-suggestion-copy { min-width:0; display:grid; gap:4px; font-size:14px; line-height:1.35 }
.sp-suggestion-copy strong { font-size:13px; color:var(--sp-green) }
.sp-home-categories { margin:36px 0 }
.sp-home-categories h2 { font-size:26px; letter-spacing:-.5px; margin-bottom:18px }
.sp-home-categories nav { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px }
.sp-home-categories nav a { display:flex; align-items:center; justify-content:space-between; gap:16px; min-height:64px; border:1px solid var(--sp-line); border-radius:10px; padding:16px; text-decoration:none; color:var(--sp-ink) }
.sp-home-categories nav a:hover { background:var(--sp-mint); border-color:var(--sp-green) }
.sp-home-categories svg { width:20px; height:20px; flex-shrink:0; color:var(--sp-green) }
@media(max-width:767px) { .sp-home-categories nav { grid-template-columns:1fr }.sp-home-categories h2 { font-size:23px } }
"""


def render_header_search(base):
    base=escape(base,quote=True)
    return f'''<div class="sp-header-search-wrap"><form id="home-search-form" class="sp-search" role="search" action="{base}search/" method="get" data-index="{base}search-index.json">
{ui_icon('search')}<input id="home-query" name="q" type="search" autocomplete="off" aria-label="Søk etter produktnavn" placeholder="Søk etter produkter …" required role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="home-suggestions">
<button type="submit" aria-label="Søk">{ui_icon('arrow')}</button></form>
<ul id="home-suggestions" class="sp-suggestions" role="listbox" aria-label="Produktforslag" hidden></ul><p id="home-search-status" class="sp-sr" role="status" aria-live="polite"></p></div>'''


HOME_STYLE += r"""
.sp-header-search-wrap { position:relative;flex:1;min-width:0;max-width:580px;margin-left:auto }.sp-header-search-wrap .sp-search { max-width:none;margin:0;width:100% }.sp-header-search-wrap .sp-suggestions { font:14px/1.4 Arial,Helvetica,sans-serif;max-height:min(420px,60vh);overscroll-behavior:contain }.sp-header-search-wrap .sp-suggestion-copy strong { color:var(--sp-ink) }
.sp-suggestion-image:empty { display:flex;align-items:center;justify-content:center;color:var(--sp-muted) }.sp-suggestion-image:empty::after { content:'▧';font-size:22px }
@media(max-width:767px) { .sp-header-search-wrap { order:2;flex:0 0 100%;max-width:none;width:100%;margin:0 }.sp-header-search-wrap .sp-search { flex:auto }.sp-header-search-wrap .sp-suggestions { max-height:55vh }.sp-header-search-wrap input { font-size:16px } }
"""


SHELL_SCRIPT=r"""
(()=>{document.querySelectorAll('.sp-menu').forEach(menu=>{
const trigger=menu.querySelector('summary');
menu.addEventListener('keydown',event=>{if(event.key==='Escape'&&menu.open){event.preventDefault();menu.open=false;trigger.focus();}});
document.addEventListener('click',event=>{if(menu.open&&!menu.contains(event.target))menu.open=false;});
menu.addEventListener('focusout',()=>{setTimeout(()=>{if(!menu.contains(document.activeElement))menu.open=false;},0);});
});})();
"""
HOME_STYLE += '.sp-menu nav { z-index:40 }.sp-menu summary:focus-visible,.sp-menu nav a:focus-visible { outline:3px solid #177fc5;outline-offset:2px }.sp-menu nav a { text-decoration:none;min-height:44px }'

SHELL_SCRIPT += r"""
(()=>{
 const toggle=document.querySelector('.sp-mobile-search-toggle');
 const panel=document.getElementById('product-header-search');
 if(!toggle||!panel)return;
 const input=panel.querySelector('input');
 function closeSearch(){document.body.classList.remove('sp-search-open');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Åpne søk');toggle.focus();}
 toggle.addEventListener('click',event=>{
   event.preventDefault();
   if(document.body.classList.contains('sp-search-open')){closeSearch();return;}
   document.body.classList.add('sp-search-open');toggle.setAttribute('aria-expanded','true');toggle.setAttribute('aria-label','Lukk søk');input.focus();
 });
 panel.addEventListener('keydown',event=>{if(event.key==='Escape'){closeSearch();}});
})();
"""

HOME_STYLE += r"""
/* Homepage discovery follows the compact horizontal rows in reference B002. */
.sp-home-front .sp-catalogue>.sp-product-grid,
.sp-home-front .sp-product-rail { display:grid; grid-auto-flow:column; grid-template-columns:none; grid-auto-columns:calc((100% - 48px)/4); gap:16px; overflow-x:auto; scroll-snap-type:x proximity; padding:4px 4px 12px; margin:0 -4px; scroll-padding:4px }
.sp-home-front .sp-product-grid>li { scroll-snap-align:start }
.sp-home-front .sp-product-card>a { padding:12px }
.sp-home-front .sp-card-image { height:140px; aspect-ratio:auto; flex-shrink:0; margin-bottom:12px }
.sp-home-front .sp-product-card h3 { font-size:14px; padding-bottom:8px; line-height:1.35 }
.sp-home-front .sp-product-category { display:none }
.sp-home-front .sp-product-brand { font-size:11px; margin-bottom:8px }
.sp-home-front .sp-card-price { font-size:21px }
.sp-home-front .sp-card-bottom { margin-top:10px }
.sp-home-front .sp-catalogue-heading a { display:inline-flex; align-items:center; justify-content:flex-end; gap:6px; min-height:44px; flex-shrink:0; font-size:13px; color:var(--sp-green); text-decoration:none }
.sp-home-front .sp-catalogue-heading a:hover { text-decoration:underline }
.sp-home-front .sp-catalogue-heading a svg { width:18px; height:18px }
.sp-home-front .sp-home-categories { margin-top:32px }
@media(max-width:767px) {
 .sp-home-front .sp-catalogue>.sp-product-grid,
 .sp-home-front .sp-product-rail { grid-auto-columns:calc((100% - 10px)/2); gap:10px }
 .sp-home-front .sp-card-image { height:110px; margin-bottom:10px }
 .sp-home-front .sp-product-card>a { padding:10px }
 .sp-home-front .sp-product-card h3 { font-size:13px; padding-bottom:6px }
 .sp-home-front .sp-card-price { font-size:20px }
 .sp-home-front .sp-product-brand { font-size:11px; margin-bottom:6px }
 .sp-home-front .sp-catalogue-heading { gap:10px; margin-bottom:10px }
 .sp-home-front .sp-catalogue-heading h2 { font-size:22px }
 .sp-home-front .sp-home-categories { margin-top:24px }
}
"""


HOME_STYLE += r"""
/* Compact discovery navigation follows the locked homepage proportions. */
.sp-home-categories .sp-catalogue-heading h2 { margin:0 }
.sp-home-categories nav { display:flex; gap:12px; overflow-x:auto; padding:4px 4px 12px; scroll-padding-inline:4px; overscroll-behavior-x:contain }
.sp-home-categories nav a { flex:0 0 auto; max-width:240px; min-height:48px; padding:12px 16px; border-radius:24px; background:var(--sp-mint); border-color:transparent; font-size:14px }
.sp-home-categories nav a span { overflow-wrap:anywhere }
.sp-home-categories nav a:hover { border-color:var(--sp-green) }
.sp-home-categories nav a:focus-visible { outline-offset:0 }
@media(max-width:767px) {
 .sp-home-hero .sp-examples>div { flex-wrap:nowrap; overflow-x:auto; padding:4px 4px 10px; scroll-padding-inline:4px; overscroll-behavior-x:contain }
 .sp-home-hero a.sp-example { flex:0 0 auto; max-width:250px; border-radius:16px }
 .sp-home-hero .sp-example svg { flex-shrink:0 }
 .sp-home-hero .sp-examples { margin-top:12px }
 .sp-home-categories nav { gap:8px }
 .sp-home-categories nav a { max-width:210px; font-size:13px; padding:10px 14px }
 .sp-home-categories .sp-catalogue-heading { align-items:center; gap:8px }
 .sp-home-categories .sp-catalogue-heading h2 { font-size:22px }
}
"""
