"""Offline URL inventory of an existing build. Does not crawl merchant links.

python tools/inventory_urls.py _beta_test /beta/ > docs/URL-INVENTORY-BETA.csv
Only site-local paths and sjekkpris.no links are recorded, never private IDs.
"""
import csv
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.urls = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.extend(value for key, value in attrs if key == 'href' and value)


def inventory(root, prefix='/'):
    root = Path(root)
    rows = set()
    for file in (root / prefix.strip('/')).rglob('*.html'):
        relative = file.relative_to(root).as_posix()
        path = '/' + relative.removesuffix('index.html') if file.name == 'index.html' else '/' + relative
        rows.add((path, 'built', 'beta-noindex; retain until reviewed cutover'))
        for url in Links(file.read_text(encoding='utf-8')).urls:
            parts = urlsplit(urljoin('https://sjekkpris.no' + path, url))
            if parts.netloc == 'sjekkpris.no' and not parts.path.startswith('/go/'):
                rows.add((parts.path, 'linked', 'exact canonical mapping required; do not infer from name'))
    return sorted(rows)


if __name__ == '__main__':
    writer = csv.writer(sys.stdout, lineterminator='\n')
    writer.writerow(('path', 'source', 'disposition'))
    writer.writerows(inventory(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '/'))
