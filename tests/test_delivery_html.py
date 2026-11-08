import copy
import json
import re
import unittest
from unittest.mock import patch

import build
from tools.render_delivery_html import render_pair
from test_build import INDEX, COMPARISONS, TOKEN_WINNER


class PairedHTMLTests(unittest.TestCase):
    def test_same_renderer_and_no_offer_fallback(self):
        p, c = INDEX['products'][0], COMPARISONS['fixture-lamp']
        before = copy.deepcopy(c)
        active, safe = render_pair(p, c, path='/p/fixture-lamp/', noindex=True)
        self.assertEqual(c, before)
        for raw in (active, safe):
            html = raw.decode()
            self.assertIn('name="viewport"', html)
            self.assertIn('noindex', html)
            self.assertIn('https://sjekkpris.no/p/fixture-lamp/', html)
            self.assertIn('sp-product', html)
            self.assertIn('sp-gallery', html)
        self.assertIn(TOKEN_WINNER.encode(), active)
        self.assertNotIn(b'/go/', safe)
        schemas = [json.loads(re.findall(r'<script type="application/ld\+json">(.*?)</script>', b.decode())[0])
                   for b in (active, safe)]
        self.assertNotIn('offers', schemas[1])
        self.assertEqual(schemas[0]['offers'][0]['price'], '1299.00')
        self.assertEqual(schemas[0]['offers'][0]['url'], build.SITE_ORIGIN + '/go/' + TOKEN_WINNER)

    def test_only_changed_products_are_rendered(self):
        # Adapter invokes this once for each changed comparison, never a catalogue build.
        with patch.object(build, 'product_body', wraps=build.product_body) as render:
            render_pair(INDEX['products'][0], COMPARISONS['fixture-lamp'],
                        path='/p/fixture-lamp/', noindex=True)
            self.assertEqual(render.call_count, 2)

    def test_policy_and_route_required(self):
        with self.assertRaises(ValueError):
            render_pair({}, {}, path='/p/../', noindex=True)
