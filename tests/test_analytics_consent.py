import unittest
from analytics_consent import GTM_ID, head_markup, body_markup, footer_link
from build import page as product_page
from home_release import page as homepage_page

class GTMConsentTests(unittest.TestCase):
    def test_shared_markup(self):
        script=body_markup()
        self.assertIn(GTM_ID,script)
        self.assertIn("choice===\"accepted\"",script)
        self.assertIn('data-choice="reject"',script)
        self.assertIn('data-choice="accept"',script)
        self.assertIn("sp-consent-settings",footer_link())
        self.assertIn("sp-consent",head_markup())

    def test_both_page_generators(self):
        for page in (product_page,homepage_page):
            with self.subTest(page=page.__module__):
                html=page("Test", "<p>Test</p>",base="/",noindex=True)
                self.assertIn(GTM_ID,html)
                self.assertIn("sp-consent",html)
                self.assertIn("sp-consent-settings",html)
                self.assertNotIn('<script src="https://www.googletagmanager.com/gtm.js',html)
