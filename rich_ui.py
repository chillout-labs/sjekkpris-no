"""Optional presentation components. Callers supply validated display data.

No API fields or publication decisions are inferred here. The complete-state
fixtures live exclusively in tools/preview_design.py until a data adapter exists.
"""
from html import escape as e
import json
from catalogue_media import image_markup


def attributes(items):
    return '<dl class="sp-key-attributes">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in items)+'</dl>' if items else ''


def variants(items):
    if not items:return ''
    return '<nav class="sp-variants" aria-label="Velg variant"><strong>Velg variant</strong><div>'+''.join(f'<a href="{e(url,quote=True)}"'+(' aria-current="page"' if selected else '')+f'>{e(label)}</a>' for label,url,selected in items)+'</div></nav>'


def gallery(images):
    valid=[(image,label,image_markup(image,label,sizes='(max-width:999px) 90vw, 360px',eager=True)) for image,label in images]
    valid=[x for x in valid if x[2]]
    if not valid:return ''
    slides=''.join(f'<div class="sp-image" data-gallery-slide {"hidden" if i else ""}>{markup}</div>' for i,(_,_,markup) in enumerate(valid))
    controls=''.join(f'<button type="button" data-gallery-index="{i}" aria-label="Vis bilde {i+1}: {e(label,quote=True)}" aria-pressed="{str(i==0).lower()}">{markup}</button>' for i,(_,label,markup) in enumerate(valid))
    return f'<div class="sp-gallery-view">{slides}<div class="sp-thumbnails">{controls}</div><p class="sp-sr" role="status" data-gallery-status>Bilde 1 av {len(valid)}</p></div>'


def knowledge(data):
    sections=[]
    if data.get('use_cases'):
        sections.append('<section class="sp-panel"><h2>Passer spesielt godt til</h2><div class="sp-use-cases">'+''.join(f'<article><h3>{e(title)}</h3><p>{e(text)}</p></article>' for title,text in data['use_cases'])+'</div></section>')
    for key,title in [('alternatives','Hva får jeg for pengene?'),('accessories','Passer til dette produktet')]:
        if data.get(key):
            sections.append(f'<section class="sp-panel" id="{key}"><h2>{title}</h2><div class="sp-value-grid">'+''.join(f'<article><h3>{e(label)}</h3><p>{e(text)}</p><a href="{e(url,quote=True)}">{e(link)} <span aria-hidden="true">→</span></a></article>' for label,text,link,url in data[key])+'</div></section>')
    if data.get('faq'):
        sections.append('<section class="sp-panel sp-faq"><h2>Vanlige spørsmål</h2>'+''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in data['faq'])+'</section>')
    return '<div class="sp-rich-content">'+''.join(sections)+'</div>' if sections else ''


def history(points):
    if len(points)<2:return ''
    values=[v for _,v in points]; low=min(values);high=max(values);span=max(high-low,1)
    coords=[(20+i*280/(len(points)-1),130-(v-low)*100/span) for i,(_,v) in enumerate(points)]
    line=' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)
    dots=''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{e(date)}: {format(v, ',').replace(',', ' ')} kr</title></circle>' for (x,y),(date,v) in zip(coords,points))
    table=''.join(f'<tr><th scope="row">{e(date)}</th><td>{format(v, ',').replace(',', ' ')} kr</td></tr>' for date,v in points)
    return _history_html(low,line,dots,points,table)


def _history_html(low,line,dots,points,table):
    observations=e(json.dumps([[date,format(value, ',').replace(',', ' ')+' kr'] for date,value in points]),quote=True)
    latest=format(points[-1][1], ',').replace(',', ' ')
    high=format(max(value for _,value in points), ',').replace(',', ' ')
    return f'''<div class="sp-history-chart" data-observations="{observations}">
<div class="sp-history-summary"><div><p>Siste observasjon</p><strong>{latest} kr</strong></div><div><p>Lavest i perioden</p><strong>{format(low, ',').replace(',', ' ')} kr</strong></div></div>
<p class="sp-history-basis">Varepris uten frakt · {len(points)} observasjoner</p>
<div class="sp-chart-scale"><span>Høyest: {high} kr</span><span>Lavest: {format(low, ',').replace(',', ' ')} kr</span></div>
<svg viewBox="0 0 320 155" role="img" aria-label="Prisutvikling. Velg observasjon nedenfor eller åpne pristabellen."><polyline points="{line}"/>{dots}</svg>
<div class="sp-chart-dates"><span>{e(points[0][0])}</span><span>{e(points[-1][0])}</span></div>
<div class="sp-history-control" hidden><label>Utforsk prisene<input type="range" min="0" max="{len(points)-1}" value="{len(points)-1}" step="1" aria-label="Velg prisobservasjon"></label><output aria-live="polite">{e(points[-1][0])}: {latest} kr</output></div>
<details><summary>Se alle prisobservasjoner</summary><table><caption class="sp-sr">Varepris uten frakt per dato</caption>{table}</table></details></div>'''


def product_parts(data):
    return {'summary':f'<p class="sp-product-summary">{e(data.get("summary",""))}</p>' if data.get('summary') else '',
            'attributes':attributes(data.get('attributes',[])), 'variants':variants(data.get('variants',[])),
            'gallery':gallery(data.get('gallery',[])), 'history':history(data.get('history',[])),
            'about':f'<p>{e(data["about"])}</p>' if data.get('about') else '',
            'specs': '<dl class="sp-specs">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in data['specs'])+'</dl>' if data.get('specs') else '',
            'extra':knowledge(data)}


def product_rail(title,cards,href):
    return f'<section class="sp-discovery"><div class="sp-catalogue-heading"><h2>{e(title)}</h2><a href="{e(href,quote=True)}">Se alle</a></div><ul class="sp-product-grid sp-product-rail">'+''.join(cards)+'</ul></section>'


RICH_SCRIPT=r"""
(()=>{document.querySelectorAll('.sp-gallery-view').forEach(root=>{
 const buttons=Array.from(root.querySelectorAll('[data-gallery-index]')),slides=Array.from(root.querySelectorAll('[data-gallery-slide]'));
 buttons.forEach((button,index)=>{button.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%buttons.length;else if(event.key==='ArrowLeft')next=(index+buttons.length-1)%buttons.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=buttons.length-1;else return;event.preventDefault();buttons[next].focus();buttons[next].click();});button.addEventListener('click',()=>{slides.forEach((s,i)=>s.hidden=i!==index);buttons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));root.querySelector('[data-gallery-status]').textContent='Bilde '+(index+1)+' av '+slides.length;});});
});})();
"""
RICH_STYLE=r"""
.sp-image[hidden] { display:none }
.sp-product-heading { grid-column:2;grid-row:1;min-width:0 }
.sp-product-options:empty { display:none }
@media(min-width:768px) and (max-width:999px) { .sp-product-heading { grid-column:1/-1;grid-row:1 } }
@media(max-width:767px) { .sp-product-heading { display:contents }.sp-product-options { order:2 }.sp-hero .sp-winner { order:3 } }
.sp-product-summary { margin-top:16px!important; line-height:1.6 }
.sp-key-attributes { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-top:20px!important }
.sp-key-attributes>div { padding:10px 8px; border:1px solid var(--sp-line); border-radius:8px; text-align:center }
.sp-key-attributes dt { color:var(--sp-muted); font-size:11px }.sp-key-attributes dd { margin:4px 0 0; font-size:14px; font-weight:700 }
.sp-variants { margin-top:20px }.sp-variants strong { font-size:13px }.sp-variants>div { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px }
.sp-variants a { padding:10px 16px; min-height:44px; border:1px solid var(--sp-line); border-radius:8px; color:var(--sp-ink); text-decoration:none }
.sp-variants a[aria-current] { color:white; background:var(--sp-green); border-color:var(--sp-green) }
.sp-thumbnails { display:flex; gap:8px; margin-top:12px; overflow-x:auto }
.sp-thumbnails button { background:white; border:1px solid var(--sp-line); border-radius:8px; width:70px; height:60px; padding:5px; flex-shrink:0; cursor:pointer }
.sp-thumbnails button[aria-pressed=true] { border:2px solid var(--sp-green) }.sp-thumbnails img { width:100%;height:100%;object-fit:contain }
.sp-rich-content { display:grid; gap:20px; margin-top:20px }.sp-use-cases,.sp-value-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; margin-top:20px }
.sp-use-cases article,.sp-value-grid article { padding:18px; background:var(--sp-surface); border-radius:10px; min-width:0 }
.sp-use-cases p,.sp-value-grid p { margin-top:8px!important; color:var(--sp-muted) }.sp-value-grid a { display:inline-flex; align-items:center; min-height:44px; color:var(--sp-green); margin-top:12px }
.sp-faq details { border-bottom:1px solid var(--sp-line); padding:10px 0 }.sp-faq summary { min-height:44px; padding:10px 0; cursor:pointer }.sp-faq details p { padding:0 0 16px; color:var(--sp-muted) }
.sp-history-chart { margin-top:20px }.sp-history-chart strong { font-size:26px }.sp-history-chart svg { width:100%; height:auto; margin-top:16px; overflow:visible }.sp-history-chart polyline { fill:none;stroke:var(--sp-green);stroke-width:3 }.sp-history-chart circle { fill:var(--sp-green) }
.sp-chart-dates { display:flex;justify-content:space-between;font-size:12px;color:var(--sp-muted) }.sp-history-chart summary { min-height:44px;padding:12px 0;cursor:pointer }.sp-history-chart table { width:100%; font-size:13px }.sp-history-chart th { text-align:left }.sp-history-chart td { text-align:right }
.sp-discovery { margin:32px 0 }.sp-catalogue-heading a { color:var(--sp-green);min-height:44px;display:inline-flex;align-items:center;white-space:nowrap }
.sp-product-rail { grid-template-columns:none!important;grid-auto-flow:column;grid-auto-columns:calc((100% - 48px)/4);overflow-x:auto;scroll-snap-type:x proximity;padding-bottom:12px }
.sp-product-rail>li { scroll-snap-align:start }.sp-editorial { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px }.sp-editorial a { display:block;padding:24px;border:1px solid var(--sp-line);border-radius:12px;text-decoration:none;color:var(--sp-ink);background:var(--sp-surface) }.sp-editorial p { margin-top:10px!important;color:var(--sp-muted) }
@media(max-width:767px) { .sp-use-cases,.sp-value-grid,.sp-editorial { grid-template-columns:1fr }.sp-product-rail { grid-auto-columns:calc((100% - 10px)/2) }.sp-key-attributes { grid-template-columns:repeat(3,minmax(0,1fr)) }.sp-discovery .sp-catalogue-heading h2 { font-size:22px }.sp-product-summary { font-size:14px } }
"""


def search_highlights(title, explanation, cards, criteria):
    chips=''.join(f'<a href="{e(url,quote=True)}">{e(label)} <span aria-hidden="true">↗</span></a>' for label,url in criteria)
    return f'<section class="sp-home sp-search-highlights"><div><h1>{e(title)}</h1><p>{e(explanation)}</p></div><ul class="sp-product-grid">'+''.join(cards)+f'</ul><nav class="sp-category-chips" aria-label="Forståtte søkekriterier">{chips}</nav></section>'


def loading_state():
    return '<section class="sp-loading" aria-busy="true" aria-label="Laster produkter"><p role="status">Henter produkter …</p><div class="sp-skeleton-grid" aria-hidden="true">'+''.join('<div class="sp-skeleton"><span></span><i></i><i></i></div>' for _ in range(3))+'</div></section>'


def error_state(retry_url):
    return f'<section class="sp-home-empty"><h2>Vi kunne ikke hente produktene</h2><p>Prøv igjen om litt. Du kan også gå tilbake og utforske kategoriene.</p><a class="sp-cta" href="{e(retry_url,quote=True)}">Prøv igjen</a> <a href="/kategori/">Utforsk kategorier</a></section>'


RICH_STYLE += r'''
.sp-search-highlights { margin:24px 0;padding:28px;background:#f0f8f7;border-radius:16px;display:grid;grid-template-columns:minmax(180px,1fr) 3fr;gap:24px }
.sp-search-highlights h1 { font-size:30px;line-height:1.2;letter-spacing:-.8px }.sp-search-highlights>div>p { color:var(--sp-muted);line-height:1.6;margin-top:12px }.sp-search-highlights>.sp-product-grid { grid-template-columns:repeat(3,minmax(0,1fr));margin:0 }.sp-search-highlights nav { grid-column:1/-1 }
.sp-skeleton-grid { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:20px 0 }.sp-skeleton { border:1px solid var(--sp-line);padding:16px;border-radius:12px }.sp-skeleton span,.sp-skeleton i { display:block;background:#e8edf1;border-radius:8px;aspect-ratio:1.4 }.sp-skeleton i { height:16px;aspect-ratio:auto;margin-top:14px;width:85% }.sp-skeleton i:last-child { width:50% }
@media(max-width:767px) { .sp-search-highlights { display:block;padding:20px 16px }.sp-search-highlights>.sp-product-grid { display:grid;grid-template-columns:none;grid-auto-flow:column;grid-auto-columns:80%;overflow-x:auto;margin:20px 0 }.sp-search-highlights h1 { font-size:28px }.sp-skeleton-grid { grid-template-columns:repeat(2,minmax(0,1fr)) }.sp-skeleton:last-child { display:none } }
'''

RICH_STYLE += '.sp-state-gallery { padding:28px 0 }.sp-state-gallery>section { margin-top:24px }.sp-state-gallery h1 { overflow-wrap:anywhere }.sp-state-gallery a:not(.sp-cta) { color:var(--sp-green);display:inline-flex;align-items:center;min-height:44px }'

RICH_STYLE += r"""
.sp-thumbnails button:focus-visible,.sp-variants a:focus-visible,.sp-faq summary:focus-visible,.sp-history-chart summary:focus-visible,.sp-value-grid a:focus-visible,.sp-editorial a:focus-visible { outline:3px solid #177fc5;outline-offset:3px }
.sp-thumbnails { padding:4px;margin-left:-4px }.sp-thumbnails button:hover { border-color:var(--sp-green) }.sp-variants a:hover { box-shadow:0 0 0 1px var(--sp-green) }.sp-faq summary:hover { color:var(--sp-green) }
@media(hover:hover) { .sp-editorial a:hover { border-color:var(--sp-green) } }
"""

RICH_SCRIPT += r"""
(()=>{document.querySelectorAll('[data-observations]').forEach(root=>{
const points=JSON.parse(root.dataset.observations), control=root.querySelector('.sp-history-control'), input=control.querySelector('input'), output=control.querySelector('output'), dots=Array.from(root.querySelectorAll('circle'));
function select(){const index=Number(input.value),text=points[index][0]+': '+points[index][1];output.textContent=text;input.setAttribute('aria-valuetext',text);dots.forEach((dot,i)=>{dot.classList.toggle('sp-point-selected',i===index);dot.setAttribute('r',i===index?'6':'4');});}
control.hidden=false;input.addEventListener('input',select);select();
});})();
"""
RICH_STYLE += r"""
.sp-history-summary { display:grid;grid-template-columns:1fr 1fr;gap:16px }.sp-history-summary p { font-size:12px;color:var(--sp-muted) }.sp-history-summary strong { display:block;margin-top:6px;font-size:23px }.sp-history-basis { font-size:12px;color:var(--sp-muted);margin-top:12px!important }
.sp-history-chart { position:relative }.sp-chart-scale { display:flex;justify-content:space-between;margin-top:20px;font-size:11px;color:var(--sp-muted) }.sp-history-chart svg { margin-top:4px }.sp-history-chart circle.sp-point-selected { stroke:#fff;stroke-width:3;paint-order:stroke;fill:var(--sp-green) }
.sp-history-control { background:var(--sp-surface);padding:12px;border-radius:8px;margin-top:16px }.sp-history-control[hidden] { display:none }.sp-history-control label { display:block;font-size:12px;color:var(--sp-muted) }.sp-history-control input { display:block;width:100%;height:44px;margin:0;accent-color:var(--sp-green);cursor:pointer }.sp-history-control input:focus-visible { outline:3px solid #177fc5;outline-offset:2px }.sp-history-control output { display:block;font-weight:700;font-size:14px;min-height:20px }
"""


RICH_SCRIPT += r"""
(()=>{
 document.querySelectorAll('.sp-tabs').forEach(nav=>{
 const links=Array.from(nav.querySelectorAll('a[href^="#"]'));
 function sync(hash=location.hash){const active=links.find(a=>a.hash===hash)||links[0];links.forEach(a=>{if(a===active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}
 links.forEach(a=>a.addEventListener('click',()=>{sync(a.hash);const target=document.getElementById(a.hash.slice(1));if(target){target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}}));
 window.addEventListener('hashchange',()=>sync());sync();
 });
 document.querySelectorAll('.sp-gallery').forEach(gallery=>{
 if(!gallery.querySelector('.sp-image img'))return;
 const button=document.createElement('button');button.type='button';button.className='sp-image-expand';button.textContent='Se større bilde';gallery.append(button);
 const dialog=document.createElement('dialog');dialog.className='sp-image-dialog';dialog.setAttribute('aria-label','Forstørret produktbilde');
 const close=document.createElement('button');close.type='button';close.textContent='Lukk bilde';close.className='sp-image-close';
 const image=document.createElement('img');dialog.append(close,image);document.body.append(dialog);
 button.addEventListener('click',()=>{const source=Array.from(gallery.querySelectorAll('.sp-image img')).find(img=>!img.closest('[hidden]'));if(!source)return;image.src=source.currentSrc||source.src;image.alt=source.alt;dialog.showModal();});
 close.addEventListener('click',()=>dialog.close());dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close();}});
 dialog.addEventListener('close',()=>button.focus());
 });
})();
"""
RICH_STYLE += r"""
.sp-product .sp-panel[id] { scroll-margin-top:20px }.sp-product .sp-panel[id]:focus { outline:none }.sp-product .sp-panel[id]:focus-visible { outline:3px solid #177fc5;outline-offset:4px }
.sp-key-attributes dt,.sp-key-attributes dd,.sp-specs dt,.sp-use-cases h3,.sp-value-grid h3 { overflow-wrap:anywhere;min-width:0 }.sp-specs div { grid-template-columns:minmax(0,1fr) minmax(0,1fr) }
.sp-image-expand,.sp-image-close { min-height:44px;padding:10px 16px;border:1px solid var(--sp-line);border-radius:8px;background:white;color:var(--sp-green);font:600 13px Arial,Helvetica,sans-serif;cursor:pointer }.sp-image-expand { margin-top:12px }.sp-image-expand:focus-visible,.sp-image-close:focus-visible { outline:3px solid #177fc5;outline-offset:3px }
.sp-image-dialog { width:min(1000px,calc(100vw - 32px));max-height:calc(100dvh - 32px);padding:16px;border:1px solid var(--sp-line);border-radius:12px;background:white;color:var(--sp-ink) }.sp-image-dialog::backdrop { background:#10203bb3 }.sp-image-dialog img { display:block;width:100%;height:auto;max-height:calc(100dvh - 140px);object-fit:contain }.sp-image-close { display:block;margin-left:auto }.sp-image-expand:hover,.sp-image-close:hover { background:var(--sp-mint) }
"""

RICH_STYLE += '@media(max-width:767px) { .sp-image-dialog { width:calc(100vw - 8px);max-width:none;padding:0 }.sp-image-close { margin:8px 8px 8px auto }.sp-image-dialog img { padding:0 0 8px } }'
