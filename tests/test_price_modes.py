"""Approved item-price default and shipping-toggle behavior."""
import unittest
from html.parser import HTMLParser

import build
from test_build import offer, TOKEN_WINNER


def scenario():
    a = offer('a', 'Fixture A', 149900, shipping_state='known_amount',
              total={'minor': 159800, 'currency': 'NOK'}, token=TOKEN_WINNER)
    a['shipping']['amount'] = {'minor': 9900, 'currency': 'NOK'}
    a['ranking']['total_price']['ranking_eligible'] = True
    b = offer('b', 'Fixture B', 154900, shipping_state='confirmed_free',
              total={'minor': 154900, 'currency': 'NOK'}, token=TOKEN_WINNER)
    b['ranking']['total_price']['ranking_eligible'] = True
    c = offer('c', 'Fixture Unknown', 140000, token=TOKEN_WINNER)
    # Backend holds the item claim on c and the total claim on b.
    return {'offers': [b, a, c], 'excluded': [],
            'lowest_item_price': 'c', 'lowest_known_total_price': 'b'}


class VisibleText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hidden = [False]
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in ('input', 'img', 'br', 'meta', 'link', 'hr'):
            return
        self.hidden.append(self.hidden[-1] or 'hidden' in dict(attrs) or tag in ('script', 'style', 'noscript'))

    def handle_endtag(self, tag):
        if len(self.hidden) > 1:
            self.hidden.pop()

    def handle_data(self, text):
        if not self.hidden[-1]:
            self.text.append(text)


class PriceModesTest(unittest.TestCase):
    def test_default_page_uses_only_item_hero_and_has_unchecked_switch(self):
        body = scenario()
        html = build.product_body({'local_name': 'Fixture'}, body, base='/')
        visible = ' '.join(VisibleText(html).text)
        self.assertIn('Laveste varepris', visible)
        self.assertIn('hos Fixture Unknown', visible)
        self.assertNotIn('Laveste kjente totalpris', visible)
        self.assertNotIn('hos Fixture B', visible)
        self.assertIn('data-price-basis="item"', html)
        self.assertIn('id="include-shipping" type="checkbox" role="switch"', html)
        self.assertNotIn(' checked', html)

    def test_mode_changes_api_winner_and_uses_total_not_item_amount(self):
        body = scenario()
        total = build.price_mode_hero(body['offers'], body, include_shipping=True)
        item = build.price_mode_hero(body['offers'], body, include_shipping=False)
        self.assertIn('hos Fixture B', total)
        self.assertIn('1\u00a0549 kr', total)
        self.assertIn('hos Fixture Unknown', item)
        self.assertIn('1\u00a0400 kr', item)
        self.assertNotIn('Ingen bekreftet totalprisvinner', item)

    def test_paid_shipping_breakdown_uses_backend_total(self):
        body = scenario()
        body['lowest_known_total_price'] = 'a'
        html = build.price_mode_hero(body['offers'], body, include_shipping=True)
        self.assertIn('1\u00a0598 kr', html)
        self.assertIn('Varepris 1\u00a0499 kr + frakt 99 kr', html)
        self.assertIn('hos Fixture A', html)

    def test_display_sorts_and_keeps_unknown_total_after_known(self):
        offers = scenario()['offers']
        self.assertEqual(build.price_display_order(offers, include_shipping=False), [2, 1, 0])
        self.assertEqual(build.price_display_order(offers, include_shipping=True), [0, 1, 2])

    def test_same_price_preserves_api_order_and_test_totals_sort_last(self):
        offers = scenario()['offers']
        offers[1]['known_total_price'] = dict(offers[0]['known_total_price'])
        self.assertEqual(build.price_display_order(offers, include_shipping=True), [0, 1, 2])
        offers[0]['shipping']['terms'] = {'is_test_data': True}
        self.assertEqual(build.price_display_order(offers, include_shipping=True), [1, 0, 2])

    def test_total_mode_without_winner_does_not_silently_show_item_price(self):
        body = scenario()
        body['lowest_known_total_price'] = None
        html = build.price_mode_hero(body['offers'], body, include_shipping=True)
        self.assertIn('Ingen kjent totalpris', html)
        self.assertNotIn('sp-amount', html)
        self.assertNotIn('/go/', html)

    def test_no_item_winner_does_not_substitute_total_winner_by_default(self):
        body = scenario()
        body['lowest_item_price'] = None
        html = build.price_mode_hero(body['offers'], body, include_shipping=False)
        self.assertIn('Ingen sammenlignbar pris', html)
        self.assertNotIn('hos Fixture B', html)

    def test_display_sort_does_not_compare_different_currencies(self):
        offers = scenario()['offers']
        offers[0]['item_price']['currency'] = 'EUR'
        with self.assertRaises(build.BuildError):
            build.price_display_order(offers, include_shipping=False)


if __name__ == '__main__':
    unittest.main()
