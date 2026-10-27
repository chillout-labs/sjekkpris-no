"""One-shot read-only, encrypted source observation. No renderer or authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import Chillout, SAFE_SEGMENT, comparison

PROPERTY = 'sjekkpris-no'
ORIGIN = 'https://backoffice-test-d71d.up.railway.app'
MAX_ROWS = 200
MAX_BYTES = 10_485_760
EXCLUDED = frozenset(['a59e052540fe2bd2e81eeedab525ab4a86cfb121241046bbe66eca2433bea708', 'ae7086b58f55e6ca1452b1ca5624f87ee92379c42797d4b60bcf4379ca82e437', '898952e53e94e8933ac9b2b6fe8a9e9439c0348c20a76d81da2763290b38c27b'])

class Refused(Exception):
    pass

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def capture(client):
    first = client.get('/api/v1/properties/' + PROPERTY + '/catalogue?locale=nb')
    if first.get('property_id') != PROPERTY or not isinstance(first.get('products'), list):
        raise Refused('scope')
    if len(first['products']) > MAX_ROWS:
        raise Refused('budget')
    seen, index, products, held = set(), [], [], 0
    for row in first['products']:
        ns, slug = row.get('namespace'), row.get('local_slug')
        if not all(isinstance(v, str) and SAFE_SEGMENT.fullmatch(v) for v in (ns, slug)):
            raise Refused('alias')
        if (ns, slug) in seen:
            raise Refused('duplicate alias')
        seen.add((ns, slug))
        value = comparison(client, ns, slug)
        pid = value.get('product_id')
        identity = value.get('identity') or {}
        if (value.get('property_id') != PROPERTY or not isinstance(pid, str)
            or not pid.startswith('prd_') or identity.get('namespace') != ns
            or identity.get('local_slug') != slug or not isinstance(value.get('offers'), list)):
            raise Refused('binding')
        if digest(pid.encode()) in EXCLUDED:
            held += 1
            continue
        index.append(row)
        products.append(value)
    if encode(first) != encode(client.get('/api/v1/properties/' + PROPERTY + '/catalogue?locale=nb')):
        raise Refused('source changed')
    return {'version':'sjekkpris.encrypted-source-observation.v1',
        'evidence_mode':'frozen_authorized_observation',
        'observed_at':datetime.now(timezone.utc).isoformat(),
        'property_id':PROPERTY,'locale':'nb','held_count':held,
        'catalogue':{'property_id':PROPERTY,'products':index},'products':products,
        'publication_authority':False,'operative_rights_created':False}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def encrypted_bytes(document, key, recipient):
    raw = encode(document)
    if not key or key.encode() in raw or len(raw) > MAX_BYTES:
        raise Refused('source integrity or budget')
    if not recipient.startswith('age1') or any(c.isspace() for c in recipient):
        raise Refused('recipient')
    result = subprocess.run(['age','--encrypt','--recipient',recipient],input=raw,
        capture_output=True,timeout=30)
    if result.returncode or not result.stdout.startswith(b'age-encryption.org/'):
        raise Refused('encryption')
    return result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recipient',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args = parser.parse_args()
    try:
        if args.out.exists() or os.environ.get('CHILLOUT_ORIGIN') != ORIGIN:
            raise Refused('unreviewed output or origin')
        key = os.environ.get('CHILLOUT_READ_KEY','')
        if not key:
            raise Refused('missing machine key')
        urllib.request.install_opener(urllib.request.build_opener(NoRedirect))
        doc = capture(Chillout(ORIGIN,key))
        cipher = encrypted_bytes(doc,key,args.recipient.read_text().strip())
        with args.out.open('xb') as output:
            output.write(cipher)
    except Exception:
        print('Encrypted source capture refused; no plaintext output.',file=sys.stderr)
        return 1
    print('Encrypted source capture complete; no plaintext output.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
