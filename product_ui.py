"""Scoped presentation styles for the approved SjekkPris product prototype.

No data selection, API access, clickout policy, or demo content lives here.
"""

_ICONS = {
    "search": '<circle cx="10" cy="10" r="6.5"/><path d="m15 15 6 6"/>',
    "menu": '<path d="M3 5h18M3 12h18M3 19h18"/>',
    "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "external": '<path d="M14 3h7v7M21 3l-11 11M10 5H4v15h15v-6"/>',
    "image": '<rect x="2" y="3" width="20" height="16" rx="2"/><path d="m3 16 5-5 4 4 4-6 5 7M8 22h8M12 19v3"/>',
    "truck": '<path d="M2 4h12v13H2zM14 9h4l4 5v3h-8"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
    "box": '<path d="m3 6 9-4 9 4v12l-9 4-9-4zM3 6l9 5 9-5M12 11v11"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
    "chart": '<path d="M3 2v19h19M6 15l5-6 4 4 6-8"/>',
    "shield": '<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6zM7 12l3 3 7-7"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',
}


def ui_icon(name: str) -> str:
    return ('<svg class="sp-icon" aria-hidden="true" width="22" height="22" '
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            + _ICONS[name] + '</svg>')


PRICE_MODE_SCRIPT = r"""
(() => {
  const root = document.querySelector('.sp-product');
  const toggle = document.getElementById('include-shipping');
  const control = document.getElementById('shipping-switch-control');
  const rows = document.getElementById('price-rows');
  const status = document.getElementById('price-sort-status');
  if (!root || !toggle || !rows || !control || !status) return;
  function renderMode() {
    const mode = toggle.checked ? 'total' : 'item';
    root.dataset.priceBasis = mode;
    root.querySelectorAll('[data-price-mode]').forEach(el => {
      el.hidden = el.dataset.priceMode !== mode;
    });
    const key = mode + 'Order';
    Array.from(rows.children).sort((a,b) =>
      Number(a.querySelector('[data-item-order]').dataset[key]) -
      Number(b.querySelector('[data-item-order]').dataset[key])
    ).forEach(row => rows.appendChild(row));
    status.textContent = toggle.checked
      ? 'Sortert etter kjent totalpris · ukjent totalpris vises sist.'
      : 'Sortert etter varepris · uten frakt.';
  }
  toggle.checked = false;
  toggle.addEventListener('change', renderMode);
  renderMode();
  control.hidden = false;
})();
"""


PRODUCT_STYLE = r"""
/* Scoped product presentation: older homepage/table rules cannot alter it. */
:root { --sp-ink:#10203b; --sp-muted:#586780; --sp-green:#006454; --sp-mint:#edf8f4; --sp-line:#e2e8ef; --sp-surface:#f5f8fb }
html { scroll-padding-top:24px; color-scheme:light }
body { margin:0; font-family:Arial,Helvetica,sans-serif; background:#fff; color:var(--sp-ink) }
.sp-shell { width:100%; max-width:1280px; padding:0 28px; margin:0 auto; box-sizing:border-box }
.sp-icon { display:inline-block; flex-shrink:0; vertical-align:middle }
.sp-sr { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap }
.sp-skip { position:absolute; top:-100px; left:16px; padding:12px; background:white; z-index:300 }
.sp-skip:focus { top:8px }
header.sp-header { position:relative; padding:0; border-bottom:1px solid var(--sp-line); background:#fff; z-index:10 }
.sp-topbar { display:flex; align-items:center; gap:32px; min-height:90px }
a.sp-brand,a.sp-brand:visited { display:block; flex-shrink:0; font-size:34px; line-height:1; letter-spacing:-1.8px; font-weight:800; color:var(--sp-ink); text-decoration:none; white-space:nowrap }
.sp-brand span { color:var(--sp-green) }
p.sp-tagline { font-size:12px; margin:0; padding-left:20px; border-left:1px solid #c6d1df; white-space:nowrap }
.sp-search { flex:1; min-width:0; max-width:580px; display:flex; align-items:center; gap:10px; margin-left:auto; border:1px solid #ced8e4; background:white; border-radius:26px; padding:0 5px 0 16px; min-height:48px }
.sp-search input { width:100%; min-width:0; flex:1; height:44px; padding:0; border:0; border-radius:0; background:none; color:var(--sp-ink); font:14px Arial,Helvetica,sans-serif }
.sp-search input::placeholder { color:var(--sp-muted) }
.sp-search:focus-within { outline:2px solid #167eaa; outline-offset:2px }
.sp-search input:focus-visible { outline:0 }
.sp-search button { border:0; background:none; color:var(--sp-ink); width:44px; min-width:44px; height:44px; padding:10px; cursor:pointer }
.sp-menu { position:relative; flex-shrink:0; margin-left:auto }
.sp-menu summary { display:flex; align-items:center; justify-content:center; gap:8px; min-height:44px; min-width:44px; cursor:pointer; font-size:13px; list-style:none }
.sp-menu summary::-webkit-details-marker { display:none }
.sp-menu nav { position:absolute; right:0; top:52px; width:225px; padding:8px; background:white; border:1px solid var(--sp-line); border-radius:12px; box-shadow:0 10px 32px #10203b16 }
.sp-menu nav a { display:block; padding:12px; color:var(--sp-ink); font-size:14px; border-radius:7px }
.sp-menu nav a:hover { background:var(--sp-mint) }
.sp-product { font:15px/1.55 Arial,Helvetica,sans-serif; color:var(--sp-ink) }
.sp-product [hidden] { display:none!important }
.sp-price-toolbar { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px }
.sp-shipping-switch { position:relative; display:inline-flex; align-items:center; gap:9px; min-height:44px; cursor:pointer; font-size:13px; color:var(--sp-ink) }
.sp-shipping-switch input { position:absolute; width:1px; height:1px; opacity:0 }
.sp-switch-track { display:block; width:40px; height:24px; border-radius:14px; background:#64748b; padding:3px; box-sizing:border-box }
.sp-switch-track:after { content:''; display:block; width:18px; height:18px; border-radius:50%; background:#fff }
.sp-shipping-switch input:checked+.sp-switch-track { background:var(--sp-green) }
.sp-shipping-switch input:checked+.sp-switch-track:after { transform:translateX(16px) }
.sp-shipping-switch input:focus-visible+.sp-switch-track { outline:3px solid #177fc5; outline-offset:4px }
.sp-product *, .sp-header * { box-sizing:border-box }
.sp-product h1,.sp-product h2,.sp-product h3,.sp-product p,.sp-product dl { margin:0 }
.sp-product h1 { font-size:34px; line-height:1.17; letter-spacing:-1px; font-weight:700; overflow-wrap:anywhere }
.sp-product h2 { font-size:23px; line-height:1.25; letter-spacing:-.4px; font-weight:700 }
.sp-product h3 { font-size:16px; line-height:1.4; font-weight:700 }
.sp-breadcrumb { display:flex; align-items:center; flex-wrap:wrap; gap:10px; padding:25px 0; font-size:12px; color:var(--sp-muted) }
.sp-breadcrumb a { color:var(--sp-muted) }
.sp-hero { display:grid; grid-template-columns:minmax(0,1.05fr) minmax(0,1fr) minmax(0,1fr); gap:28px; align-items:start; margin-bottom:32px }
.sp-identity { grid-column:2; grid-row:1; padding-top:8px; min-width:0 }
.sp-gallery { grid-column:1; grid-row:1; min-width:0 }
.sp-winner { grid-column:3; grid-row:1; min-width:0 }
.sp-image { width:100%; aspect-ratio:1.36; display:flex; align-items:center; justify-content:center; overflow:hidden; border-radius:10px }
.sp-image img { display:block; width:100%; height:100%; object-fit:contain }
.sp-image-empty { aspect-ratio:auto; min-height:160px; padding:24px; background:var(--sp-surface); color:var(--sp-muted); flex-direction:column; gap:13px; font-size:14px }
.sp-image-empty svg { width:40px; height:40px; color:#91a1b5 }
.sp-product .sp-meta { margin-top:19px; font-size:13px; display:flex; flex-direction:column; gap:10px }
.sp-meta div { display:flex; flex-wrap:wrap; gap:7px }
.sp-meta dt { color:var(--sp-muted) }
.sp-meta dd { margin:0; overflow-wrap:anywhere }
.sp-price { padding:23px 20px 16px; border-radius:12px; background:var(--sp-mint) }
.sp-product .sp-price-label { font-size:14px; font-weight:700 }
.sp-product .sp-amount { font-size:42px; line-height:1.2; font-weight:750; letter-spacing:-1.5px; margin:6px 0; font-variant-numeric:tabular-nums }
.sp-product .sp-breakdown { font-size:13px; color:var(--sp-muted); margin:6px 0; overflow-wrap:anywhere }
.sp-product .sp-merchant { font-size:14px; margin:5px 0 17px }
a.sp-cta,a.sp-cta:visited { display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:44px; padding:10px 12px; border:1px solid var(--sp-green); border-radius:8px; color:white; background:var(--sp-green); font-size:12px; line-height:1.3; font-weight:700; text-decoration:none; text-align:center }
a.sp-cta:hover { background:#004d41; text-decoration:none }
.sp-cta svg { width:15px; height:15px }
.sp-hero-cta .sp-cta { width:100%; min-height:49px; font-size:15px }
.sp-facts { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:21px; padding-bottom:14px }
.sp-facts div { display:flex; flex-direction:column; align-items:center; gap:8px; padding:0 5px; text-align:center; font-size:11px; overflow-wrap:anywhere }
.sp-facts div+div { border-left:1px solid #ccdfdc }
.sp-facts svg { color:var(--sp-green); width:24px; height:24px }
.sp-product .sp-confirmed { padding-top:11px; border-top:1px solid #d7e9e2; color:var(--sp-muted); font-size:11px }
.sp-product .sp-price-caveat { font-size:12px; color:var(--sp-muted); margin-top:10px; padding:0 4px }
.sp-no-link { font-size:12px; color:var(--sp-muted) }
.sp-tabs { display:flex; gap:28px; overflow-x:auto; white-space:nowrap; border-bottom:1px solid var(--sp-line); margin-bottom:22px }
.sp-tabs a { display:block; padding:14px 2px; min-height:48px; font-size:13px; color:var(--sp-ink); text-decoration:none }
.sp-tabs a[aria-current="location"] { font-weight:700; border-bottom:3px solid var(--sp-ink) }
.sp-comparison { display:grid; grid-template-columns:minmax(0,2fr) minmax(0,1fr); gap:18px; align-items:start }
.sp-panel { min-width:0; border:1px solid var(--sp-line); border-radius:12px; padding:20px }
.sp-product .sp-subtitle { font-size:12px; margin:7px 0 15px; color:var(--sp-muted) }
.sp-offers { width:100%; border-collapse:collapse; font-size:12px; table-layout:fixed }
.sp-offers th { background:white; font-size:11px; font-weight:400; color:var(--sp-muted); padding:10px 5px; border-bottom:1px solid var(--sp-line) }
.sp-offers td { padding:16px 5px; border-bottom:1px solid var(--sp-line); vertical-align:middle; overflow-wrap:anywhere; font-size:12px }
.sp-offers th:first-child,.sp-offers td:first-child { padding-left:0; width:23% }
.sp-offers th:nth-child(2) { width:14% }.sp-offers th:nth-child(3) { width:13% }.sp-offers th:nth-child(4) { width:16% }.sp-offers th:nth-child(5) { width:13% }.sp-offers th:last-child { width:21% }
.sp-offers td:last-child { padding-right:0 }
.sp-offers tbody tr:hover { background:var(--sp-surface) }
.sp-offers .sp-total { font-variant-numeric:tabular-nums; font-size:14px }
.sp-offers .sp-cta { width:100%; padding:9px 6px; font-size:11px; gap:4px }
.sp-offers .sp-cta svg { width:12px; height:12px }
.sp-note { display:block; font-size:11px; color:var(--sp-muted); margin-top:7px }
.sp-price-note { display:block; font-size:10px; color:var(--sp-green); margin-top:5px }
.sp-mobile-label { display:none }
.sp-product .sp-footnote { font-size:12px; margin-top:16px; padding:12px; background:var(--sp-surface); border-radius:8px; color:var(--sp-muted) }
.sp-history-empty { display:flex; align-items:center; justify-content:center; flex-direction:column; text-align:center; gap:10px; padding:20px 8px 4px; color:var(--sp-muted) }
.sp-history-empty>svg { width:44px; height:44px; background:var(--sp-surface); padding:10px; border-radius:10px; color:var(--sp-ink) }
.sp-history-empty h3 { color:var(--sp-ink) }.sp-history-empty p { font-size:13px; max-width:250px }
.sp-details { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin-top:18px }
.sp-product .sp-empty { color:var(--sp-muted); font-size:14px; padding:12px 0 0 }
.sp-product .sp-specs { margin-top:16px; font-size:13px }
.sp-specs div { display:grid; grid-template-columns:1fr 1fr; gap:14px; padding:10px 0; border-bottom:1px solid var(--sp-line) }
.sp-specs dt { color:var(--sp-muted) }.sp-specs dd { margin:0; overflow-wrap:anywhere }
.sp-product .sp-excluded-title { margin:24px 0 12px }
.sp-trust { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; background:var(--sp-mint); border-radius:12px; margin:20px 0; padding:24px }
.sp-trust>div { display:flex; gap:12px; align-items:flex-start; min-width:0 }
.sp-trust svg { color:var(--sp-green); width:27px; height:27px }.sp-trust strong { display:block; font-size:12px }.sp-trust span { display:block; font-size:11px; color:var(--sp-muted); margin-top:4px }
footer.sp-footer { margin-top:32px; padding:24px 0; background:var(--sp-surface); color:var(--sp-muted); font-size:12px; border-top:1px solid var(--sp-line) }
.sp-footer p { margin:5px 0 }.sp-footer strong { color:var(--sp-ink); font-size:18px }
.sp-product :focus-visible,.sp-header :focus-visible { outline:3px solid #177fc5; outline-offset:3px }
@media(max-width:1150px) { .sp-tagline { display:none } .sp-topbar { gap:24px } }
@media(min-width:768px) and (max-width:999px) { .sp-hero { grid-template-columns:minmax(0,1fr) minmax(0,1fr) }.sp-identity { grid-column:1/-1;grid-row:1 }.sp-gallery { grid-column:1;grid-row:2 }.sp-winner { grid-column:2;grid-row:2 }.sp-comparison { grid-template-columns:1fr } }
@media(max-width:767px) {
.sp-shell { padding:0 16px }.sp-topbar { min-height:0; padding-top:18px; padding-bottom:16px; flex-wrap:wrap; gap:14px }.sp-brand { order:0 } a.sp-brand { font-size:30px }.sp-tagline { display:none }.sp-menu { order:1; margin-left:auto }.sp-menu summary span { display:none }.sp-search { order:2; flex:0 0 100%; max-width:none; width:100%; margin:0 }.sp-search input { font-size:14px }
.sp-breadcrumb { font-size:11px; padding:19px 0 }.sp-hero { display:flex; flex-direction:column; gap:18px; margin-bottom:22px }.sp-identity { order:0; width:100%; padding:0 }.sp-gallery { order:1; width:100% }.sp-winner { order:2; width:100% }.sp-product h1 { font-size:29px; letter-spacing:-.8px; line-height:1.2 }.sp-product .sp-meta { margin-top:10px; font-size:12px; gap:5px }.sp-image { aspect-ratio:1.55 }.sp-image-empty { aspect-ratio:auto; min-height:72px; padding:16px; flex-direction:row; gap:10px; font-size:13px }.sp-image-empty svg { width:24px; height:24px }.sp-price { padding:19px 16px 15px }.sp-product .sp-amount { font-size:38px }.sp-product .sp-breakdown { font-size:12px }.sp-facts { margin-top:18px }.sp-product .sp-price-caveat { font-size:11px }
.sp-tabs { gap:23px; margin-bottom:18px }.sp-tabs a { font-size:12px; padding:12px 2px }.sp-comparison { display:flex; flex-direction:column; gap:18px; align-items:stretch }.sp-panel { padding:17px }.sp-offer-panel { padding:0; border:0 }.sp-product h2 { font-size:22px }.sp-product .sp-subtitle { margin-bottom:12px }
.sp-offers,.sp-offers tbody { display:block; width:100% }.sp-offers thead { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%) }.sp-offers thead tr { position:static }.sp-offers tbody tr { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:8px 12px; padding:14px; margin:0 0 12px; border:1px solid var(--sp-line); border-radius:9px; background:white }.sp-offers td { display:block; width:auto; padding:0; margin:0; border:0; text-align:left; position:static; font-size:12px; min-width:0 }.sp-offers td:before { display:none }.sp-offers td:first-child { grid-column:1;grid-row:1; width:auto; padding:0; border:0; font-size:13px }.sp-offers .sp-total { grid-column:2;grid-row:1; padding:0; border:0; text-align:right; font-size:16px }.sp-offers .sp-total .sp-mobile-label { display:block; font-weight:400; font-size:10px; color:var(--sp-muted) }.sp-offers .sp-item { grid-column:1;grid-row:2; display:block; border:0; padding:0; color:var(--sp-muted); font-size:11px }.sp-offers .sp-shipping { grid-column:2;grid-row:2; display:block; padding:0; border:0; color:var(--sp-muted); font-size:11px; text-align:right }.sp-offers .sp-stock { grid-column:1;grid-row:3; align-self:center; padding:0; border:0; font-size:11px; color:var(--sp-muted) }.sp-offers .sp-action { grid-column:2;grid-row:3; padding:0; text-align:right; border:0 }.sp-offers .sp-cta { font-size:11px; gap:4px; padding:9px 6px; min-height:44px }.sp-mobile-label { display:inline }.sp-note { font-size:10px }.sp-price-note { font-size:10px }.sp-history-empty { display:grid; grid-template-columns:36px minmax(0,1fr); gap:4px 12px; text-align:left; padding:14px 0 0 }.sp-history-empty>svg { grid-row:1/3; width:36px; height:36px; padding:8px }.sp-history-empty p { max-width:none }.sp-history-empty h3 { font-size:14px }.sp-details { grid-template-columns:1fr; gap:18px }.sp-trust { display:flex; flex-direction:column; padding:20px; gap:20px }.sp-trust strong { font-size:13px }.sp-trust span { font-size:12px }
}
/* Match the prototype's five visual columns. Keep stock as a separate
   semantic table cell, positioned under the merchant, not as column six. */
@media(min-width:768px) {
 .sp-offers,.sp-offers thead,.sp-offers tbody { display:block; width:100% }
 .sp-offers tr { display:grid; grid-template-columns:1.3fr .85fr .6fr 1fr 1.2fr; gap:7px 10px; align-items:center; padding:15px 0; border-bottom:1px solid var(--sp-line) }
 .sp-offers thead tr { padding:9px 0 }
 .sp-offers th,.sp-offers td,.sp-offers th:first-child,.sp-offers td:first-child { width:auto; min-width:0; padding:0; border:0; text-align:left }
 .sp-offers th:nth-child(2),.sp-offers th:nth-child(3),.sp-offers th:nth-child(4),.sp-offers th:last-child { width:auto }
 .sp-offers th:nth-child(5) { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%) }
 .sp-offers td:first-child { grid-column:1; grid-row:1 }
 .sp-offers .sp-item { grid-column:2; grid-row:1 / span 2 }
 .sp-offers .sp-shipping { grid-column:3; grid-row:1 / span 2 }
 .sp-offers .sp-total { grid-column:4; grid-row:1 / span 2 }
 .sp-offers .sp-stock { grid-column:1; grid-row:2; font-size:11px; color:var(--sp-muted) }
 .sp-offers .sp-action { grid-column:5; grid-row:1 / span 2 }
 .sp-offers .sp-cta { padding:8px; gap:5px; white-space:nowrap }
}
@media(prefers-reduced-motion:reduce) { html { scroll-behavior:auto } }
@media(min-width:768px) {
 .sp-product[data-price-basis="item"] .sp-switchable-offers tr { grid-template-columns:1.3fr .6fr 1fr 1.2fr }
 .sp-product[data-price-basis="item"] .sp-switchable-offers th:nth-child(2),
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-item { display:none }
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-shipping { grid-column:2 }
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-total { grid-column:3 }
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-action { grid-column:4 }
}
/* Compact item-price cards: the main price is already displayed at the top. */
@media(max-width:767px) {
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-item { display:none }
 .sp-product[data-price-basis="item"] .sp-switchable-offers .sp-shipping { grid-column:1 / -1; text-align:left }
}
.sp-product #specifications details { margin-top:12px; font-size:13px; color:var(--sp-muted) }
.sp-product #specifications summary { min-height:44px; display:flex; align-items:center; cursor:pointer; color:var(--sp-green) }
.sp-product #specifications summary::before { content:'›'; margin-right:8px; font-size:20px }
.sp-product #specifications details[open] summary::before { transform:rotate(90deg) }
.sp-home .sp-product-category, .sp-home .sp-product-brand { font-size:12px; color:var(--sp-muted); margin:0 0 8px }

.sp-category-nav { border-top:1px solid var(--sp-line); background:#fff }
.sp-category-nav>.sp-shell { display:flex; gap:26px; align-items:center; overflow-x:auto }
.sp-category-nav a { display:flex; align-items:center; min-height:46px; white-space:nowrap; font-size:13px; color:var(--sp-ink); text-decoration:none }
.sp-category-nav a:hover { color:var(--sp-green) }.sp-category-nav .sp-all-categories { font-weight:700; padding-right:24px; border-right:1px solid var(--sp-line) }
@media(max-width:767px) { .sp-category-nav>.sp-shell { gap:18px }.sp-category-nav a { font-size:12px; min-height:44px }.sp-category-nav .sp-all-categories { padding-right:18px } }
"""

from rich_ui import RICH_STYLE
PRODUCT_STYLE += RICH_STYLE

PRODUCT_STYLE += r"""
/* Product mobile header: compact default, existing search revealed on demand. */
.sp-mobile-search-toggle { display:none }
@media(max-width:767px) {
 .sp-product-page .sp-topbar { padding-top:8px; padding-bottom:8px; gap:8px }
 .sp-product-page .sp-mobile-search-toggle { display:flex; align-items:center; justify-content:center; width:44px; height:44px; margin-left:auto; order:1; color:var(--sp-ink); border-radius:8px }
 .sp-product-page .sp-menu { order:2; margin-left:0 }
 .sp-product-page .sp-header-search-wrap { display:none; order:3 }
 .sp-product-page.sp-search-open .sp-header-search-wrap { display:block }
 .sp-product-page .sp-category-nav { display:none }
 .sp-product-page .sp-breadcrumb { padding:4px 0; min-height:44px; font-size:12px }
 .sp-product-page .sp-breadcrumb>* { display:none }
 .sp-product-page .sp-breadcrumb .sp-current-category,
 .sp-product-page .sp-breadcrumb:not(:has(.sp-current-category))>a:first-child { display:inline-flex; align-items:center; gap:8px; min-height:44px; color:var(--sp-muted); text-decoration:none }
 .sp-product-page .sp-breadcrumb .sp-current-category::before,
 .sp-product-page .sp-breadcrumb:not(:has(.sp-current-category))>a:first-child::before { content:'←'; font-size:20px; flex-shrink:0 }
 .sp-product-page .sp-meta [data-product-meta="category"] { display:none }
}
"""
