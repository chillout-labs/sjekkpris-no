"""Isolated layout fixtures for different proportions and dense offer lists."""
import copy
import json
from PIL import Image, ImageDraw
import build
from home_release import page, home_money
from catalogue_ui import render_listing
from test_build import offer, TOKEN_WINNER


def create_scenarios(out, products):
    prototype=products[0]
    # Technical proportion diagrams, not product photography or real packaging.
    dimensions = [('portrait', 320, 800), ('square', 600, 600), ('wide', 1000, 300)]
    for name, width, height in dimensions:
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        inset = min(width, height) // 12
        draw.rounded_rectangle((inset, inset, width-inset, height-inset), radius=16,
                               fill='#edf8f4', outline='#006454', width=4)
        draw.line((inset*2, height//2, width-inset*2, height//2), fill='#006454', width=4)
        draw.text((inset*2, height//2+16), f'{width} x {height}', fill='#10203b')
        image.save(out/f'assets/layout-{name}.webp')
    items=[]
    examples=[('demo-pakning', 'Eksempel på kontaktlinsepakning – 30 stk.', 'Kontaktlinser', 'square'),
              ('demo-hoy', 'Eksempel på et høyt husholdningsprodukt', 'Hjem og husholdning', 'portrait'),
              ('demo-bred', 'Eksempel på bred produktpakning med lang modellbetegnelse', 'Elektronikk', 'wide')]
    for index,(slug,name,category,shape) in enumerate(examples):
        product=copy.deepcopy(prototype)
        product.update(local_slug=slug,local_name=name,local_brand='Eksempelmerke',local_category=category,
                       categories={'primary':{'id':slug,'display_name':category,'active':True,'path':[{'id':slug,'display_name':category}]}},
                       image={'url':f'https://sjekkpris.no/assets/layout-{shape}.webp'},
                       lowest_item_price={'minor':24900+index*10000,'currency':'NOK'},offer_count=2)
        if category=='Elektronikk':
            product['categories']['primary']['id']='demo-electronics'
            product['categories']['primary']['path']=[{'id':'demo-electronics','display_name':category}]
        minor=product['lowest_item_price']['minor']
        offers=[offer('a','Eksempelbutikk A',minor,token=TOKEN_WINNER),offer('b','Eksempelbutikk B',minor+2000)]
        body={'identity':product,'offers':offers,'excluded':[],'lowest_item_price':'a','lowest_known_total_price':None}
        presentation={'summary':'Kun et eksempel på utforming. Bildene er måldiagrammer, og dette er ikke en virkelig vare.',
            'gallery':[({'url':f'https://sjekkpris.no/assets/layout-{s}.webp'},f'Måldiagram: {s}') for s in [shape]+[s for s,_,_ in dimensions if s!=shape]],
            'specs':[('Eksempeltype',category),('Visning','Ulike bildeproporsjoner')],
            'about':'Denne siden tester hvordan produktmalen håndterer ulike kategorier og bildeformater. Ingen produktegenskaper eller kjøpsråd er bekreftet.'}
        target=out/f'p/catalogue/{slug}';target.mkdir(parents=True,exist_ok=True)
        html=build.product_body(product,body,base='/',breadcrumbs=[('Produkttyper','/produkttyper/')],presentation=presentation)
        (target/'index.html').write_text(build.page(name,html,base='/',noindex=True),encoding='utf-8')
        items.append(product)
    target=out/'produkttyper';target.mkdir(exist_ok=True)
    content=render_listing(items,base='/',money=home_money,day=build.day,segment=build.segment,title='Ulike produkttyper',category=True)
    content=content.replace('<h1>Ulike produkttyper</h1>','<h1>Ulike produkttyper</h1><p>Fiktive eksempler med kvadratiske, høye og brede måldiagrammer. Åpne et produkt for å prøve bildegalleriet.</p>')
    (target/'index.html').write_text(page('Produkttyper – designtest',content,base='/',noindex=True),encoding='utf-8')
    from category_catalog import category_index, render_category_index, category_href
    nodes=category_index(products+items)
    index_path=out/'search-index.json'
    index=json.loads(index_path.read_text(encoding='utf-8'))
    index.extend({'name':p['local_name'],'url':f"/p/catalogue/{p['local_slug']}/",'price':home_money(p['lowest_item_price'])} for p in items)
    index_path.write_text(json.dumps(index),encoding='utf-8')
    search=render_listing(products+items,base='/',money=home_money,day=build.day,segment=build.segment)
    (out/'search/index.html').write_text(page('Søk – SjekkPris',search,base='/',noindex=True),encoding='utf-8')
    (out/'kategori/index.html').write_text(page('Utforsk kategorier',render_category_index(nodes,'/'),base='/',noindex=True),encoding='utf-8')
    for node in nodes.values():
        if node['slug']=='tv':continue  # Keep the detailed TV help and facets.
        target=out/'kategori'/node['slug'];target.mkdir(parents=True,exist_ok=True)
        content=render_listing(list(node['products'].values()),base='/',money=home_money,day=build.day,segment=build.segment,
            title=node['name'],category=True,children=[(nodes[k]['name'],category_href(nodes[k],'/'),len(nodes[k]['products'])) for k in node['children']])
        (target/'index.html').write_text(page(node['name'],content,base='/',noindex=True),encoding='utf-8')
    # A dense list includes stale, unavailable and excluded offers, all explicit.
    product=copy.deepcopy(prototype)
    product['local_name']='Eksempel med mange butikker og lange variantnavn'
    product['local_slug']='demo-mange-tilbud'
    offers=[]
    for i in range(12):
        minor=129900+i*1700
        o=offer(f'offer-{i}',f'Eksempelbutikk {i+1}' if i!=1 else 'EksempelbutikkMedEtSværtLangtSammenhengendeNavn',minor,
                shipping_state='confirmed_free' if i%3==0 else 'not_provided',
                total={'minor':minor,'currency':'NOK'} if i%3==0 else None,
                token=TOKEN_WINNER if i<9 else None,eligible=i<9,
                availability='out_of_stock' if i==10 else 'unknown' if i==11 else 'in_stock',stale=i==9)
        if i%3==0 and i<9:o['ranking']['total_price']['ranking_eligible']=True
        offers.append(o)
    excluded=offer('excluded','Eksempelbutikk – annen pakningsstørrelse',99900,eligible=False)
    excluded['comparison_status']='not_comparable'
    body={'identity':product,'offers':offers,'excluded':[excluded],'lowest_item_price':'offer-0','lowest_known_total_price':'offer-0'}
    url='/p/catalogue/demo-mange-tilbud/'
    presentation={'summary':'Designeksempel med tolv tilbud og ett tilbud som ikke kan sammenlignes. Variantnavnene tester tekstbryting og åpner samme eksempelside.',
                  'variants':[(label,url,i==0) for i,label in enumerate(['Standardpakning','Større pakning med ekstra tilbehør','EkstraLangSammenhengendeVariantbetegnelseForLayoutkontroll'])]}
    target=out/'p/catalogue/demo-mange-tilbud';target.mkdir(parents=True,exist_ok=True)
    (target/'index.html').write_text(build.page(product['local_name'],build.product_body(product,body,base='/',breadcrumbs=[('Designoversikt','/designoversikt/')],presentation=presentation),base='/',noindex=True),encoding='utf-8')
