"""Exercise existing search/cards/controls with 2 and 20 synthetic colors."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
import json
import argparse
import base64
from playwright.sync_api import sync_playwright
import build
from catalogue_ui import render_listing, LISTING_STYLE
from home_release import home_money
from rich_ui import variants
from test_variant_discovery import choices

parser=argparse.ArgumentParser()
parser.add_argument('--axe',type=Path)
parser.add_argument('--out',type=Path)
args=parser.parse_args()
if args.out: args.out.mkdir(parents=True,exist_ok=False)
pixel=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZ1EAAAAASUVORK5CYII=')
css=build.STYLE+build.PRODUCT_STYLE+build.HOME_STYLE+LISTING_STYLE

with sync_playwright() as p:
    browser=p.chromium.launch()
    for count in (2,20):
        values=choices(count)
        product=dict(values[0],variant_choices=values)
        listing=render_listing([product],base='/',money=home_money,day=build.day,segment=build.segment)
        for width in (390,1280):
            context=browser.new_context(viewport={'width':width,'height':900})
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            html=build.page('Synthetic variant test',listing,base='/',noindex=True)
            entries=[dict(name=v['local_name'],url=v['presentation_url'],price=home_money(v['lowest_item_price']),image=v['image']) for v in values]
            def route(r):
                if r.request.resource_type=='document': r.fulfill(status=200,content_type='text/html',body=html)
                elif r.request.url.endswith('/search-index.json'): r.fulfill(status=200,content_type='application/json',body=json.dumps([dict(entries[0],variants=entries)]))
                elif r.request.resource_type=='image': r.fulfill(status=200,content_type='image/png',body=pixel)
                elif r.request.resource_type=='stylesheet': r.fulfill(status=200,content_type='text/css',body=css)
                else: r.abort()
            page.route('**/*',route)
            page.goto('http://127.0.0.1:19999/search/?q=Synthetic+Model')
            card=page.locator('#search-results>li:visible')
            assert card.count()==1
            assert card.locator('a').get_attribute('href').endswith('farge=0')
            field=page.locator('#home-query')
            for query,index in [('Synthetic Model Hvit',1),('Synthetic Model Svart',0),('Synthetic Model',0)]:
                field.fill(query)
                assert card.locator('a').get_attribute('href').endswith('farge='+str(index))
                assert card.locator('img').get_attribute('src')==values[index]['image']['url']
                assert card.locator('.sp-card-price').inner_text()==home_money(values[index]['lowest_item_price'])
                assert card.locator('img').count()==1
                page.wait_for_selector('#home-suggestions li')
                assert page.locator('#home-suggestions li').count()==1
                assert page.locator('#home-suggestions img').get_attribute('src')==values[index]['image']['url']
            field.fill('Synthetic Model unknowncolor')
            assert page.locator('#search-results>li:visible').count()==0
            assert not errors,errors
            page.close()
            page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            control=variants([(v['local_name'],v['presentation_url'],i==count-1) for i,v in enumerate(values)])
            page.set_content(build.page('Synthetic colors','<h1>Syntetiske fargevalg</h1>'+control,base='/',noindex=True))
            page.add_style_tag(content=css)
            assert page.locator('.sp-variants a:visible').count()==min(count,6)
            assert page.locator('.sp-variants a[aria-current=page]:visible').count()==1
            if count==20:
                summary=page.get_by_text('Vis alle 20 farger',exact=True)
                summary.focus();page.keyboard.press('Enter')
                assert page.locator('.sp-variants a:visible').count()==20
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            if args.axe:
                page.add_script_tag(path=str(args.axe))
                violations=page.evaluate("async()=> (await axe.run(document.querySelector('.sp-variants'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
                assert not violations,[(v['id'],[n['target'] for n in v['nodes']]) for v in violations]
            if args.out: page.screenshot(path=str(args.out/f'colors-{count}-{width}.png'),full_page=True)
            assert not errors,errors
            context.close()
    browser.close()
print(json.dumps({'synthetic':True,'viewports':[390,1280],'colors':[2,20],'result':'passed'}))
