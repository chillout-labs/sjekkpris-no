"""Review an existing complete Delivery site; never fetch, rebuild or publish.

Core owns bundle verification and qualification. This module owns SjekkPris
presentation checks and explicit candidate SEO. Default remains private noindex.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
try:
    from .beta_navigation import approved_change
except ImportError:
    from beta_navigation import approved_change
from urllib.parse import urlsplit, urljoin, unquote
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_output import check  # noqa: E402

ORIGIN = "https://sjekkpris.no"
PRIVATE_BANNER = ('<aside class="sp-panel" aria-label="Privat forhåndsvisning"><p>'
                  'Privat readinessbygg · datert øyeblikksbilde. '
                  'Butikkhandlinger er sperret.</p></aside>')
CLICKOUT = re.compile(r"/go/tgt_[0-9A-HJKMNP-TV-Z]{26}")


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.canonicals, self.robots, self.links, self.images = [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href'))
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots.append(a.get('content', ''))
        if tag == 'a' and a.get('href'):
            self.links.append(a)
        if tag == 'img' and a.get('src'):
            self.images.append(a)


def route(path, root):
    return '/' + path.relative_to(root).parent.as_posix().strip('.').strip('/') + '/'


def entity_path(value):
    return bool(re.fullmatch(r'/(?:p|k|kategori)/[a-zA-Z0-9_./-]+/', value))


def inspect(site, *, navigation_aliases=()):
    site = Path(site)
    pages = {}
    for path in site.rglob('*.html'):
        if path.is_symlink() or path.is_junction():
            raise ValueError('site link')
        if path.name == 'index.html':
            pages[route(path, site).replace('//', '/')] = Page(path.read_text('utf-8'))
    products = {p for p in pages if p.startswith('/p/')}
    categories = {p for p in pages if p.startswith(('/k/', '/kategori/'))
                  and p not in {'/k/', '/kategori/'}
                  and p.strip('/') + '/index.html' not in navigation_aliases}
    if not products:
        raise ValueError('empty qualified catalogue')
    index = json.loads((site / 'search-index.json').read_text('utf-8'))
    if not isinstance(index, list):
        raise ValueError('search index')
    search = set()
    for item in index:
        url = urlsplit(item['url'])
        if url.scheme or url.netloc or not url.path.startswith('/p/') or url.path not in products:
            raise ValueError('search references missing or foreign product')
        search.add(url.path)
    if search != products:
        raise ValueError('product missing from search')
    members = {p: {urlsplit(urljoin(ORIGIN+p, a['href'])).path
                   for a in pages[p].links
                   if urlsplit(urljoin(ORIGIN+p, a['href'])).netloc == 'sjekkpris.no'}
               & products for p in categories}
    listed = set().union(*members.values()) if members else set()
    if not products <= listed:
        raise ValueError('product missing from category listings')
    for product in products:
        page = pages[product]
        if not page.images:
            raise ValueError('product image missing')
        for a in page.links:
            target = urlsplit(a['href'])
            if target.path.startswith('/go/'):
                if (target.scheme or target.netloc) and (
                        target.scheme != 'https' or target.netloc != 'sjekkpris.no'):
                    raise ValueError('foreign clickout')
                if (not CLICKOUT.fullmatch(target.path) or target.query or target.fragment
                        or not {'sponsored', 'nofollow'} <= set(a.get('rel', '').split())):
                    raise ValueError('clickout contract')
            if target.path.startswith(('/p/', '/k/', '/kategori/')) and target.path not in pages:
                raise ValueError('broken entity link')
    # Check all HTML, including preserved informational/beta pages and relative links.
    for path in site.rglob('*.html'):
        source = '/' + path.relative_to(site).as_posix()
        for anchor in Page(path.read_text('utf-8')).links:
            target = urlsplit(urljoin(ORIGIN + source, anchor['href']))
            if target.scheme not in ('http', 'https') or target.netloc != 'sjekkpris.no':
                continue
            local = unquote(target.path)
            if local.startswith('/go/'):
                continue  # Existing dynamic resolver; validated separately on products.
            dest = site / local.lstrip('/')
            if not dest.resolve().is_relative_to(site.resolve()):
                raise ValueError('unsafe internal link')
            if local.endswith('/'):
                dest /= 'index.html'
            if not dest.is_file():
                raise ValueError('broken internal link: ' + source + ' -> ' + local)
    return pages, products, {p for p, products_in_category in members.items()
                             if products_in_category}


def prepare(site, *, indexable=False, navigation_aliases=(), mutable_pages=None):
    """Only a staging copy may be passed here. Does not authorize indexability."""
    site = Path(site)
    pages, products, categories = inspect(site, navigation_aliases=navigation_aliases)
    indexable_routes = products | categories
    # Complete validation before any SEO write; never repair conflicting identity.
    for url in indexable_routes:
        page = pages[url]
        if not entity_path(url):
            raise ValueError('entity path')
        if page.canonicals and page.canonicals != [ORIGIN + url]:
            raise ValueError('canonical conflict')
        if (len(page.robots) != 1 or 'noindex' not in
                {v.strip() for v in page.robots[0].lower().split(',')}):
            raise ValueError('expected private noindex input')
    for url in sorted(indexable_routes):
        path = site / url.strip('/') / 'index.html'
        text = path.read_text('utf-8')
        if not pages[url].canonicals:
            if text.lower().count('</head>') != 1:
                raise ValueError('page head')
            text = re.sub('</head>', '<link rel="canonical" href="'+ORIGIN+url+'"></head>',
                          text, flags=re.I)
        # Preserve existing public clickout identity; only normalize the private relative form.
        text = re.sub(r'href="(/go/tgt_[0-9A-HJKMNP-TV-Z]{26})"',
                      lambda m: 'href="'+ORIGIN+m[1]+'"', text)
        if indexable:
            text, n = re.subn(r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>',
                              '<meta name="robots" content="index,follow">', text, flags=re.I)
            if n != 1:
                raise ValueError('robots markup')
        path.write_text(text, encoding='utf-8')
    if indexable:
        # Exact known renderer decoration only. Unknown private markup fails closed.
        for path in site.rglob('*.html'):
            if mutable_pages is not None and path.relative_to(site).as_posix() not in mutable_pages:
                continue
            original = path.read_text('utf-8')
            text = original.replace(PRIVATE_BANNER, '')
            if 'Privat forhåndsvisning' in text or 'Privat readinessbygg' in text:
                raise ValueError('unknown private presentation')
            if text != original:
                path.write_text(text, encoding='utf-8')
    urls = sorted(indexable_routes) if indexable else []
    (site / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
        ''.join('<url><loc>'+escape(ORIGIN+p)+'</loc></url>' for p in urls) + '</urlset>',
        encoding='utf-8')
    (site / 'robots.txt').write_text(
        'User-agent: *\nDisallow: /beta/\nDisallow: /go/\nDisallow: /search/\n'
        'Disallow: /sok/\nSitemap: '+ORIGIN+'/sitemap.xml\n'
        if indexable else 'User-agent: *\nDisallow: /\n', encoding='utf-8')
    problems = check(site)
    if problems:
        raise ValueError('existing output safety check failed')
    # Non-catalogue pages never gain indexability through this projection.
    for url, page in pages.items():
        if url not in indexable_routes and not any('noindex' in v.lower() for v in page.robots):
            raise ValueError('non-catalogue page lacks noindex')
    return dict(product_routes=sorted(products), category_routes=sorted(categories),
                seo_mode='public-candidate' if indexable else 'private',
                published=None, publication_authorized=False)


def preservation(baseline, candidate, retirement=None, *, navigation_aliases=()):
    """Existing URLs cannot silently vanish during a full catalogue build."""
    old = {f['path']: f for f in baseline['files']}
    new = {f['path']: f for f in candidate['files']}
    removed = sorted(set(old) - set(new))
    retired = set()
    if retirement is not None:
        if (retirement.get('version') != 'sjekkpris.test-catalogue-retirement.v1'
                or retirement.get('scope') != baseline.get('scope')
                or baseline.get('scope', [None])[0] != 'sjekkpris-no'
                or retirement.get('baseline_tree_sha256') != baseline.get('tree_sha256')
                or not baseline.get('tree_sha256')
                or not isinstance(retirement.get('files'), list)
                or not retirement['files']):
            raise ValueError('retirement binding')
        for row in retirement['files']:
            name = row['path']
            if (not re.fullmatch(r'p/(?:[a-z0-9-]+/)+index\.html', name)
                    or name in retired or old.get(name) != row):
                raise ValueError('retirement descriptor')
            retired.add(name)
        if retired & new.keys():
            raise ValueError('retired product remains')
    if set(removed) != retired:
        raise ValueError('baseline files missing; explicit migration review required')
    # Shared catalogue surfaces may change; protected design/beta assets may not.
    if any(p != 'search/index.html' and not (p.startswith('kategori/') and p.endswith('/index.html'))
           for p in navigation_aliases):
        raise ValueError('unsupported navigation alias')
    mutable = {'index.html', 'search-index.json', 'robots.txt', 'sitemap.xml'} | set(navigation_aliases)
    changed_protected = [p for p in old if p not in mutable
                         and not (p.startswith(('p/', 'k/', 'kategori/', 'sok/'))
                                  and p.endswith('/index.html'))]
    if any(old[p] != new[p] and not approved_change(old[p], new[p]) for p in changed_protected):
        raise ValueError('existing design or beta changed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--indexable-candidate', action='store_true')
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.report.resolve().is_relative_to(args.site.resolve()):
        raise ValueError('report outside deployable site required')
    result = prepare(args.site, indexable=args.indexable_candidate)
    result['sitemap_sha256'] = hashlib.sha256((args.site/'sitemap.xml').read_bytes()).hexdigest()
    args.report.write_text(json.dumps(result, sort_keys=True), encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError):
        raise SystemExit('Candidate refused; do not publish') from None
