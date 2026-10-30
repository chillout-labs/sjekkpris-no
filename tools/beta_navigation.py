"""Owner-approved link-only correction to one recovered design-preview page.

This immutable before/after exception grants no general beta editing permission.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

PLAN = json.loads(Path(__file__).with_name('beta-navigation-adjustment.json').read_text('utf-8'))


def descriptor(raw, name):
    return dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def approved_change(before, after):
    return before == PLAN['before'] and after == PLAN['after']


def adjust(raw, retired_routes, plan=PLAN):
    if descriptor(raw, plan['before']['path']) != plan['before']:
        raise ValueError('beta navigation baseline mismatch')
    if not {urlsplit(link).path for link in plan['links']} <= retired_routes:
        raise ValueError('beta navigation requires exact retired targets')
    result, count = raw, 0
    for link in plan['links']:
        original = ('href="' + link + '"').encode()
        count += result.count(original)
        result = result.replace(original, ('href="' + plan['target'] + '"').encode())
    if count != plan['count'] or descriptor(result, plan['after']['path']) != plan['after']:
        raise ValueError('beta navigation result mismatch')
    return result
