"""Homepage HTML/contract checks. Browser/visual verification remains separate."""
import copy
from html.parser import HTMLParser
import unittest

import build
from test_build import INDEX


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class HomeUITest(unittest.TestCase):
    def render(self, products):
        return build.page('Test', build.index_body(products, base='/beta/'),
                          base='/beta/', noindex=True, home=True)

    def test_only_one_search_form_on_homepage(self):
        html = self.render(INDEX['products'])
        forms = [a for tag, a in Elements(html).elements if tag == 'form']
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]['action'], '/beta/search/')
        self.assertEqual(forms[0]['method'], 'get')
        self.assertEqual(forms[0]['data-index'], '/beta/search-index.json')
        self.assertIn('Søket finner foreløpig produkter etter navn.', html)

    def test_each_catalogue_product_has_exactly_one_card(self):
        html = self.render(INDEX['products'])
        cards = [a for t, a in Elements(html).elements
                 if t == 'article' and a.get('class') == 'sp-product-card']
        self.assertEqual(len(cards), len(INDEX['products']))
        self.assertIn('1\u00a0299 kr', html)
        self.assertIn('Laveste varepris', html)
        self.assertIn('Frakt kan komme i tillegg', html)
        self.assertIn('Ingen pris', html)
        self.assertNotIn('<table', html)

    def test_single_product_is_not_duplicated_to_fill_grid_or_examples(self):
        html = self.render(INDEX['products'][:1])
        self.assertEqual(html.count('<article class="sp-product-card">'), 1)
        self.assertEqual(html.count('class="sp-example"'), 1)
        self.assertIn('>1 produkt</span>', html)

    def test_empty_catalogue_keeps_search_but_has_no_placeholder_products(self):
        html = self.render([])
        self.assertIn('Ingen produkter er publisert ennå.', html)
        self.assertIn('id="home-query"', html)
        self.assertNotIn('<article', html)
        self.assertNotIn('class="sp-example"', html)

    def test_long_and_html_like_names_are_preserved_and_escaped(self):
        products = copy.deepcopy(INDEX['products'][:1])
        name = '<img src=x onerror=alert(1)> ' + 'Langt produktnavn æøå ' * 30
        products[0]['local_name'] = name
        html = self.render(products)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('Langt produktnavn æøå ' * 30, html)

    def test_no_unsupported_content_claims_or_dead_buttons(self):
        html = self.render(INDEX['products'])
        for claim in ['Dagens beste priser', 'Mest søkt akkurat nå', 'Fortsett der du slapp',
                      'Best i test', 'Ny lavpris', 'kommer snart']:
            self.assertNotIn(claim, html)
        self.assertNotIn('href="#"', html)
        self.assertNotIn('/go/', html)

    def test_combobox_references_existing_ids(self):
        elements = Elements(self.render(INDEX['products'])).elements
        ids = [a['id'] for _, a in elements if 'id' in a]
        self.assertEqual(len(ids), len(set(ids)))
        field = next(a for _, a in elements if a.get('id') == 'home-query')
        self.assertEqual(field['role'], 'combobox')
        self.assertIn(field['aria-controls'], ids)
        self.assertIn(field['aria-describedby'], ids)
        self.assertEqual(field['aria-expanded'], 'false')


if __name__ == '__main__':
    unittest.main()
