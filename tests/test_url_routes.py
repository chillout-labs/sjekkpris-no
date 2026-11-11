"""ADR-039 synthetic canonical identities; never production allocation evidence."""
import copy
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

import build
import check_output
from category_catalog import category_index, category_links
from tools.check_design_links import check
from url_routes import RouteRegistry, RouteError, descriptive_slug, entity_path, validate_readiness
from test_build import INDEX, COMPARISONS


def snapshot():
    return {'version': 1, 'property': 'sjekkpris-no', 'revision': 'synthetic-1',
        'entities': [
            {'kind': 'product', 'entity_id': 'prd_FIXTURE', 'slug': 'nord-pro-plus-256-gb', 'state': 'active'},
            {'kind': 'product', 'entity_id': 'prd_FIXTURE2', 'slug': 'nord-pro-plus-512-gb', 'state': 'active'},
            {'kind': 'category', 'entity_id': 'root', 'slug': 'elektronikk', 'state': 'active'},
            {'kind': 'category', 'entity_id': 'leaf', 'slug': 'telefoner', 'state': 'active'},
        ], 'aliases': [
            {'source': '/kategori/mobiltelefoner/', 'kind': 'category', 'entity_id': 'leaf', 'status': 301, 'evidence': 'Synthetic reviewed category identity'},
            {'source': '/produkt/old-phone/', 'kind': 'product', 'entity_id': 'prd_FIXTURE', 'status': 301, 'evidence': 'Synthetic verified same entity'},
            {'source': '/p/catalogue/fixture-lamp/', 'kind': 'product', 'entity_id': 'prd_FIXTURE', 'status': 308, 'evidence': 'Synthetic reviewed beta product URL'},
            {'source': '/p/catalogue/fixture-empty/', 'kind': 'product', 'entity_id': 'prd_FIXTURE2', 'status': 308, 'evidence': 'Synthetic reviewed beta product URL'},
            {'source': '/Shopping/gone.aspx', 'status': 410, 'evidence': 'Synthetic known removal'},
            {'source': '/never-existed.aspx', 'status': 404, 'evidence': 'Synthetic no successor'},
        ]}


class FixtureClient:
    def __init__(self, products=None, comparisons=None):
        self.products = copy.deepcopy(products if products is not None else INDEX['products'])
        self.comparisons = copy.deepcopy(comparisons if comparisons is not None else COMPARISONS)
        self.paths = []
        self.property_id = 'sjekkpris-no'

    def get(self, path):
        self.paths.append(path)
        if path.split('?')[0].endswith('/catalogue'):
            return {'property_id': self.property_id, 'products': self.products}
        return self.comparisons[path.split('/')[-2]]


class Signals(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.canonicals = []
        self.noindex = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs['href'])
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.noindex = 'noindex' in attrs.get('content', '')


class RegistryTests(unittest.TestCase):
    def test_normalization_preserves_distinguishing_tokens_without_length_cap(self):
        self.assertEqual(descriptive_slug('Nørd Pro+ Ultra XL 65" 2026 256 GB 6-pakning'),
            'nord-pro-plus-ultra-xl-65-2026-256-gb-6-pakning')
        self.assertGreater(len(descriptive_slug('Long verified model ' * 20)), 100)
        self.assertEqual(entity_path('brand', 'nord'), '/merke/nord/')
        self.assertEqual(entity_path('guide', 'velg-tv'), '/guide/velg-tv/')

    def test_duplicate_slugs_and_duplicate_identity_fail(self):
        for field, value in [('slug', 'nord-pro-plus-256-gb'), ('entity_id', 'prd_FIXTURE')]:
            data = snapshot()
            data['entities'][1][field] = value
            with self.assertRaises(RouteError):
                RouteRegistry(data)

    def test_verified_disambiguator_or_public_suffix_is_explicit(self):
        data = snapshot()
        data['entities'][1]['slug'] = 'nord-pro-plus-256-gb-p7k42'
        registry = RouteRegistry(data)
        self.assertNotEqual(registry.path('product', 'prd_FIXTURE'), registry.path('product', 'prd_FIXTURE2'))
        data['entities'][1]['slug'] = 'p7k42'
        self.assertEqual(RouteRegistry(data).path('product', 'prd_FIXTURE2'), '/p/p7k42/')

    def test_namespace_slug_and_title_never_define_canonical_identity(self):
        registry = RouteRegistry(snapshot())
        product = copy.deepcopy(INDEX['products'][0])
        product['local_name'] = 'A completely corrected title'
        product['local_slug'] = 'different-upstream-alias'
        self.assertEqual(registry.bind_product(product, COMPARISONS['fixture-lamp'])['_public_path'], '/p/nord-pro-plus-256-gb/')
        with self.assertRaises(RouteError):
            registry.bind_product(product, {'identity': {'local_name': product['local_name']}})
        product['product_id'] = 'wrong'
        with self.assertRaises(RouteError):
            registry.bind_product(product, COMPARISONS['fixture-lamp'])

    def test_freeze_and_permanent_reservations_across_snapshots(self):
        data = snapshot()
        data['revision'] = 'synthetic-2'
        RouteRegistry(data, snapshot())
        for change in ('rename', 'delete', 'recycle'):
            changed = copy.deepcopy(data)
            if change == 'rename': changed['entities'][0]['slug'] = 'new-name'
            if change == 'delete': changed['entities'].pop(0)
            if change == 'recycle': changed['entities'][0]['entity_id'] = 'another'
            with self.assertRaises(RouteError): RouteRegistry(changed, snapshot())
        reserved = copy.deepcopy(data)
        reserved['entities'][1]['state'] = 'reserved'
        reserved['aliases'].append({'source': '/p/nord-pro-plus-512-gb/', 'status': 410, 'evidence': 'Synthetic intentional removal'})
        registry = RouteRegistry(reserved, snapshot())
        with self.assertRaises(RouteError): registry.path('product', 'prd_FIXTURE2')

    def test_reviewed_rename_and_merge_keep_historical_ownership(self):
        data = snapshot()
        old = copy.deepcopy(data['entities'][0])
        data['entities'][0]['slug'] = 'corrected-model'
        data['reservations'] = [old]
        data['aliases'].append({'source': '/p/nord-pro-plus-256-gb/', 'kind': 'product', 'entity_id': 'prd_FIXTURE',
            'status': 301, 'evidence': 'Synthetic approved correction'})
        registry = RouteRegistry(data, snapshot())
        self.assertEqual(registry.owners['/p/nord-pro-plus-256-gb/'], ('product', 'prd_FIXTURE'))
        self.assertEqual(registry.path('product', 'prd_FIXTURE'), '/p/corrected-model/')
        merged = snapshot()
        merged['entities'][1]['state'] = 'reserved'
        merged['aliases'].append({'source': '/p/nord-pro-plus-512-gb/', 'kind': 'product', 'entity_id': 'prd_FIXTURE',
            'status': 301, 'evidence': 'Synthetic proven duplicate merge'})
        RouteRegistry(merged, snapshot())

    def test_successive_merges_flatten_all_historical_aliases(self):
        first = snapshot()
        first['entities'][0]['state'] = 'reserved'
        first['aliases'].append({'source': '/p/nord-pro-plus-256-gb/', 'kind': 'product', 'entity_id': 'prd_FIXTURE2',
            'status': 301, 'evidence': 'Synthetic first reviewed merge'})
        RouteRegistry(first, snapshot())
        second = copy.deepcopy(first)
        second['revision'] = 'synthetic-2'
        second['entities'][1]['state'] = 'reserved'
        second['entities'].append({'kind': 'product', 'entity_id': 'prd_SURVIVOR', 'slug': 'surviving-model', 'state': 'active'})
        second['aliases'].append({'source': '/p/nord-pro-plus-512-gb/', 'kind': 'product', 'entity_id': 'prd_SURVIVOR',
            'status': 301, 'evidence': 'Synthetic second reviewed merge'})
        registry = RouteRegistry(second, first)
        rules = registry.redirect_plan({'/p/surviving-model/', '/k/telefoner/'})
        for rule in rules:
            if rule['source'].startswith(('/produkt/', '/p/nord-')):
                self.assertEqual(rule['target'], '/p/surviving-model/')
        second['entities'][-1]['state'] = 'reserved'
        second['aliases'].append({'source': '/p/surviving-model/', 'kind': 'product', 'entity_id': 'prd_FIXTURE',
            'status': 301, 'evidence': 'Synthetic bad circular merge'})
        with self.assertRaisesRegex(RouteError, 'cycle'):
            RouteRegistry(second)

    def test_snapshot_input_mutation_cannot_change_validated_routes(self):
        data = snapshot()
        registry = RouteRegistry(data)
        data['entities'][0]['slug'] = 'changed-after-validation'
        data['aliases'][1]['entity_id'] = 'wrong'
        self.assertEqual(registry.path('product', 'prd_FIXTURE'), '/p/nord-pro-plus-256-gb/')
        self.assertEqual(registry.aliases['/produkt/old-phone/']['entity_id'], 'prd_FIXTURE')

    def test_offers_property_and_requested_alias_must_match(self):
        registry = RouteRegistry(snapshot())
        for supplied in (None, 'another-property'):
            body = dict(COMPARISONS['fixture-lamp'], property_id=supplied)
            with self.assertRaisesRegex(RouteError, 'Property'):
                registry.bind_product(INDEX['products'][0], body)
        for field in ('namespace', 'local_slug'):
            body = copy.deepcopy(COMPARISONS['fixture-lamp'])
            body['identity'][field] = 'another-catalogue-alias'
            with self.assertRaisesRegex(RouteError, 'requested catalogue alias'):
                registry.bind_product(INDEX['products'][0], body)

    def test_retirement_without_reviewed_disposition_fails(self):
        data = snapshot(); data['entities'][1]['state'] = 'reserved'
        with self.assertRaises(RouteError): RouteRegistry(data, snapshot())

    def test_historical_equivalent_aliases_follow_reviewed_terminal_gone_status(self):
        data = snapshot()
        data['entities'][0]['state'] = 'reserved'
        data['aliases'].append({'source': '/p/nord-pro-plus-256-gb/', 'status': 410, 'evidence': 'Synthetic known removal without replacement'})
        registry = RouteRegistry(data, snapshot())
        rules = {r['source']: r for r in registry.redirect_plan({'/p/nord-pro-plus-512-gb/', '/k/telefoner/'})}
        for source in ('/produkt/old-phone/', '/produkt/old-phone', '/p/catalogue/fixture-lamp/', '/p/nord-pro-plus-256-gb/'):
            self.assertEqual(rules[source]['status'], 410)
            self.assertNotIn('target', rules[source])

    def test_parallel_readers_agree_and_conflicting_snapshot_is_rejected(self):
        # Read-only consumers; atomic allocation is a documented API dependency.
        with ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(lambda _: RouteRegistry(snapshot()).path('product', 'prd_FIXTURE'), range(32)))
        self.assertEqual(len(set(paths)), 1)
        conflicting = snapshot()
        conflicting['entities'].append(dict(conflicting['entities'][0], entity_id='new-canonical'))
        with self.assertRaises(RouteError): RouteRegistry(conflicting)

    def test_invalid_aliases_chains_loops_and_recycling_fail(self):
        for source in ('//evil.test/', '/../outside/', '/p/nord-pro-plus-256-gb/', '/a?b=1', '/a%2fb', '/a\\b', '/a?', '/a#', '/a//b/'):
            data = snapshot(); data['aliases'][0]['source'] = source
            with self.assertRaises(RouteError): RouteRegistry(data)
        data = snapshot(); data['aliases'][0]['entity_id'] = 'missing'
        with self.assertRaises(RouteError): RouteRegistry(data)
        data = snapshot(); data['aliases'][0]['evidence'] = ''
        with self.assertRaises(RouteError): RouteRegistry(data)
        data = snapshot(); data['aliases'].pop()
        with self.assertRaises(RouteError): RouteRegistry(data, snapshot())

    def test_version_property_and_route_syntax(self):
        for field, value in [('version', 2), ('property', 'another'), ('revision', '')]:
            data = snapshot(); data[field] = value
            with self.assertRaises(RouteError): RouteRegistry(data)
        for slug in ('Name', '../a', 'a/b', 'a--b', 'a_b', ''):
            with self.assertRaises(RouteError): entity_path('product', slug)


class ReadinessBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / 'site'
        self.client = FixtureClient()
        self.client.products[0]['categories'] = {'primary': {'id': 'leaf', 'display_name': 'Mobiltelefoner',
            'path': [{'id': 'root', 'display_name': 'Elektronikk'}, {'id': 'leaf', 'display_name': 'Mobiltelefoner'}]}}

    def run_build(self, base='/'):
        return build.build(self.client, self.out, base=base, noindex=True, routes=RouteRegistry(snapshot()))

    def test_end_to_end_routes_links_search_canonical_and_noindex(self):
        for base in ('/', '/preview/'):
            self.assertEqual(self.run_build(base), 2)
            for file in self.out.rglob('*.html'):
                signal = Signals(file.read_text(encoding='utf-8'))
                self.assertTrue(signal.noindex, file)
                if file.name != '404.html':
                    path = file.relative_to(self.out).as_posix().removesuffix('index.html')
                    self.assertEqual(signal.canonicals, ['https://sjekkpris.no' + base + path])
            self.assertTrue((self.out / 'p/nord-pro-plus-256-gb/index.html').is_file())
            self.assertTrue((self.out / 'k/telefoner/index.html').is_file())
            self.assertTrue((self.out / 'k/elektronikk/index.html').is_file())
            self.assertFalse((self.out / 'p/catalogue').exists())
            self.assertFalse((self.out / 'search').exists())
            index = json.loads((self.out / 'search-index.json').read_text())
            self.assertEqual(index[0]['url'], base + 'p/nord-pro-plus-256-gb/')
            self.assertNotIn('<loc>', (self.out / 'sitemap.xml').read_text())
            # Existing comprehensive local-link gate, including JSON search paths.
            root = self.out
            if base != '/':
                import shutil
                root = Path(self.tmp.name) / 'host'
                shutil.copytree(self.out, root / base.strip('/'), dirs_exist_ok=True)
            self.assertEqual(check(root, base), [])
            self.assertEqual(check_output.check(self.out), [])

    def test_one_product_activates_complete_supplied_ancestry(self):
        self.client.products = self.client.products[:1]
        data = snapshot()
        data['aliases'] = [a for a in data['aliases'] if a.get('entity_id') != 'prd_FIXTURE2']
        build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))
        for slug in ('telefoner', 'elektronikk'):
            text = (self.out / f'k/{slug}/index.html').read_text(encoding='utf-8')
            self.assertIn('/p/nord-pro-plus-256-gb/', text)
        nodes = category_index(self.client.products, registry=RouteRegistry(snapshot()))
        self.assertEqual(len(nodes['root']['products']), 1)
        self.assertEqual(category_links(self.client.products[0], nodes, '/')[-1][1], '/k/telefoner/')

    def test_one_product_activates_primary_and_additional_paths_but_not_empty_branches(self):
        self.client.products = self.client.products[:1]
        self.client.products[0]['categories']['additional'] = [{'id': 'other', 'display_name': 'Tilbehør',
            'path': [{'id': 'root', 'display_name': 'Elektronikk'}, {'id': 'other', 'display_name': 'Tilbehør'}]}]
        data = snapshot()
        data['aliases'] = [a for a in data['aliases'] if a.get('entity_id') != 'prd_FIXTURE2']
        data['entities'].extend([
            {'kind': 'category', 'entity_id': 'other', 'slug': 'tilbehor', 'state': 'active'},
            {'kind': 'category', 'entity_id': 'empty', 'slug': 'tom-gren', 'state': 'active'}])
        build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))
        for slug in ('elektronikk', 'telefoner', 'tilbehor'):
            self.assertTrue((self.out / f'k/{slug}/index.html').exists())
        self.assertFalse((self.out / 'k/tom-gren').exists())

    def test_rename_and_taxonomy_move_preserve_frozen_url(self):
        self.run_build()
        self.client.products[0]['local_name'] = 'Corrected model name'
        self.client.products[0]['categories']['primary']['path'] = []
        self.run_build()
        self.assertTrue((self.out / 'p/nord-pro-plus-256-gb/index.html').exists())
        self.assertTrue((self.out / 'k/telefoner/index.html').exists())

    def test_variants_follow_canonical_ids_even_when_titles_are_identical(self):
        for product in self.client.products:
            product['local_name'] = 'Identical provider presentation'
        self.run_build()
        self.assertTrue((self.out / 'p/nord-pro-plus-256-gb/index.html').exists())
        self.assertTrue((self.out / 'p/nord-pro-plus-512-gb/index.html').exists())
        # Frontend must never coalesce two aliases of one entity into two pages.
        self.client.comparisons['fixture-empty']['product_id'] = 'prd_FIXTURE'
        with self.assertRaises(RouteError): self.run_build()

    def test_missing_canonical_or_category_route_fails_closed(self):
        del self.client.comparisons['fixture-lamp']['product_id']
        with self.assertRaises(RouteError): self.run_build()
        self.client = FixtureClient()
        data = snapshot(); data['entities'].pop(0)
        with self.assertRaises(RouteError):
            build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))

    def test_indexing_cannot_be_enabled_by_readiness_input(self):
        with self.assertRaises(build.BuildError):
            build.build(self.client, self.out, base='/', noindex=False, routes=RouteRegistry(snapshot()))

    def test_edge_plan_is_one_hop_exact_target_and_outside_served_artifact(self):
        self.run_build()
        plan = json.loads(self.out.with_name('site.redirects.json').read_text())
        rules = {r['source']: r for r in plan}
        self.assertEqual(len(plan), len(rules))
        self.assertEqual(rules['/p/catalogue/fixture-lamp/']['target'], '/p/nord-pro-plus-256-gb/')
        self.assertEqual(rules['/kategori/mobiltelefoner/']['target'], '/k/telefoner/')
        self.assertEqual(rules['/kategori/mobiltelefoner']['target'], '/k/telefoner/')
        self.assertEqual(rules['/p/catalogue/fixture-lamp']['target'], '/p/nord-pro-plus-256-gb/')
        self.assertEqual(rules['/produkt/old-phone']['target'], '/p/nord-pro-plus-256-gb/')
        self.assertEqual(rules['/p/nord-pro-plus-256-gb']['status'], 308)
        self.assertEqual(rules['/Shopping/gone.aspx']['status'], 410)
        self.assertEqual(rules['/never-existed.aspx']['status'], 404)
        for rule in plan:
            if 'target' in rule:
                self.assertNotIn(rule['target'], rules)
                self.assertTrue((self.out / rule['target'].strip('/') / 'index.html').is_file())
                self.assertNotEqual(rule['target'], '/')
        self.assertFalse((self.out / 'site.redirects.json').exists())
        self.assertEqual(len([p for p in self.client.paths if '/offers?' in p]), 2)

    def test_redirect_to_unbuilt_brand_or_guide_fails(self):
        data = snapshot()
        data['entities'].append({'kind': 'guide', 'entity_id': 'guide-1', 'slug': 'guide', 'state': 'active'})
        data['aliases'].append({'source': '/old-guide/', 'kind': 'guide', 'entity_id': 'guide-1', 'status': 301, 'evidence': 'fixture'})
        with self.assertRaises(RouteError):
            build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))

    def test_output_gate_rejects_bad_canonical_noindex_and_internal_links(self):
        for old, new in [
            ('rel="canonical"', 'rel="alternate"'),
            ('content="noindex"', 'content="index"'),
            ('href="/sok/"', 'href="/missing/"'),
            ('href="/sok/"', 'href="/sok"'),
            ('href="#main"', 'href="#missing"'),
        ]:
            self.run_build()
            path = self.out / 'index.html'
            text = path.read_text(encoding='utf-8')
            self.assertIn(old, text)
            path.write_text(text.replace(old, new), encoding='utf-8')
            with self.assertRaises(RouteError): validate_readiness(self.out, '/')

    def test_missing_category_and_cyclic_ancestry_fail(self):
        data = snapshot(); data['entities'] = [e for e in data['entities'] if e['entity_id'] != 'root']
        with self.assertRaises(RouteError):
            build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))
        primary = self.client.products[0]['categories']['primary']
        primary['path'].append(primary['path'][0])
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            category_index(self.client.products)

    def test_current_category_label_does_not_invent_historical_redirect(self):
        primary = self.client.products[0]['categories']['primary']
        primary['display_name'] = primary['path'][-1]['display_name'] = 'Nytt kategorinavn'
        self.run_build()
        rules = {r['source']: r for r in json.loads(self.out.with_name('site.redirects.json').read_text())}
        self.assertNotIn('/kategori/nytt-kategorinavn/', rules)
        self.assertEqual(rules['/kategori/mobiltelefoner/']['target'], '/k/telefoner/')
        self.assertTrue((self.out / 'k/telefoner/index.html').exists())

    def test_failed_rebuild_removes_previous_redirect_plan(self):
        self.run_build()
        plan = self.out.with_name('site.redirects.json')
        self.assertTrue(plan.exists())
        del self.client.comparisons['fixture-lamp']['product_id']
        with self.assertRaises(RouteError): self.run_build()
        self.assertFalse(plan.exists())

    def test_missing_reviewed_beta_alias_fails_instead_of_guessing_migration(self):
        data = snapshot()
        data['aliases'] = [a for a in data['aliases'] if a['source'] != '/p/catalogue/fixture-lamp/']
        with self.assertRaisesRegex(RouteError, 'reviewed registry alias'):
            build.build(self.client, self.out, base='/', noindex=True, routes=RouteRegistry(data))

    def test_wrong_or_missing_catalogue_property_fails(self):
        for value in (None, 'another-property'):
            self.client.property_id = value
            with self.assertRaisesRegex(RouteError, 'Catalogue response'):
                self.run_build()

    def test_noindex_sitemap_gate_rejects_entries_and_malformed_xml(self):
        self.run_build()
        for content in ('<not-xml', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://sjekkpris.no/</loc></url></urlset>'):
            (self.out / 'sitemap.xml').write_text(content, encoding='utf-8')
            with self.assertRaises(RouteError): validate_readiness(self.out, '/')
