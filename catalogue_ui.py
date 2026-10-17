"""Shared search/category presentation. Input is a product view model, not offers."""
from html import escape as e
from home_ui import render_product_card


def render_listing(products, *, base, money, day, segment, title='Søk etter produkter', category=False, breadcrumbs=(), children=()):
    trail = ''.join(f'<a href="{e(url)}">{e(label)}</a><span aria-hidden="true">›</span>' for label,url in breadcrumbs)
    chips = ''.join(f'<a href="{e(url)}">{e(label)}<span>{count}</span></a>' for label,url,count in children)
    subcategories = f'<nav class="sp-category-chips" aria-label="Underkategorier">{chips}</nav>' if chips else ''
    cards = ''.join(render_product_card(p, base=base, money=money, day=day, segment=segment) for p in products)
    brands = sorted({p.get('local_brand') for p in products if p.get('local_brand')})
    options = ''.join(f'<option value="{e(b, quote=True)}">{e(b)}</option>' for b in brands)
    brand = f'<label>Merke<select id="listing-brand"><option value="">Alle merker</option>{options}</select></label>' if brands else ''
    return f'''<section class="sp-home sp-listing" data-category="{str(category).lower()}">
<nav class="sp-breadcrumb" aria-label="Brødsmulesti"><a href="{e(base)}">Hjem</a><span aria-hidden="true">›</span>{trail}<span aria-current="page">{e(title)}</span></nav>
<h1>{e(title)}</h1><p class="sp-listing-intro">Sammenlign produkter og butikkenes varepriser. Frakt vises på produktsiden.</p>
{subcategories}<div class="sp-listing-layout">
<div id="filter-desktop-slot">
<details class="sp-listing-filters" open><summary>Filtrer produkter</summary><div>
<div class="sp-price-range"><label>Min. pris (kr)<input id="listing-min" aria-describedby="listing-price-help" type="number" min="0" step="1" inputmode="numeric" placeholder="Valgfri"></label><label>Maks. pris (kr)<input id="listing-max" aria-describedby="listing-price-help" type="number" min="0" step="1" inputmode="numeric" placeholder="Valgfri"></label></div><p id="listing-price-help" class="sp-filter-help" role="status" hidden></p>{brand}
<button id="listing-reset" type="button">Nullstill filtre</button></div></details></div>
<div class="sp-listing-main"><div class="sp-listing-toolbar"><button id="filter-open" class="sp-filter-open" type="button" aria-haspopup="dialog" aria-controls="filter-dialog" hidden>Filter <span id="filter-count"></span></button><p id="result-status" role="status" aria-live="polite">{len(products)} produkter</p>
<label>Sorter etter<select id="listing-sort"><option value="name">Produktnavn</option><option value="price" {"selected" if category else ""}>Laveste varepris</option><option value="price-desc">Høyeste varepris</option></select></label></div>
<div id="active-filters" class="sp-active-filters" aria-label="Valgte filtre"></div>
<div class="sp-home-empty" id="listing-empty" hidden><h2>Ingen produkter funnet</h2><p id="listing-empty-help">Prøv et annet søk eller fjern et filter.</p><div class="sp-empty-actions"><button type="button" id="listing-clear-filters" hidden>Fjern filtrene</button><button type="button" id="listing-show-all">Vis alle produkter</button><a href="{e(base)}kategori/">Utforsk kategorier</a></div></div>
<ul class="sp-product-grid" id="search-results">{cards}</ul><noscript>Alle produkter vises. Filtrering og sortering krever JavaScript.</noscript>
</div></div>
<dialog id="filter-dialog" aria-labelledby="filter-heading"><div class="sp-filter-heading"><h2 id="filter-heading">Filtre</h2><button id="filter-close" type="button" aria-label="Lukk filtre">✕</button></div><div class="sp-active-filters" id="mobile-active-filters" aria-label="Valgte filtre"></div><div id="filter-mobile-slot"></div><button id="filter-apply" type="button">Vis produkter</button></dialog>
</section><script>{LISTING_SCRIPT}</script>'''


LISTING_SCRIPT = r"""
(()=>{
 const root=document.querySelector('.sp-listing'); if(!root)return;
 const form=document.querySelector('.sp-search'), input=form.querySelector('input');
 const grid=document.getElementById('search-results'), rows=Array.from(grid.children);
 const brand=document.getElementById('listing-brand'), max=document.getElementById('listing-max'), min=document.getElementById('listing-min'), sort=document.getElementById('listing-sort');
 const category=root.dataset.category==='true';
 input.value=category?'':new URLSearchParams(location.search).get('q')||'';
 function filter(){
   const q=category?'':input.value.trim().toLocaleLowerCase('nb');
   const minimum=min.value===''?0:Number(min.value)*100;
   const limit=max.value===''?Infinity:Number(max.value)*100; let n=0;
   const invalid=minimum>limit;
   const priceHelp=document.getElementById('listing-price-help');
   priceHelp.hidden=!invalid;priceHelp.textContent=invalid?'Minsteprisen er høyere enn maksprisen. Juster ett av beløpene.':'';
   [min,max].forEach(el=>el.setAttribute('aria-invalid',String(invalid)));
   rows.forEach(row=>{
     const price=row.dataset.price===''?Infinity:Number(row.dataset.price);
     row.hidden=!row.dataset.name.toLocaleLowerCase('nb').includes(q)||(brand&&brand.value&&row.dataset.brand!==brand.value)||(Number.isFinite(limit)&&price>limit)||price<minimum||(minimum>0&&!Number.isFinite(price));
     if(!row.hidden)n++;
   });
   [...rows].sort((a,b)=>{
     if(sort.value==='price'||sort.value==='price-desc'){
       const x=a.dataset.price===''?Infinity:Number(a.dataset.price), y=b.dataset.price===''?Infinity:Number(b.dataset.price);
       if(x===Infinity||y===Infinity)return x===y?0:x===Infinity?1:-1;
       if(x!==y)return sort.value==='price-desc'?y-x:x-y;
     }
     return a.dataset.name.localeCompare(b.dataset.name,'nb');
   }).forEach(row=>grid.appendChild(row));
   document.getElementById('result-status').textContent=n+' '+(n===1?'produkt':'produkter')+(q?' for «'+input.value.trim()+'»':'');
   document.getElementById('listing-empty').hidden=n!==0;
   document.getElementById('filter-apply').textContent='Vis '+n+' '+(n===1?'produkt':'produkter');
   const activeAreas=[document.getElementById('active-filters'),document.getElementById('mobile-active-filters')];
   activeAreas.forEach(area=>area.replaceChildren());
   const selected=[[brand,brand?.value],[min,min.value?'Fra '+min.value+' kr':''],[max,max.value?'Til '+max.value+' kr':'']].filter(([el,label])=>label);
   document.getElementById('filter-count').textContent=selected.length||'';
   activeAreas.forEach(active=>selected.forEach(([el,label])=>{const b=document.createElement('button');b.type='button';b.textContent=label+' ×';b.setAttribute('aria-label','Fjern filter: '+label);b.addEventListener('click',()=>{el.value='';filter();if(dialog.open)el.focus();else document.getElementById('listing-sort').focus();});active.appendChild(b);}));
   const queryMatches=rows.filter(row=>row.dataset.name.toLocaleLowerCase('nb').includes(q)).length;
   const clearFilters=document.getElementById('listing-clear-filters');
   clearFilters.hidden=!(queryMatches&&selected.length);
   clearFilters.textContent='Fjern filtrene – vis '+queryMatches+' '+(queryMatches===1?'produkt':'produkter');
   document.getElementById('listing-empty-help').textContent=invalid ? 'Prisintervallet er snudd. Juster beløpene i filtrene, eller fjern filtrene for å se treffene.' : queryMatches && selected.length
     ? queryMatches+' '+(queryMatches===1?'produkt er':'produkter er')+' tilgjengelig uten filtrene. Fjern et valgt filter eller nullstill alle.'
     : q ? 'Ingen treff for «'+input.value.trim()+'». Prøv et kortere navn, eller se alle produktene.'
     : 'Ingen produkter tilgjengelig her akkurat nå. Utforsk en annen kategori fra menyen.';
 }
 function reset(){if(brand)brand.value='';max.value='';min.value='';filter();}
 document.getElementById('listing-reset').addEventListener('click',reset);
 document.getElementById('listing-clear-filters').addEventListener('click',()=>{reset();document.getElementById('listing-sort').focus();});
 document.getElementById('listing-show-all').addEventListener('click',()=>{if(!category)input.value='';reset();});
 [brand,min,max,sort].filter(Boolean).forEach(el=>el.addEventListener('input',filter));
 if(!category){
   input.addEventListener('input',filter);
   form.addEventListener('submit',e=>{e.preventDefault();const url=new URL(location.href);url.searchParams.set('q',input.value.trim());history.pushState({},'',url);filter();});
   addEventListener('popstate',()=>{input.value=new URLSearchParams(location.search).get('q')||'';filter();});
 }
 const mq=matchMedia('(max-width:767px)'), dialog=document.getElementById('filter-dialog');
 const panel=root.querySelector('.sp-listing-filters'), opener=document.getElementById('filter-open');
 function placeFilters(){
   if(dialog.open)dialog.close();
   document.getElementById(mq.matches?'filter-mobile-slot':'filter-desktop-slot').appendChild(panel);
   panel.open=true;opener.hidden=!mq.matches;
 }
 opener.addEventListener('click',()=>dialog.showModal());
 document.getElementById('filter-close').addEventListener('click',()=>dialog.close());
 document.getElementById('filter-apply').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{
   // The mobile trigger disappears when the layout changes to desktop.
   // Keep keyboard focus on a visible control in the same filter group.
   (mq.matches?opener:panel.querySelector('summary')).focus();
 });
 mq.addEventListener('change',placeFilters);placeFilters();
 filter();
})();
"""

LISTING_STYLE = r"""
.sp-listing { padding-bottom:32px }.sp-listing h1 { font-size:36px; letter-spacing:-1px }.sp-listing-intro { color:var(--sp-muted); max-width:680px; margin-top:12px!important }
.sp-listing-layout { display:grid; grid-template-columns:220px minmax(0,1fr); gap:28px; margin-top:28px; align-items:start }.sp-listing-main { min-width:0 }
.sp-listing-filters { border:1px solid var(--sp-line); border-radius:12px; padding:18px; position:sticky; top:20px }.sp-listing-filters summary { cursor:pointer; font-weight:700; min-height:44px; display:flex; align-items:center }.sp-listing-filters>div { display:grid; gap:20px; margin-top:20px }
.sp-listing label { display:grid; gap:7px; font-size:12px; color:var(--sp-muted) }.sp-listing input,.sp-listing select { min-width:0; width:100%; border:1px solid var(--sp-line); background:white; color:var(--sp-ink); border-radius:8px; min-height:44px; padding:10px; font:14px Arial,sans-serif }
.sp-listing button { border:1px solid var(--sp-line); background:white; color:var(--sp-green); border-radius:8px; padding:10px 14px; min-height:44px; cursor:pointer; font-weight:700 }.sp-listing button:hover { background:var(--sp-mint) }
.sp-listing-toolbar { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:20px }.sp-listing-toolbar>p { font-size:14px }.sp-listing-toolbar label { min-width:160px }
.sp-listing .sp-product-grid { grid-template-columns:repeat(3,minmax(0,1fr)) }.sp-listing .sp-home-empty h2 { font-size:22px; margin-bottom:8px }.sp-listing .sp-home-empty button { margin-top:16px }.sp-listing [hidden] { display:none!important }
@media(max-width:999px) { .sp-listing-layout { grid-template-columns:180px minmax(0,1fr); gap:18px }.sp-listing .sp-product-grid { grid-template-columns:repeat(2,minmax(0,1fr)) } }
@media(max-width:767px) { .sp-listing h1 { font-size:29px }.sp-listing-intro { font-size:14px }.sp-listing-layout { display:block; margin-top:20px }.sp-listing-filters { position:static; padding:14px; margin-bottom:18px }.sp-listing-filters summary { min-height:32px; display:flex; align-items:center }.sp-listing-toolbar { gap:12px }.sp-listing-toolbar label { min-width:145px }.sp-listing-toolbar>p { font-size:12px; overflow-wrap:anywhere } }

.sp-category-chips { display:flex; flex-wrap:wrap; gap:9px; margin:22px 0 0 }
.sp-category-chips a { display:flex; align-items:center; gap:10px; min-height:44px; padding:9px 13px; border:1px solid var(--sp-line); border-radius:8px; color:var(--sp-ink); font-size:13px; text-decoration:none }
.sp-category-chips a:hover { background:var(--sp-mint) }.sp-category-chips span { color:var(--sp-muted); font-size:11px }
.sp-listing .sp-active-filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px }.sp-listing .sp-active-filters:empty { display:none }
.sp-listing .sp-active-filters button { background:var(--sp-mint); font-size:12px }
.sp-price-range { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px }
@media(min-width:768px) { .sp-listing .sp-card-image { height:210px; aspect-ratio:auto; flex-shrink:0 }.sp-listing .sp-card-image img { max-height:100% } }
#filter-desktop-slot { position:sticky; top:20px }
.sp-listing #filter-dialog { max-width:none; max-height:none; width:100%; height:100dvh; margin:0; padding:20px; padding-bottom:max(20px,env(safe-area-inset-bottom)); border:0; color:var(--sp-ink); background:white }
#filter-dialog[open] { display:flex; flex-direction:column }
#filter-dialog::backdrop { background:#10203b66 }
.sp-filter-heading { display:flex; flex-shrink:0; align-items:center; justify-content:space-between; gap:16px; padding-bottom:14px; border-bottom:1px solid var(--sp-line) }
.sp-filter-heading h2 { font-size:22px }.sp-filter-heading button { border:0 }
#mobile-active-filters { margin-top:16px; flex-shrink:0 }
#filter-mobile-slot { overflow-y:auto; overscroll-behavior:contain; min-height:0; flex:1; padding:8px 4px 20px }
#filter-mobile-slot .sp-listing-filters { border:0; padding:0; margin:0 }
#filter-mobile-slot summary { display:none }
.sp-listing #filter-apply { flex-shrink:0; width:100%; background:var(--sp-green); color:white; font-size:16px; min-height:50px }
body:has(#filter-dialog[open]) { overflow:hidden }
.sp-category-index { padding-bottom:40px }.sp-category-index>p { color:var(--sp-muted); margin-top:12px }
.sp-category-tree { list-style:none; padding:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; margin-top:28px }
.sp-category-tree>li { border:1px solid var(--sp-line); border-radius:12px; padding:18px }
.sp-category-tree ul { list-style:none; padding-left:15px; border-left:1px solid var(--sp-line) }
.sp-category-tree a { display:flex; align-items:center; justify-content:space-between; gap:12px; min-height:44px; color:var(--sp-ink); font-size:14px; text-decoration:none; padding:8px 0 }
.sp-category-tree a:hover { color:var(--sp-green) }.sp-category-tree small { white-space:nowrap; font-size:11px; color:var(--sp-muted) }
@media(max-width:767px) {
 .sp-category-tree { grid-template-columns:1fr }.sp-category-tree ul { padding-left:10px }
 #filter-desktop-slot { position:static }
 .sp-listing-toolbar { flex-wrap:wrap; display:grid; grid-template-columns:auto minmax(0,1fr) }
 .sp-listing-toolbar>p { grid-row:2; grid-column:1/-1 }.sp-listing-toolbar label { min-width:0 }
 .sp-filter-open { align-self:end }.sp-listing-toolbar label select { padding-right:24px }
 .sp-listing .sp-product-grid { grid-template-columns:1fr }
 .sp-listing .sp-product-card>a { display:grid; grid-template-columns:108px minmax(0,1fr); gap:4px 14px; padding:14px }
 .sp-listing .sp-card-image { grid-column:1; grid-row:1/8; align-self:center; aspect-ratio:1; height:108px; margin:0; padding:0 }
 .sp-listing .sp-product-card h3 { grid-column:2; padding:0 0 4px; margin:0; font-size:15px }
 .sp-listing .sp-product-card p,.sp-listing .sp-card-bottom { grid-column:2; margin:0 }
 .sp-listing .sp-product-category { display:none }
 .sp-listing .sp-card-confirmed { display:none }
 .sp-listing .sp-card-price { font-size:20px }
 .sp-listing .sp-card-bottom { margin-top:6px; font-size:12px }
}
"""

LISTING_STYLE += r"""
.sp-listing .sp-filter-help { font-size:13px;line-height:1.5;color:#8c321d;background:#fff4ee;border-left:3px solid #b14b2d;padding:12px;border-radius:4px;margin:0 }
.sp-listing input[aria-invalid=true] { border-color:#b14b2d }.sp-empty-actions { display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:20px }.sp-listing .sp-empty-actions button { margin-top:0 }.sp-empty-actions a { min-height:44px;display:inline-flex;align-items:center;color:var(--sp-green);font-size:14px }.sp-listing #listing-clear-filters { background:var(--sp-green);color:white }.sp-listing #listing-clear-filters:hover { background:#004c40 }
@media(max-width:767px) { .sp-listing .sp-home-empty { padding:22px 18px }.sp-empty-actions { align-items:stretch;flex-direction:column }.sp-empty-actions button { width:100% }.sp-empty-actions a { justify-content:center }.sp-listing input,.sp-listing select { font-size:16px } }
"""
