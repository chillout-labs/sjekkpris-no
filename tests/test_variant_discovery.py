"""Synthetic display-only facts. No approval, identity or price inference."""
import json
import unittest
import tempfile
from pathlib import Path
from html.parser import HTMLParser

import build
from catalogue_ui import render_listing
from home_ui import render_product_card, variant_search_entry
from rich_ui import variants
import home_release


def choices(count):
    return [dict(namespace='synthetic', local_slug='color-'+str(i),
                 local_name='Synthetic Model – '+('Svart' if i == 0 else 'Hvit' if i == 1 else 'Farge '+str(i)),
                 presentation_url='/p/synthetic-model/?farge='+str(i),
                 image={'url':'https://sjekkpris.no/images/synthetic-'+str(i)+'.png'},
                 lowest_item_price={'minor':(i+1)*10000,'currency':'NOK'}, offer_count=i+1)
            for i in range(count)]


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.tags=[]; self.feed(html)
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag,dict(attrs)))


class VariantDiscovery(unittest.TestCase):
    def test_unsafe_color_links_refuse_before_rendering(self):
        for url in ('javascript:alert(1)','//foreign.invalid/p/model/?farge=red','/p/model/?farge=red&foreign=1','/p/model/?farge=../red'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                variant_search_entry(dict(choices(2)[0],presentation_url=url),build.money)

    def test_search_index_rejects_image_that_card_rejects(self):
        values=choices(2)
        values[1]['image']={'url':'https://foreign.example.invalid/unreviewed.png'}
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            home_release.write_home([dict(values[0],variant_choices=values)],out,base='/',noindex=True,day=build.day,segment=build.segment)
            entries=json.loads((out/'search-index.json').read_bytes())[0]['variants']
        self.assertIsNone(entries[1]['image'])

    def test_card_has_one_image_price_and_link_without_color_picker(self):
        values=choices(2)
        html=render_product_card(dict(values[0],variant_choices=values),base='/',money=build.money,day=build.day,segment=build.segment)
        tags=Tags(html).tags
        self.assertEqual(len([a for t,a in tags if t=='img']),1)
        self.assertEqual([a['href'] for t,a in tags if t=='a'],[values[0]['presentation_url']])
        self.assertIn('Andre farger tilgjengelig',html)
        self.assertNotIn('<nav',html)
        options=json.loads(next(a for t,a in tags if 'data-variant-options' in a)['data-variant-options'])
        self.assertEqual([v['price'] for v in options],['100 kr','200 kr'])

    def test_two_and_twenty_choices_keep_selected_visible_and_all_linkable(self):
        for count in (2,20):
            html=variants([(str(i),'/p/model/?farge='+str(i),i==count-1) for i in range(count)])
            tags=Tags(html).tags
            self.assertEqual(len([a for t,a in tags if t=='a']),count)
            self.assertEqual(sum(a.get('aria-current')=='page' for t,a in tags),1)
            self.assertEqual('<details>' in html,count>6)
            if count>6:
                self.assertIn('Vis alle 20 farger',html)
                self.assertIn('farge=19',html.split('<details>')[0])


if __name__=='__main__':
    unittest.main()
