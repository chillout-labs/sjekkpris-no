"""Compose existing Core receiver + website checks. No deploy or live read API."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

from delivery_candidate import prepare, preservation


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core', type=Path, required=True)
    p.add_argument('--receiver', type=Path, required=True)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--result-sha256', required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--baseline-sha256', required=True)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--environment', required=True, choices=('test',))
    p.add_argument('--indexable-candidate', action='store_true')
    p.add_argument('--synthetic-only', action='store_true')
    args = p.parse_args()
    if args.report.resolve().is_relative_to(args.site.resolve()):
        raise ValueError('report must remain private')
    spec = importlib.util.spec_from_file_location('core_pages_candidate', args.core)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    scope = ('sjekkpris-no', args.environment)
    if args.synthetic_only:
        with tarfile.open(args.bundle, 'r:') as archive:
            member = archive.next()
            if (member is None or member.name != 'result.json' or not member.isfile()
                    or member.size > 1024 * 1024):
                raise ValueError('synthetic envelope required')
            raw = archive.extractfile(member).read(member.size + 1)
            if (core.sha(raw) != args.result_sha256
                    or json.loads(raw).get('evidence_mode') != 'synthetic'):
                raise ValueError('public Actions accepts synthetic evidence only')
    baseline = core.read_inventory(args.baseline, args.baseline_sha256, scope)
    receipt = core.receive(args.bundle, args.site, args.receiver, scope, args.result_sha256)
    received = core.inventory(args.site, scope, args.result_sha256)
    preservation(baseline, received)
    website = prepare(args.site, indexable=args.indexable_candidate)
    candidate = core.inventory(args.site, scope, args.result_sha256)
    preservation(baseline, candidate)
    report = core.compare(baseline, candidate)
    report.update(received_tree_sha256=received['tree_sha256'], receipt=receipt, website=website)
    args.report.write_text(json.dumps(report, sort_keys=True), encoding='utf-8')
    # Log counts only. Site and detailed evidence are not uploaded by this slice.
    print(json.dumps({'products': len(website['product_routes']),
                      'changed_files': len(report['changes']),
                      'published': None, 'publication_authorized': False}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, tarfile.TarError):
        sys.exit('Delivery review refused; do not publish')
