"""Exercise existing search/cards/controls with 2 and 20 synthetic colors."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
import json
from playwright.sync_api import sync_playwright
import build
from catalogue_ui import render_listing
from home_release import home_money
from rich_ui import variants
from test_variant_discovery import choices


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
            page.route('**/*',lambda route: route.fulfill(status=200,content_type='text/html',body=html) if route.request.resource_type=='document' else route.abort())
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
            field.fill('Synthetic Model unknowncolor')
            assert page.locator('#search-results>li:visible').count()==0
            control=variants([(v['local_name'],v['presentation_url'],i==count-1) for i,v in enumerate(values)])
            page.set_content(build.page('Synthetic colors',control,base='/',noindex=True))
            assert page.locator('.sp-variants a:visible').count()==min(count,6)
            assert page.locator('.sp-variants a[aria-current=page]:visible').count()==1
            if count==20:
                summary=page.get_by_text('Vis alle 20 farger',exact=True)
                summary.focus();page.keyboard.press('Enter')
                assert page.locator('.sp-variants a:visible').count()==20
            assert not errors,errors
            context.close()
    browser.close()
print(json.dumps({'synthetic':True,'viewports':[390,1280],'colors':[2,20],'result':'passed'}))
