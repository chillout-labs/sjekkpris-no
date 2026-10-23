"""ADR-039 read-only route snapshot consumer. Never allocates canonical identities.

The registry is private build input; only resolved paths may reach public output.
Atomic allocation/publication remains the responsibility of the registry owner.
"""
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
import json
import re
import unicodedata
from urllib.parse import urlsplit, urljoin, unquote

PREFIXES = {'product': 'p', 'category': 'k', 'brand': 'merke', 'guide': 'guide'}
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


class RouteError(ValueError):
    pass


def descriptive_slug(verified_name):
    """Normalization only, not permission to publish a provider title."""
    value = verified_name.lower().replace('+', ' plus ')
    value = value.translate(str.maketrans({'æ': 'ae', 'ø': 'o', 'å': 'a'}))
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def entity_path(kind, slug):
    if kind not in PREFIXES or not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise RouteError('Invalid route kind or frozen slug')
    return f'/{PREFIXES[kind]}/{slug}/'


def product_href(product, base):
    path = product.get('_public_path')
    if path is not None:
        if not re.fullmatch(r'/p/[a-z0-9]+(?:-[a-z0-9]+)*/', path):
            raise RouteError('Invalid resolved product path')
    else:
        path = f'/p/{product["namespace"]}/{product["local_slug"]}/'
    return base + path.lstrip('/')


def local_path(path):
    if not isinstance(path, str):
        raise RouteError('Invalid alias source')
    parts = urlsplit(path)
    if (not path.startswith('/') or path.startswith('//') or parts.scheme or parts.netloc
            or parts.query or parts.fragment or any(c in path for c in ('\\', '%'))
            or any(ord(c) < 33 for c in path)
            or any(p in ('.', '..') for p in path.split('/'))):
        raise RouteError('Invalid alias source')
    return path


class RouteRegistry:
    def __init__(self, snapshot, previous=None):
        if snapshot.get('version') != 1 or snapshot.get('property') != 'sjekkpris-no':
            raise RouteError('Unsupported property route snapshot')
        if not snapshot.get('revision'):
            raise RouteError('Missing route revision')
        self.snapshot = deepcopy(snapshot)
        self.entities, self.owners, self.aliases = {}, {}, {}
        for row in snapshot.get('entities', []):
            key = (row['kind'], row['entity_id'])
            path = entity_path(row['kind'], row['slug'])
            if key in self.entities or path in self.owners:
                raise RouteError('Duplicate identity or slug collision in route snapshot')
            if row.get('state') not in ('active', 'reserved'):
                raise RouteError('Route must be active or permanently reserved')
            self.entities[key] = row
            self.owners[path] = key
        # Historical slugs retain their original owner even after a reviewed
        # correction/merge; reservation and redirect destination are distinct.
        for row in snapshot.get('reservations', []):
            key = (row['kind'], row['entity_id'])
            path = entity_path(row['kind'], row['slug'])
            if path in self.owners:
                raise RouteError('Historical slug collision')
            self.owners[path] = key
        for alias in snapshot.get('aliases', []):
            source = local_path(alias['source'])
            owner = self.owners.get(source)
            owner_row = self.entities.get(owner)
            live_source = owner_row and owner_row['state'] == 'active' and entity_path(owner_row['kind'], owner_row['slug']) == source
            if live_source or source in self.aliases or source in ('/', '/sok/', '/k/'):
                raise RouteError('Alias shadows an existing route')
            status = alias['status']
            if status in (301, 308):
                target = self.path(alias['kind'], alias['entity_id'])
                if source == target:
                    raise RouteError('Redirect loop')
            elif status in (404, 410):
                if any(k in alias for k in ('kind', 'entity_id', 'target')):
                    raise RouteError('Gone routes cannot have a successor')
            else:
                raise RouteError('Unsupported route disposition')
            if not alias.get('evidence'):
                raise RouteError('Alias requires reviewed identity/migration evidence')
            self.aliases[source] = alias
        if previous is not None:
            old = RouteRegistry(previous)
            for path, key in old.owners.items():
                if self.owners.get(path) != key:
                    raise RouteError('Frozen route removed or recycled; retain its reservation')
            for source, alias in old.aliases.items():
                if self.aliases.get(source) != alias:
                    raise RouteError('Historical disposition removed or changed without review')
            for path, key in old.owners.items():
                old_row = old.entities.get(key)
                was_active = old_row and old_row['state'] == 'active' and entity_path(old_row['kind'], old_row['slug']) == path
                current_row = self.entities.get(key)
                still_active = current_row and current_row['state'] == 'active' and entity_path(current_row['kind'], current_row['slug']) == path
                if was_active and not still_active and path not in self.aliases:
                    raise RouteError('Retired published path requires reviewed redirect or gone disposition')

    def path(self, kind, entity_id):
        row = self.entities.get((kind, entity_id))
        if not row or row['state'] != 'active':
            raise RouteError('Missing active canonical entity route')
        return entity_path(kind, row['slug'])

    def bind_product(self, product, comparison):
        # The existing offers contract supplies the canonical ID. A title, GTIN,
        # namespace or local slug is never sufficient evidence of this identity.
        identity = comparison.get('product_id')
        if not identity:
            raise RouteError('Offers response lacks canonical product identity')
        if product.get('product_id') not in (None, identity):
            raise RouteError('Catalogue and offers canonical identity disagree')
        result = dict(product)
        result['_public_path'] = self.path('product', identity)
        return result

    def redirect_plan(self, built_paths, base='/', existing_products=None):
        """Auditable edge input; GitHub Pages does not execute this plan."""
        def scoped(path):
            return base + path.lstrip('/')
        rules = {}
        for path in sorted(built_paths):
            if path != '/':
                rules[path.rstrip('/')] = {'source': scoped(path.rstrip('/')),
                    'status': 308, 'target': scoped(path)}
        for source, alias in self.aliases.items():
            rule = {'source': scoped(source), 'status': alias['status']}
            if alias['status'] in (301, 308):
                target = self.path(alias['kind'], alias['entity_id'])
                if target not in built_paths:
                    raise RouteError('Redirect target is not a built canonical page')
                rule['target'] = scoped(target)
            if source in built_paths or source in rules:
                raise RouteError('Alias shadows a built route or slash rule')
            rules[source] = rule
        for source, target in (existing_products or {}).items():
            local_path(source)
            if target not in built_paths or source in built_paths:
                raise RouteError('Invalid existing product URL mapping')
            rule = {'source': scoped(source), 'status': 308, 'target': scoped(target)}
            if source in rules and rules[source] != rule:
                raise RouteError('Conflicting existing product URL disposition')
            rules[source] = rule
        return list(rules.values())


def finalize_readiness(out, registry, base, existing_routes):
    """Align crawl signals without changing presentation or enabling indexing."""
    built = set()
    for file in out.rglob('*.html'):
        relative = file.relative_to(out).as_posix()
        text = file.read_text(encoding='utf-8')
        text = re.sub(r'''(["'])''' + re.escape(base) + r'(search|kategori)/',
            lambda match: match[1] + base + {'search': 'sok', 'kategori': 'k'}[match[2]] + '/', text)
        if relative == '404.html':
            file.write_text(text, encoding='utf-8')
            continue
        if not relative.endswith('index.html'):
            raise RouteError('Unexpected non-directory HTML page')
        path = '/' + relative[:-len('index.html')]
        built.add(path)
        # Shared shell/search keep their old defaults for the unactivated build.
        canonical = 'https://sjekkpris.no' + base + path.lstrip('/')
        text = text.replace('</head>', '<link rel="canonical" href="' + escape(canonical, quote=True) + '"></head>')
        file.write_text(text, encoding='utf-8')
    # Every page is noindex, so there are deliberately no sitemap entries.
    (out / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n', encoding='utf-8')
    (out / 'robots.txt').write_text('User-agent: *\nDisallow:\n', encoding='utf-8')
    existing_routes = dict(existing_routes, **{'/search/': '/sok/', '/kategori/': '/k/'})
    plan = registry.redirect_plan(built, base, existing_routes)
    # A deployed alias must never shadow a generated asset or HTML file.
    for rule in plan:
        path = rule['source'][len(base):]
        if (out / path).is_file():
            raise RouteError('Alias shadows a generated file')
    validate_readiness(out, base)
    return plan


class _Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.canonical, self.links, self.ids = [], [], set()
        self.noindex = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'link' and data.get('rel') == 'canonical':
            self.canonical.append(data.get('href'))
        if tag == 'meta' and data.get('name') == 'robots':
            self.noindex = 'noindex' in data.get('content', '').split(',')
        if data.get('id'):
            self.ids.add(data['id'])
        for key in ('href', 'src'):
            if data.get(key):
                self.links.append(data[key])


def validate_readiness(out, base):
    """Fail on missing/self-conflicting canonical, lost noindex or broken links."""
    out = out.resolve()
    pages = {file: _Page(file.read_text(encoding='utf-8')) for file in out.rglob('*.html')}
    links = []
    for file, page in pages.items():
        relative = file.relative_to(out).as_posix()
        public = base + relative.removesuffix('index.html')
        if not page.noindex:
            raise RouteError('Readiness page lost beta noindex')
        if relative != '404.html' and page.canonical != ['https://sjekkpris.no' + public]:
            raise RouteError('Canonical must point exactly to its built page')
        links.extend((public, value) for value in page.links)
    for row in json.loads((out / 'search-index.json').read_text(encoding='utf-8')):
        links.append((base, row['url']))
    for source, value in links:
        parts = urlsplit(urljoin('https://sjekkpris.no' + source, value))
        if parts.netloc != 'sjekkpris.no' or parts.path.startswith('/go/'):
            continue
        if not parts.path.startswith(base):
            raise RouteError('Internal link escapes build base')
        path = (out / unquote(parts.path[len(base):])).resolve()
        if not path.is_relative_to(out.resolve()):
            raise RouteError('Internal link escapes artifact')
        if path.is_dir():
            path = path / 'index.html'
        if not path.is_file():
            raise RouteError('Required internal link target is missing')
        if parts.fragment and path.suffix == '.html':
            if unquote(parts.fragment) not in pages[path].ids:
                raise RouteError('Required internal fragment is missing')
