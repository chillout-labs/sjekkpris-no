"""Rendering regressions with synthetic data; these are not visual approvals."""
import copy
import unittest

import build
from test_build import COMPARISONS, INDEX, TOKEN_WINNER, offer


class ProductUITest(unittest.TestCase):
    def test_known_total_shows_actual_breakdown_and_merchant(self):
        winner = offer('total', 'FIXTURE Shop <A>', 129900,
                       shipping_state='known_amount',
                       total={'minor': 134800, 'currency': 'NOK'},
                       token=TOKEN_WINNER)
        winner['shipping']['amount'] = {'minor': 4900, 'currency': 'NOK'}
        winner['ranking']['total_price']['ranking_eligible'] = True
        selected, kind = build.find_hero_offer([winner], 'total', None)
        html = build.render_price_hero(selected, kind)
        self.assertEqual(kind, 'total')
        self.assertIn('Laveste kjente totalpris', html)
        self.assertIn('1\u00a0348 kr', html)
        self.assertIn('Varepris 1\u00a0299 kr + frakt 49 kr', html)
        self.assertIn('hos FIXTURE Shop &lt;A&gt;', html)
        self.assertIn('Gå til butikken', html)
        self.assertNotIn('Gå til FIXTURE', html)

    def test_unknown_shipping_does_not_become_free_shipping(self):
        winner = offer('item', 'FIXTURE Shop', 129900, token=TOKEN_WINNER)
        selected, kind = build.find_hero_offer([winner], None, 'item')
        html = build.render_price_hero(selected, kind)
        self.assertEqual(kind, 'item')
        self.assertIn('Laveste varepris', html)
        self.assertIn('Frakt ukjent', html)
        self.assertNotIn('frakt 0 kr', html)
        self.assertNotIn('Laveste kjente totalpris', html)

    def test_no_winner_is_not_invented_from_cheapest_offer(self):
        winner = offer('cheap', 'FIXTURE Shop', 100, token=TOKEN_WINNER)
        selected, kind = build.find_hero_offer([winner], 'missing', 'missing')
        self.assertEqual((selected, kind), (None, 'none'))
        html = build.render_price_hero({}, kind)
        self.assertIn('Ingen sammenlignbar pris', html)
        self.assertNotIn('/go/', html)

    def test_empty_product_has_no_store_cta(self):
        html = build.product_body(INDEX['products'][0], {'offers': []}, base='/')
        self.assertIn('Ingen tilbud akkurat nå', html)
        self.assertNotIn('Gå til butikken', html)
        self.assertNotIn('/go/', html)

    def test_single_heading_precedes_image_in_document(self):
        body = copy.deepcopy(COMPARISONS['fixture-lamp'])
        body['identity']['image'] = {'url': 'https://fixture.invalid/image.png'}
        html = build.product_body(INDEX['products'][0], body, base='/beta/')
        self.assertEqual(html.count('<h1'), 1)
        self.assertLess(html.index('<h1'), html.index('<img'))
        self.assertNotIn('FIXTURE Lamp <b>', html)

    def test_header_search_preserves_base_path_and_noindex(self):
        html = build.page('Test', '', base='/beta/', noindex=True)
        self.assertIn('action="/beta/search/" method="get"', html)
        self.assertIn('name="q"', html)
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertIn('<details class="sp-menu">', html)

    def test_confirmed_free_shipping_is_explicit(self):
        winner = offer('free', 'FIXTURE Shop', 129900,
                       shipping_state='confirmed_free',
                       total={'minor': 129900, 'currency': 'NOK'})
        winner['ranking']['total_price']['ranking_eligible'] = True
        selected, kind = build.find_hero_offer([winner], 'free', None)
        html = build.render_price_hero(selected, kind)
        self.assertIn('Varepris 1\u00a0299 kr + frakt 0 kr', html)
        self.assertIn('Fri frakt', html)

    def test_test_shipping_terms_cannot_support_a_hero_claim(self):
        winner = offer('test', 'FIXTURE Shop', 100,
                       shipping_state='confirmed_free',
                       total={'minor': 100, 'currency': 'NOK'})
        winner['ranking']['total_price']['ranking_eligible'] = True
        winner['shipping']['terms'] = {'is_test_data': True}
        self.assertEqual(build.find_hero_offer([winner], 'test', 'test'), (None, 'none'))
        html = build.offer_row(winner, lowest=None, excluded=False)
        self.assertIn('Frakt ikke bekreftet', html)
        self.assertIn('Totalpris ukjent', html)
        self.assertNotIn('Fri frakt', html)

    def test_api_total_winner_takes_priority_over_lower_item_price(self):
        total = offer('total', 'FIXTURE Total Shop', 200,
                      shipping_state='confirmed_free',
                      total={'minor': 200, 'currency': 'NOK'})
        total['ranking']['total_price']['ranking_eligible'] = True
        item = offer('item', 'FIXTURE Item Shop', 100)
        selected, kind = build.find_hero_offer([item, total], 'total', 'item')
        self.assertIs(selected, total)
        self.assertEqual(kind, 'total')

    def test_excluded_offer_retains_information_but_has_no_clickout(self):
        excluded = offer('excluded', 'FIXTURE Excluded Shop', 12300,
                         token=TOKEN_WINNER)
        html = build.offer_row(excluded, lowest='excluded', excluded=True)
        self.assertIn('FIXTURE Excluded Shop', html)
        self.assertIn('123 kr', html)
        self.assertIn('Ingen lenke', html)
        self.assertNotIn('/go/', html)
        self.assertNotIn('Laveste pris', html)

    def test_light_design_has_no_automatic_dark_token_override(self):
        self.assertNotIn('prefers-color-scheme: dark', build.STYLE)


if __name__ == '__main__':
    unittest.main()
