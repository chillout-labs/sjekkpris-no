"""Shared search/category presentation. Input is a product view model, not offers."""
from html import escape as e
from home_ui import render_product_card


def render_listing(products, *, base, money, day, segment, title='Søk etter produkter', category=False):
    cards = ''.join(render_product_card(p, base=base, money=money, day=day, segment=segment) for p in products)
    brands = sorted({p.get('local_brand') for p in products if p.get('local_brand')})
    options = ''.join(f'<option value="{e(b, quote=True)}">{e(b)}</option>' for b in brands)
    brand = f'<label>Merke<select id="listing-brand"><option value="">Alle merker</option>{options}</select></label>' if brands else ''
    return f'''<section class="sp-home sp-listing" data-category="{str(category).lower()}">
<nav class="sp-breadcrumb" aria-label="Brødsmulesti"><a href="{e(base)}">Hjem</a><span aria-hidden="true">›</span><span>{e(title)}</span></nav>
<h1>{e(title)}</h1><p class="sp-listing-intro">Sammenlign produkter og finn butikkens laveste varepris. Frakt vises på produktsiden.</p>
<div class="sp-listing-layout">
<details class="sp-listing-filters" open><summary>Filtrer produkter</summary><div>
{brand}<label>Makspris i kroner<input id="listing-max" type="number" min="0" step="1" inputmode="numeric" placeholder="Ingen grense"></label>
<button id="listing-reset" type="button">Nullstill filtre</button></div></details>
<div class="sp-listing-main"><div class="sp-listing-toolbar"><p id="result-status" role="status" aria-live="polite">{len(products)} produkter</p>
<label>Sorter etter<select id="listing-sort"><option value="name">Produktnavn</option><option value="price">Laveste varepris</option></select></label></div>
<div class="sp-home-empty" id="listing-empty" hidden><h2>Ingen produkter funnet</h2><p>Prøv et kortere produktnavn, fjern merkevalget eller øk maksprisen.</p><button type="button" id="listing-show-all">Vis alle produkter</button></div>
<ul class="sp-product-grid" id="search-results">{cards}</ul><noscript>Alle produkter vises. Filtrering og sortering krever JavaScript.</noscript>
</div></div></section><script>{LISTING_SCRIPT}</script>'''


LISTING_SCRIPT = r"""
(()=>{
 const root=document.querySelector('.sp-listing'); if(!root)return;
 const form=document.querySelector('.sp-search'), input=form.querySelector('input');
 const grid=document.getElementById('search-results'), rows=Array.from(grid.children);
 const brand=document.getElementById('listing-brand'), max=document.getElementById('listing-max'), sort=document.getElementById('listing-sort');
 const category=root.dataset.category==='true';
 input.value=category?'':new URLSearchParams(location.search).get('q')||'';
 function filter(){
   const q=category?'':input.value.trim().toLocaleLowerCase('nb');
   const limit=max.value===''?Infinity:Number(max.value)*100; let n=0;
   rows.forEach(row=>{
     const price=row.dataset.price===''?Infinity:Number(row.dataset.price);
     row.hidden=!row.dataset.name.toLocaleLowerCase('nb').includes(q)||(brand&&brand.value&&row.dataset.brand!==brand.value)||(Number.isFinite(limit)&&price>limit);
     if(!row.hidden)n++;
   });
   [...rows].sort((a,b)=>{
     if(sort.value==='price'){
       const x=a.dataset.price===''?Infinity:Number(a.dataset.price), y=b.dataset.price===''?Infinity:Number(b.dataset.price);
       if(x!==y)return x-y;
     }
     return a.dataset.name.localeCompare(b.dataset.name,'nb');
   }).forEach(row=>grid.appendChild(row));
   document.getElementById('result-status').textContent=n+' '+(n===1?'produkt':'produkter')+(q?' for «'+input.value.trim()+'»':'');
   document.getElementById('listing-empty').hidden=n!==0;
 }
 function reset(){if(brand)brand.value='';max.value='';filter();}
 document.getElementById('listing-reset').addEventListener('click',reset);
 document.getElementById('listing-show-all').addEventListener('click',()=>{if(!category)input.value='';reset();});
 [brand,max,sort].filter(Boolean).forEach(el=>el.addEventListener('input',filter));
 if(!category){
   input.addEventListener('input',filter);
   form.addEventListener('submit',e=>{e.preventDefault();const url=new URL(location.href);url.searchParams.set('q',input.value.trim());history.pushState({},'',url);filter();});
   addEventListener('popstate',()=>{input.value=new URLSearchParams(location.search).get('q')||'';filter();});
 }
 if(matchMedia('(max-width:767px)').matches)root.querySelector('details').open=false;
 filter();
})();
"""

LISTING_STYLE = r"""
.sp-listing { padding-bottom:32px }.sp-listing h1 { font-size:36px; letter-spacing:-1px }.sp-listing-intro { color:var(--sp-muted); max-width:680px; margin-top:12px!important }
.sp-listing-layout { display:grid; grid-template-columns:220px minmax(0,1fr); gap:28px; margin-top:28px; align-items:start }.sp-listing-main { min-width:0 }
.sp-listing-filters { border:1px solid var(--sp-line); border-radius:12px; padding:18px; position:sticky; top:20px }.sp-listing-filters summary { cursor:pointer; font-weight:700; min-height:28px }.sp-listing-filters>div { display:grid; gap:20px; margin-top:20px }
.sp-listing label { display:grid; gap:7px; font-size:12px; color:var(--sp-muted) }.sp-listing input,.sp-listing select { min-width:0; width:100%; border:1px solid var(--sp-line); background:white; color:var(--sp-ink); border-radius:8px; min-height:44px; padding:10px; font:14px Arial,sans-serif }
.sp-listing button { border:1px solid var(--sp-line); background:white; color:var(--sp-green); border-radius:8px; padding:10px 14px; min-height:44px; cursor:pointer; font-weight:700 }.sp-listing button:hover { background:var(--sp-mint) }
.sp-listing-toolbar { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:20px }.sp-listing-toolbar>p { font-size:14px }.sp-listing-toolbar label { min-width:160px }
.sp-listing .sp-product-grid { grid-template-columns:repeat(3,minmax(0,1fr)) }.sp-listing .sp-home-empty h2 { font-size:22px; margin-bottom:8px }.sp-listing .sp-home-empty button { margin-top:16px }.sp-listing [hidden] { display:none!important }
@media(max-width:999px) { .sp-listing-layout { grid-template-columns:180px minmax(0,1fr); gap:18px }.sp-listing .sp-product-grid { grid-template-columns:repeat(2,minmax(0,1fr)) } }
@media(max-width:767px) { .sp-listing h1 { font-size:29px }.sp-listing-intro { font-size:14px }.sp-listing-layout { display:block; margin-top:20px }.sp-listing-filters { position:static; padding:14px; margin-bottom:18px }.sp-listing-filters summary { min-height:32px; display:flex; align-items:center }.sp-listing-toolbar { gap:12px }.sp-listing-toolbar label { min-width:145px }.sp-listing-toolbar>p { font-size:12px; overflow-wrap:anywhere } }
"""
