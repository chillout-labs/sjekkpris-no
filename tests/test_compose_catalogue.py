"""Synthetic website selection; shared verifier has its own pinned Core tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compose_catalogue import compose, catalogue
from delivery_candidate import prepare, preservation
from test_delivery_candidate import fixture, html, write


class VerifiedInventory:
    @staticmethod
    def inventory(root, scope, release):
        files = [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size,
                      sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in sorted(root.rglob('*')) if p.is_file()]
        return dict(scope=list(scope), files=files,
                    tree_sha256=hashlib.sha256(json.dumps(files).encode()).hexdigest())


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new, self.out = [self.root / n for n in ('old', 'new', 'out')]
        self.old.mkdir(); self.new.mkdir()
        fixture(self.new)
        write(self.new, 'k/index.html', html('<a href="/k/grips/">Grips</a>'))
        write(self.old, 'index.html', html('Old catalogue'))
        write(self.old, 'p/test/index.html', html('Retired'))
        write(self.old, 'search-index.json', '[{"url":"/p/test/"}]')
        write(self.old, 'search/index.html', html('Old search'))
        write(self.old, 'kategori/test/index.html', html('<a href="/p/test/">Test</a>'))
        write(self.old, 'beta/index.html', html('Published beta ' + 'unchanged'))
        write(self.old, 'about/index.html', html('<a href="/kategori/test/">Catalogue</a>'))
        write(self.old, 'style.css', 'original design')
        write(self.new, 'style.css', 'private different unused alias')
        self.scope = ('sjekkpris-no', 'test')
        self.base = VerifiedInventory.inventory(self.old, self.scope, '')
        self.retire = dict(version='sjekkpris.test-catalogue-retirement.v1', scope=list(self.scope),
                           baseline_tree_sha256=self.base['tree_sha256'],
                           files=[f for f in self.base['files'] if f['path'].startswith('p/')])

    def run_composition(self):
        return compose(VerifiedInventory, self.base, self.old, self.new, self.out,
                       self.scope, self.retire)

    def test_catalogue_replaced_beta_and_other_files_preserved(self):
        aliases = self.run_composition()
        mutable = {p.relative_to(self.out).as_posix() for p in self.out.rglob('*.html')
                   if catalogue(p.relative_to(self.out).as_posix())} | aliases
        result = prepare(self.out, indexable=True, navigation_aliases=aliases, mutable_pages=mutable)
        preservation(self.base, VerifiedInventory.inventory(self.out, self.scope, ''),
                     self.retire, navigation_aliases=aliases)
        for name in ('beta/index.html', 'about/index.html', 'style.css'):
            self.assertEqual((self.old/name).read_bytes(), (self.out/name).read_bytes())
        self.assertEqual(result['product_routes'], ['/p/new/', '/p/old/'])
        self.assertFalse((self.out/'p/test/index.html').exists())
        for name in ('search-index.json', 'kategori/test/index.html', 'sitemap.xml'):
            self.assertNotIn('/p/test/', (self.out/name).read_text())
        self.assertIn('noindex', (self.out/'kategori/test/index.html').read_text())
        self.assertNotIn('/kategori/test/', (self.out/'sitemap.xml').read_text())
        self.assertEqual((self.new/'sok/index.html').read_bytes(), (self.out/'search/index.html').read_bytes())

    def test_preserved_beta_link_to_retired_product_blocks_candidate(self):
        write(self.old, 'beta/index.html', html('<a href="/p/test/">Old design link</a>'))
        self.base = VerifiedInventory.inventory(self.old, self.scope, '')
        self.retire['baseline_tree_sha256'] = self.base['tree_sha256']
        aliases = self.run_composition()
        with self.assertRaisesRegex(ValueError, 'broken internal link'):
            prepare(self.out, navigation_aliases=aliases)
        self.assertEqual((self.old/'beta/index.html').read_bytes(),
                         (self.out/'beta/index.html').read_bytes())

    def test_tampered_baseline_refused_before_output(self):
        write(self.old, 'style.css', 'tampered')
        with self.assertRaisesRegex(ValueError, 'baseline content'):
            self.run_composition()
        self.assertFalse(self.out.exists())

    def test_unapproved_product_removal_refused(self):
        self.retire = None
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.run_composition()
        self.assertFalse(self.out.exists())

    def test_used_conflicting_asset_refused(self):
        write(self.new, 'index.html', html('<link href="/style.css">'))
        with self.assertRaisesRegex(ValueError, 'protected asset'):
            self.run_composition()
        self.assertFalse(self.out.exists())

    def test_unrelated_received_page_refused(self):
        write(self.new, 'unrequested/index.html', html('Unexpected'))
        with self.assertRaisesRegex(ValueError, 'unexpected received page'):
            self.run_composition()

    def test_missing_catalogue_surface_refused(self):
        (self.new/'sok/index.html').unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.run_composition()

    def test_second_product_group_uses_same_composition_without_retirement(self):
        fixture(self.old)
        (self.old/'p/test/index.html').unlink()
        self.base = VerifiedInventory.inventory(self.old, self.scope, '')
        self.retire = None
        write(self.new, 'p/third/index.html', html('<img src="https://images.example/third.webp">'))
        write(self.new, 'search-index.json', json.dumps([{'url': '/p/'+p+'/'} for p in ('old','new','third')]))
        write(self.new, 'k/grips/index.html', html(''.join('<a href="/p/'+p+'/">Product</a>' for p in ('old','new','third'))))
        aliases = self.run_composition()
        self.assertEqual(len(prepare(self.out, navigation_aliases=aliases)['product_routes']), 3)


if __name__ == '__main__':
    unittest.main()
