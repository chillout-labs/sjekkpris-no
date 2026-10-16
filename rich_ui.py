"""Optional presentation components. Callers supply validated display data.

No API fields or publication decisions are inferred here. The complete-state
fixtures live exclusively in tools/preview_design.py until a data adapter exists.
"""
from html import escape as e
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
    return f'<div class="sp-history-chart"><p>Laveste varepris i perioden</p><strong>{format(low, ',').replace(',', ' ')} kr</strong><svg viewBox="0 0 320 155" role="img" aria-label="Prisutvikling. Verdier finnes i pristabellen."><polyline points="{line}"/>{dots}</svg><div class="sp-chart-dates"><span>{e(points[0][0])}</span><span>{e(points[-1][0])}</span></div><details><summary>Se alle prisobservasjoner</summary><table><caption class="sp-sr">Varepris uten frakt per dato</caption>{table}</table></details></div>'


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
 buttons.forEach((button,index)=>button.addEventListener('click',()=>{slides.forEach((s,i)=>s.hidden=i!==index);buttons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));root.querySelector('[data-gallery-status]').textContent='Bilde '+(index+1)+' av '+slides.length;}));
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
