"""Public projection repeats only its displayed image in Product JSON-LD."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_output import check

ORIGIN = 'https://chillout.example.invalid'
IMAGE = ORIGIN + '/images/' + 'x' * 43


class PublicationImageOutputTest(unittest.TestCase):
    def check_page(self, document, *, image=IMAGE, attrs='type="application/ld+json"', suffix=''):
        raw = document if isinstance(document, str) else json.dumps(document)
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {'CHILLOUT_ORIGIN': ORIGIN}):
            root = Path(temporary)
            (root / 'index.html').write_text(
                f'<script {attrs}>{raw}</script><img src="{image}">' + suffix,
                encoding='utf-8')
            return check(root)

    def product(self, **extra):
        return {'@context': 'https://schema.org', '@type': 'Product', 'image': IMAGE, **extra}

    def test_same_displayed_public_image_is_allowed(self):
        self.assertEqual(self.check_page(self.product()), [])

    def test_other_fields_remain_checked(self):
        for field in ('url', 'description', 'offers'):
            with self.subTest(field=field):
                self.assertTrue(self.check_page(self.product(**{field: IMAGE})))

    def test_private_ids_and_credentials_still_checked_in_original_text(self):
        for secret in ('apk_synthetic', 'prd_synthetic'):
            self.assertTrue(self.check_page(self.product(name=secret)))

    def test_unshown_or_invalid_image_refuses(self):
        self.assertTrue(self.check_page(self.product(), image='/local.jpg'))
        self.assertTrue(self.check_page(self.product(image=ORIGIN + '/api/private')))
        self.assertTrue(self.check_page(self.product(image=IMAGE + '?token=synthetic')))

    def test_only_exact_product_document_and_script_type(self):
        for document in (self.product(**{'@type': 'Thing'}),
                         self.product(**{'@context': 'https://example.invalid'}),
                         [self.product()]):
            self.assertTrue(self.check_page(document))
        for attrs in ('type="text/javascript"', 'type="application/ld+json" src="/code.js"'):
            self.assertTrue(self.check_page(self.product(), attrs=attrs))

    def test_malformed_and_duplicate_json_refuse(self):
        self.assertTrue(self.check_page('{"image":"' + IMAGE + '"'))
        raw = json.dumps(self.product())[:-1] + ',"image":"' + IMAGE + '"}'
        self.assertTrue(self.check_page(raw))

    def test_text_and_later_script_still_refuse(self):
        self.assertTrue(self.check_page(self.product(), suffix=IMAGE))
        self.assertTrue(self.check_page(self.product(), suffix='<script>' + IMAGE + '</script>'))


if __name__ == '__main__':
    unittest.main()
