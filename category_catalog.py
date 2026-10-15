"""Presentation index of Chillout's categories. Never classifies products.

/category routes are preview-only until the property route contract is locked.
"""
from html import escape as e
import re
import unicodedata


def preview_slug(name):
    value = name.lower().translate(str.maketrans({'æ':'ae', 'ø':'o', 'å':'a'}))
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def category_index(products):
    nodes, routes = {}, {}
    for product in products:
        facts = product.get('categories') or {}
        memberships = [facts.get('primary')] + list(facts.get('additional') or [])
        for category in memberships:
            if not category or not category.get('active', True):
                continue
            path = list(category.get('path') or [])
            if not path or path[-1].get('id') != category.get('id'):
                path.append(category)
            parent = None
            for position, fact in enumerate(path):
                key = fact.get('id')
                name = fact.get('display_name') or fact.get('name')
                if not key or not name:
                    raise ValueError('Category path lacks an identity or name')
                slug = preview_slug(name)
                if not slug:
                    raise ValueError('Category cannot form a preview route')
                if slug in routes and routes[slug] != key:
                    raise ValueError('Category preview route collision: ' + slug)
                routes[slug] = key
                node = nodes.setdefault(key, {'name':name, 'slug':slug, 'parent':parent,
                                             'ancestors':[], 'products':{}, 'children':[]})
                if node['parent'] != parent or node['name'] != name:
                    raise ValueError('Inconsistent category path supplied by Chillout')
                node['ancestors'] = [part['id'] for part in path[:position]]
                node['products'][(product['namespace'], product['local_slug'])] = product
                if parent and key not in nodes[parent]['children']:
                    nodes[parent]['children'].append(key)
                parent = key
    return nodes


def category_href(node, base):
    return f'{base}kategori/{node["slug"]}/'


def category_navigation(nodes, base):
    if not nodes:
        return ''
    roots = [n for n in nodes.values() if n['parent'] is None]
    links = ''.join(f'<a href="{e(category_href(n, base), quote=True)}">{e(n["name"])}</a>' for n in sorted(roots,key=lambda n:n['name']))
    return (f'<nav class="sp-category-nav" aria-label="Kategorier"><div class="sp-shell">'
            f'<a class="sp-all-categories" href="{e(base)}kategori/">Alle kategorier</a>{links}</div></nav>')


def category_links(product, nodes, base):
    primary = (product.get('categories') or {}).get('primary') or {}
    node = nodes.get(primary.get('id'))
    if not node:
        return []
    return [(nodes[key]['name'], category_href(nodes[key],base)) for key in node['ancestors']] + [(node['name'],category_href(node,base))]


def render_category_index(nodes, base):
    def branch(key):
        n = nodes[key]
        children = ''.join(branch(k) for k in sorted(n['children'],key=lambda k:nodes[k]['name']))
        return (f'<li><a href="{e(category_href(n,base))}"><span>{e(n["name"])}</span><small>{len(n["products"])} produkter</small></a>'
                + (f'<ul>{children}</ul>' if children else '') + '</li>')
    roots = sorted((k for k,n in nodes.items() if n['parent'] is None), key=lambda k:nodes[k]['name'])
    return ('<section class="sp-home sp-category-index"><nav class="sp-breadcrumb" aria-label="Brødsmulesti">'
            f'<a href="{e(base)}">Hjem</a><span>›</span><span>Kategorier</span></nav>'
            '<h1>Utforsk kategorier</h1><p>Finn produkter og sammenlign butikkenes priser.</p>'
            '<ul class="sp-category-tree">' + ''.join(branch(k) for k in roots) + '</ul></section>')
