"""Synthetic full catalogue candidate, no API key or live publication."""
import json
from pathlib import Path
import tempfile
import unittest

from tools import delivery_candidate as candidate


def html(body='', canonical=''):
    return ('<html><head><meta name="robots" content="noindex">'+canonical+
            '</head><body>'+body+'</body></html>')


def write(root, name, body):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding='utf-8')


def fixture(root):
    write(root, 'index.html', html('<a href="/p/old/">Old</a><a href="/p/new/">New</a>'))
    for slug in ('old', 'new'):
        write(root, f'p/{slug}/index.html', html(
            '<img src="https://images.example/verified.webp" alt="Product">'
            '<a href="/k/grips/">Grips</a>'
            '<a href="/go/tgt_01ARZ3NDEKTSV4RRFFQ69G5FAV" rel="sponsored nofollow">Shop</a>'))
    write(root, 'k/grips/index.html', html('<a href="/p/old/">Old</a><a href="/p/new/">New</a>'))
    write(root, 'sok/index.html', html('Search'))
    write(root, 'beta/index.html', html('Unchanged design fixture'))
    write(root, 'search-index.json', json.dumps([
        {'name': name, 'url': f'/p/{name}/', 'price': '119 kr'} for name in ('old', 'new')]))


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def test_default_keeps_noindex_and_empty_sitemap(self):
        result = candidate.prepare(self.root)
        self.assertEqual(result['product_routes'], ['/p/new/', '/p/old/'])
        self.assertFalse(result['publication_authorized'])
        self.assertIn('noindex', (self.root/'p/new/index.html').read_text())
        self.assertNotIn('<url>', (self.root/'sitemap.xml').read_text())
        self.assertIn('Disallow: /\n', (self.root/'robots.txt').read_text())

    def test_explicit_public_candidate_indexes_catalogue_only(self):
        beta = (self.root/'beta/index.html').read_bytes()
        search = (self.root/'sok/index.html').read_bytes()
        result = candidate.prepare(self.root, indexable=True)
        text = (self.root/'p/new/index.html').read_text()
        self.assertIn('content="index,follow"', text)
        self.assertIn('href="https://sjekkpris.no/p/new/"', text)
        self.assertIn('https://sjekkpris.no/go/tgt_', text)
        sitemap = (self.root/'sitemap.xml').read_text()
        self.assertEqual(sitemap.count('<url>'), 3)
        self.assertNotIn('/sok/', sitemap)
        self.assertNotIn('/beta/', sitemap)
        self.assertEqual(beta, (self.root/'beta/index.html').read_bytes())
        self.assertEqual(search, (self.root/'sok/index.html').read_bytes())
        self.assertIsNone(result['published'])

    def test_existing_namespace_url_preserved(self):
        # No blanket rename from deployed namespace paths to new Core paths.
        old = self.root/'p/old'
        target = self.root/'p/legacy/old'
        target.parent.mkdir()
        old.rename(target)
        for path in (self.root/'search-index.json', self.root/'k/grips/index.html', self.root/'index.html'):
            path.write_text(path.read_text().replace('/p/old/', '/p/legacy/old/'))
        result = candidate.prepare(self.root, indexable=True)
        self.assertIn('/p/legacy/old/', result['product_routes'])

    def test_product_must_be_in_search_and_category(self):
        write(self.root, 'search-index.json', '[]')
        with self.assertRaisesRegex(ValueError, 'search'):
            candidate.prepare(self.root)
        fixture(self.root)
        write(self.root, 'k/grips/index.html', html('<a href="/p/old/">Old</a>'))
        with self.assertRaisesRegex(ValueError, 'category'):
            candidate.prepare(self.root)

    def test_canonical_conflict_never_repaired(self):
        path = self.root/'p/new/index.html'
        path.write_text(path.read_text().replace('</head>',
            '<link rel="canonical" href="https://other.example/p/new/"></head>'))
        with self.assertRaisesRegex(ValueError, 'canonical'):
            candidate.prepare(self.root, indexable=True)

    def test_bad_clickout_refused(self):
        path = self.root/'p/new/index.html'
        path.write_text(path.read_text().replace('href="/go/', 'href="https://other.example/go/'))
        with self.assertRaisesRegex(ValueError, 'clickout'):
            candidate.prepare(self.root)

    def test_output_leak_guard_reused(self):
        write(self.root, 'unsafe.txt', 'apk_synthetic')
        with self.assertRaisesRegex(ValueError, 'safety'):
            candidate.prepare(self.root)

    def test_missing_old_url_or_changed_design_refuses(self):
        old = {'files': [{'path': 'p/old/index.html', 'sha256': 'a'},
                         {'path': 'style.css', 'sha256': 'b'}]}
        with self.assertRaisesRegex(ValueError, 'missing'):
            candidate.preservation(old, {'files': [old['files'][1]]})
        new = {'files': [old['files'][0], {'path': 'style.css', 'sha256': 'c'}]}
        with self.assertRaisesRegex(ValueError, 'design'):
            candidate.preservation(old, new)

    def test_empty_category_is_private_and_not_in_sitemap(self):
        write(self.root, 'k/empty/index.html', html('<h1>Empty</h1>'))
        report = candidate.prepare(self.root, indexable=True)
        self.assertNotIn('/k/empty/', report['category_routes'])
        self.assertIn('noindex', (self.root/'k/empty/index.html').read_text('utf-8'))
        self.assertNotIn('/k/empty/', (self.root/'sitemap.xml').read_text('utf-8'))

    def test_private_banner_preserved_by_default_and_removed_from_public_copy(self):
        for name in ('index.html', 'p/new/index.html', 'k/grips/index.html'):
            path = self.root/name
            path.write_text(path.read_text('utf-8').replace('<body>', '<body>'+candidate.PRIVATE_BANNER), 'utf-8')
        candidate.prepare(self.root)
        self.assertIn(candidate.PRIVATE_BANNER, (self.root/'index.html').read_text('utf-8'))
        candidate.prepare(self.root, indexable=True)
        for name in ('index.html', 'p/new/index.html', 'k/grips/index.html'):
            self.assertNotIn(candidate.PRIVATE_BANNER, (self.root/name).read_text('utf-8'))

    def test_unknown_private_decoration_refuses_public_candidate(self):
        path = self.root/'index.html'
        path.write_text(html(candidate.PRIVATE_BANNER.replace('readinessbygg', 'readinessbygg v2')), 'utf-8')
        with self.assertRaisesRegex(ValueError, 'private presentation'):
            candidate.prepare(self.root, indexable=True)

    def test_broken_links_on_preserved_pages_are_rejected(self):
        for link in ('/p/missing/', 'https://sjekkpris.no/p/missing/', '../p/missing/'):
            with self.subTest(link=link):
                write(self.root, 'about/index.html', html('<a href="'+link+'">Missing</a>'))
                with self.assertRaisesRegex(ValueError, 'internal link'):
                    candidate.prepare(self.root)

    def test_retirement_bound_to_baseline_scope_and_exact_product_files(self):
        row = {'path': 'p/test/index.html', 'sha256': 'a', 'bytes': 1}
        protected = {'path': 'about/index.html', 'sha256': 'b', 'bytes': 1}
        baseline = {'scope': ['sjekkpris-no', 'test'], 'tree_sha256': 'c'*64,
                    'files': [row, protected]}
        new = dict(baseline, files=[protected])
        plan = {'version': 'sjekkpris.test-catalogue-retirement.v1',
                'scope': baseline['scope'], 'baseline_tree_sha256': 'c'*64, 'files': [row]}
        candidate.preservation(baseline, new, plan)
        for changed in (dict(plan, scope=['other', 'test']),
                        dict(plan, baseline_tree_sha256='d'*64),
                        dict(plan, files=[dict(row, sha256='wrong')]),
                        dict(plan, files=[protected]), dict(plan, files=[row, row])):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                candidate.preservation(baseline, new, changed)
        with self.assertRaisesRegex(ValueError, 'remains'):
            candidate.preservation(baseline, baseline, plan)
        with self.assertRaisesRegex(ValueError, 'design'):
            candidate.preservation(baseline, dict(new, files=[dict(protected, sha256='changed')]), plan)

    def test_retired_product_cannot_survive_in_search_or_preserved_links(self):
        (self.root/'p/old/index.html').unlink()
        with self.assertRaisesRegex(ValueError, 'search'):
            candidate.prepare(self.root, indexable=True)
        write(self.root, 'search-index.json', json.dumps([{'url': '/p/new/'}]))
        write(self.root, 'k/grips/index.html', html('<a href="/p/new/">New</a>'))
        with self.assertRaisesRegex(ValueError, 'internal link'):
            candidate.prepare(self.root, indexable=True)
        write(self.root, 'index.html', html('<a href="/p/new/">New</a>'))
        report = candidate.prepare(self.root, indexable=True)
        self.assertEqual(report['product_routes'], ['/p/new/'])
        self.assertNotIn('/p/old/', (self.root/'sitemap.xml').read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()
