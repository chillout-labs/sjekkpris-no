"""Paired HTML for an already-qualified immutable Chillout comparison.

Callable by the pinned Delivery consumer. No API requests, qualification or export.
Existing renderer remains the owner of visible data semantics and site design.
"""
import copy
import json
import re
from decimal import Decimal

import build

AVAILABILITY = {'in_stock': 'InStock', 'out_of_stock': 'OutOfStock',
                'preorder': 'PreOrder', 'backorder': 'BackOrder'}


def product_schema(product, comparison, canonical):
    identity = comparison.get('identity') or {}
    schema = {'@context': 'https://schema.org', '@type': 'Product',
              'name': identity.get('local_name') or product['local_name'], 'url': canonical}
    offers = []
    for offer in comparison.get('offers') or []:
        href = build.shop_href(offer, excluded=False)
        amount = offer.get('item_price')
        if not href or not amount:
            continue
        if type(amount['minor']) is not int or amount['minor'] < 0:
            raise ValueError('invalid price representation')
        item = {'@type': 'Offer', 'url': href,
                'price': format(Decimal(amount['minor']) / 100, '.2f'),
                'priceCurrency': amount['currency']}
        availability = AVAILABILITY.get((offer.get('availability') or {}).get('status'))
        if availability:
            item['availability'] = 'https://schema.org/' + availability
        if offer.get('advertiser'):
            item['seller'] = {'@type': 'Organization', 'name': offer['advertiser']}
        # Shipping is shown by the existing renderer. Do not invent destinations,
        # delivery windows or free-shipping evidence just to populate JSON-LD.
        offers.append(item)
    if offers:
        schema['offers'] = offers
    return schema


def render_pair(product, comparison, *, path, noindex, breadcrumbs=(), presentation=None):
    if not re.fullmatch(r'/p/[a-z0-9]+(?:-[a-z0-9]+)*/', path) or type(noindex) is not bool:
        raise ValueError('invalid route or indexing policy')
    canonical = build.SITE_ORIGIN + path
    safe = copy.deepcopy(comparison)
    safe.update(offers=[], excluded=[], lowest_item_price=None, lowest_known_total_price=None)
    result = []
    for body in (comparison, safe):
        content = build.product_body(product, body, base='/', breadcrumbs=breadcrumbs,
                                     presentation=presentation)
        schema = json.dumps(product_schema(product, body, canonical), ensure_ascii=False,
                            separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e')
        content += '<script type="application/ld+json">' + schema + '</script>'
        html = build.page(product['local_name'] + ' – SjekkPris', content, base='/', noindex=noindex)
        html = html.replace('</head>', '<link rel="canonical" href="' + build.e(canonical) + '"></head>', 1)
        if body is safe and '/go/' in html:
            raise ValueError('fallback contains a purchase link')
        result.append(html.encode())
    return tuple(result)
