"""Synthetic public image tokens and product facts; no external requests."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
import check_output
from catalogue_media import category_markup, image_markup, public_image_url
from home_ui import render_home

ORIGIN = "https://chillout.example.invalid"
IMAGE = ORIGIN + "/images/" + "x" * 43
CATEGORY = {"id": "cat_synthetic", "name": "Choppers", "display_name": "Løkhakkere",
            "active": True, "path": [{"name": "Kitchen", "display_name": "Kjøkken"},
                                      {"name": "Choppers", "display_name": "Løkhakkere"}]}


class MediaTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CHILLOUT_ORIGIN": ORIGIN})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_home_and_detail_render_actual_image_variants_brand_and_norwegian_categories(self):
        media = {"url": IMAGE, "variants": [{"width": 108, "url": IMAGE + "?w=108"},
                                            {"width": 360, "url": IMAGE + "?w=360"}]}
        product = {"local_name": 'Synthetic <chopper>', "namespace": "catalogue", "local_slug": "synthetic",
                   "local_brand": 'Brand <x>', "image": media, "categories": {"primary": CATEGORY, "additional": []}}
        home = render_home([product], base="/", money=build.money, day=build.day, segment=build.segment)
        detail = build.product_body(product, {"identity": product, "offers": [], "excluded": []}, base="/")
        for html in (home, detail):
            self.assertIn('src="' + IMAGE + '"', html)
            self.assertIn('?w=108 108w,', html)
            self.assertIn('Løkhakkere', html)
            self.assertIn('Brand &lt;x&gt;', html)
            self.assertNotIn('Synthetic <chopper>', html)
        self.assertIn('Kjøkken › Løkhakkere', detail)
        self.assertIn('Ingen tilbud akkurat nå.', detail)

    def test_invalid_image_urls_and_widths_never_become_image_attributes(self):
        for url in ['javascript:alert(1)', 'http://chillout.example.invalid/images/' + 'x'*43,
                    ORIGIN + '/api/v1/catalogue', IMAGE + '?secret=value',
                    'https://user:password@chillout.example.invalid/images/'+'x'*43,
                    'https://foreign.example/images/'+'x'*43, IMAGE+'#fragment']:
            self.assertFalse(public_image_url(url), url)
            self.assertEqual(image_markup({"url": url}, 'name', sizes='100px'), '')
        html = image_markup({"url": IMAGE, "variants": [{"width": -1, "url": IMAGE},
                            {"width": 100, "url": 'javascript:alert(1)'}]}, '" onerror="x', sizes='100px')
        self.assertNotIn('srcset=', html)
        self.assertIn('&quot; onerror=&quot;x', html)

    def test_origin_exception_only_in_image_attributes_and_never_for_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'page.html'
            path.write_text(image_markup({"url": IMAGE}, 'Synthetic', sizes='100px'))
            self.assertEqual(check_output.check(root), [])
            for text in [f"<img onload='let src=\"{IMAGE}\";'>", f'<script>const x = \'<img src="{IMAGE}">\'</script>',
                         f'<img data-src="{IMAGE}">', f'<!-- <img src="{IMAGE}"> -->', IMAGE, f'<a href="{IMAGE}">link</a>', f'<script>"{IMAGE}"</script>',
                         f'<img src="{IMAGE}?apikey=apk_synthetic">',
                         f'<img src="{IMAGE}" alt="apk_synthetic">',
                         f'<img src="{IMAGE}" alt="prd_synthetic">',
                         f'<img srcset="{IMAGE} 100w, {ORIGIN}/api 200w">']:
                path.write_text(text)
                self.assertTrue(check_output.check(root), text)

    def test_image_markup_in_non_html_files_is_not_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for extension in ['json', 'css', 'js']:
                (root / ('leak.' + extension)).write_text(f'<img src="{IMAGE}">')
            self.assertEqual(len(check_output.check(root)), 3)

    def test_missing_and_inactive_category_do_not_invent_classification(self):
        self.assertEqual(category_markup(None), '')
        self.assertEqual(category_markup({"primary": {**CATEGORY, "active": False}}), '')
        html = category_markup({"primary": CATEGORY, "additional": [{"name": '<Other>'}]}, full=True)
        self.assertIn('&lt;Other&gt;', html)


if __name__ == '__main__':
    unittest.main()
