"""Package the isolated design fixture under /beta/ in an existing site build."""
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent


def package(site):
    source = ROOT / '.design-preview'
    target = Path(site) / 'beta'
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    # Rebase HTML attributes, inline script URLs, JSON search results and CSS URLs.
    # Only root-relative paths are changed; external and protocol-relative URLs stay intact.
    for path in target.rglob('*'):
        if path.suffix not in {'.html', '.json', '.css', '.js'}:
            continue
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'''(["'])/(?!/)''', r'\1/beta/', text)
        text = re.sub(r'url\(/(?!/)', 'url(/beta/', text)
        path.write_text(text, encoding='utf-8')
        if path.suffix == '.html':
            assert 'noindex' in text, path
            assert 'Beta / designoversikt' in text, path
    # Fixture sitemap/crawl files must not advertise synthetic products.
    for name in ('sitemap.xml', 'robots.txt', 'CNAME'):
        (target / name).unlink(missing_ok=True)
    print(f'Beta preview packaged at {target}')


if __name__ == '__main__':
    package(sys.argv[1])
