"""Website-owned catalogue composition over a hash-verified served baseline."""
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit

from delivery_candidate import ORIGIN, preservation
from beta_navigation import PLAN, adjust


def catalogue(name):
    return (name in {'index.html', 'search-index.json', 'robots.txt', 'sitemap.xml'}
            or (name.startswith(('p/', 'k/', 'sok/')) and name.endswith('/index.html')))


def compose(core, baseline, baseline_site, received_site, output, scope, retirement=None):
    """No renderer, network, authority or original-input mutation."""
    baseline_site, received_site, output = map(Path, (baseline_site, received_site, output))
    if output.exists() or any(output.resolve().is_relative_to(p.resolve()) or
                              p.resolve().is_relative_to(output.resolve())
                              for p in (baseline_site, received_site)):
        raise ValueError('composition requires separate new output')
    actual = core.inventory(baseline_site, scope, 'baseline-check')
    if actual['tree_sha256'] != baseline['tree_sha256'] or actual['files'] != baseline['files']:
        raise ValueError('baseline content mismatch')
    received = core.inventory(received_site, scope, 'received-check')
    old = {f['path']: f for f in baseline['files']}
    incoming = {f['path']: f for f in received['files']}
    for required in ('index.html', 'search-index.json', 'sok/index.html', 'k/index.html'):
        if required not in incoming:
            raise ValueError('incomplete received catalogue')
    # Legacy navigation survives, but never retains stale product membership.
    aliases = {name: ('sok/index.html' if name == 'search/index.html' else 'k/index.html')
               for name in old if name == 'search/index.html' or
               (name.startswith('kategori/') and name.endswith('/index.html'))}
    selected = {name: baseline_site / name for name in old if not catalogue(name)}
    selected.update({name: received_site / name for name in incoming if catalogue(name)})
    selected.update({name: received_site / target for name, target in aliases.items()})
    conflicts = set()
    for name in incoming:
        if catalogue(name) or name.startswith('beta/'):
            continue
        if name in old:
            if old[name] != incoming[name]:
                conflicts.add(name)
        else:
            # Only supporting assets, never unrelated received HTML pages.
            if name.endswith('.html'):
                raise ValueError('unexpected received page')
            selected[name] = received_site / name
    # A different protected asset cannot silently change the generated presentation.
    # Include CSS references; unrelated old aliases may differ if unused by new pages.
    for name, source in selected.items():
        if source.is_relative_to(received_site) and source.suffix in ('.html', '.css', '.js'):
            text = source.read_text('utf-8')
            references = re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)', text)
            references += re.findall(r'url\([\"\x27]?([^\)\"\x27]+)', text)
            for value in references:
                url = urlsplit(urljoin(ORIGIN + '/' + name, value))
                if url.netloc == 'sjekkpris.no' and url.path.lstrip('/') in conflicts:
                    raise ValueError('received reference conflicts with protected asset')
    descriptors = []
    for name, source in sorted(selected.items()):
        root, rows = (received_site, incoming) if source.is_relative_to(received_site) else (baseline_site, old)
        descriptors.append(dict(rows[source.relative_to(root).as_posix()], path=name))
    projected = dict(baseline, files=descriptors)
    preservation(baseline, projected, retirement, navigation_aliases=set(aliases))
    # Validate the entire selection before writing. Caller's temporary directory is
    # published as a candidate only after all website checks and final preservation.
    output.mkdir(parents=True)
    for name, source in selected.items():
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    # Apply only the separately approved, exact before/after link correction.
    name = PLAN['before']['path']
    if retirement and old.get(name) == PLAN['before']:
        retired_routes = {'/' + row['path'].removesuffix('index.html')
                          for row in retirement['files']}
        path = output / name
        path.write_bytes(adjust(path.read_bytes(), retired_routes))
    return set(aliases)
