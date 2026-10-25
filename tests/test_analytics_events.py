import unittest
from analytics_events import events_markup
from build import page as product_page
from home_release import page as homepage_page

class AnalyticsEventsTests(unittest.TestCase):
    def test_events_are_consent_gated_and_do_not_export_click_tokens(self):
        script=events_markup()
        for event in ('view_item','select_item','search','merchant_click'):
            self.assertIn('"'+event+'"',script)
        self.assertIn('sp-analytics-consent-v1',script)
        self.assertIn('sp-analytics-enabled',script)
        self.assertNotIn('click_id:',script)
        self.assertNotIn('clickout_url:',script)
        self.assertIn('items:[{item_id:',script)

    def test_both_generators_embed_listener_once(self):
        for render in (product_page,homepage_page):
            with self.subTest(render=render.__module__):
                html=render('Test','<p>Test</p>',base='/',noindex=True)
                self.assertEqual(html.count('document.addEventListener("submit"'),1)
                self.assertEqual(html.count('document.addEventListener("click"'),1)
