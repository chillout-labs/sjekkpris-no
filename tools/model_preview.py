"""URL-03F: localhost-only consumer of reviewed URL-03E observations.

Not imported by build.py, not a Delivery adapter, publisher or route registry.
Real input stays outside this repository. Integrity is not current authority.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import analytics_consent
import build

CORE_COMMIT = "08d606a97c7f863141daf961207459da4a4e13c2"
SCOPE = ("sjekkpris-no", "test", "nb")
CSS = "* { box-sizing:border-box }\n" + build.STYLE + build.PRODUCT_STYLE + build.HOME_STYLE
CSS_PATH = "/style-" + hashlib.sha256((build.STYLE + build.PRODUCT_STYLE + build.HOME_STYLE).encode()).hexdigest()[:12] + ".css"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def core_verifier(checkout):
    """Use the existing pinned Core implementation; never copy or install it."""
    checkout = Path(checkout).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=checkout, text=True)
    if head != CORE_COMMIT or dirty:
        raise ValueError("a clean, pinned URL-03E checkout is required")
    sys.path.insert(0, str(checkout / "src"))
    from chillout import model_presentation as contract
    limits = contract.Limits(contract.export.Limits(max_aliases=20000, max_offers_per_product=100,
                              max_bytes=10_485_760, max_seconds=30), 4, 8, 1000)

    def verify(entry, artifact_data):
        artifact = contract.export.Export(base64.b64decode(artifact_data["manifest"], validate=True),
                                           base64.b64decode(artifact_data["payload"], validate=True))
        raw = base64.b64decode(entry["payload"], validate=True)
        request = json.loads(raw)["request"]
        request = contract.Request(**(request | {k: tuple(request[k]) for k in ("product_ids", "pending_product_ids")}))
        value = contract.verify(contract.Snapshot(raw), artifact, snapshot_sha256=entry["sha256"],
                                request=request, limits=limits)
        trace = json.loads(artifact.manifest)["trace"]
        rows = json.loads(artifact.payload)["locales"][request.locale]["products"]
        identities = [row["identity"] for row, owner in zip(rows, trace, strict=True)
                      if owner["product_id"] == value["selected"]["product_id"]]
        if not identities or any(i != identities[0] for i in identities):
            raise ValueError("ambiguous source identity")
        return value, identities[0]
    return verify


class BundleReader:
    """Reload the exact local approval on EVERY request, including errors/assets.

    Expected hash is supplied out of band. Removal, edit, inactive or expiry
    immediately refuses subsequent requests. This is a frozen private review,
    not a live revocation check or publication lease from Chillout.
    """
    def __init__(self, path, expected_sha256, verify):
        self.path, self.expected, self.verify = Path(path), expected_sha256, verify

    def __call__(self):
        if self.path.stat().st_size > 10_485_760:
            raise ValueError("bundle budget")
        raw = self.path.read_bytes()
        if digest(raw) != self.expected:
            raise ValueError("bundle changed")
        doc = json.loads(raw)
        now = datetime.now(timezone.utc)
        observed = datetime.fromisoformat(doc["observed_at"])
        expiry = datetime.fromisoformat(doc["expires_at"])
        if (doc["active"] is not True or doc["core_commit"] != CORE_COMMIT
                or not observed <= now < expiry or (expiry - observed).total_seconds() > 86400):
            raise ValueError("approval expired or inactive")
        if len(doc["snapshots"]) != 8:
            raise ValueError("exact eight selections required")
        states, models, seen = {}, None, set()
        source = specification = None
        for entry in doc["snapshots"]:
            value, identity = self.verify(entry, doc["artifact"])
            request = value["request"]
            if (tuple(request[k] for k in ("property_id", "environment", "locale")) != SCOPE
                    or value["contract_version"] != "chillout.model-presentation.v1"
                    or value["visibility"] != "private" or value["reserved"] is not False
                    or value["runtime_integrated"] is not False or value["published"] is not None
                    or value["build_ready"] is not False):
                raise ValueError("scope or inactive boundary")
            if models is None:
                models, source, specification = value["models"], value["source"], value["specification"]
            if (value["models"] != models or value["source"] != source
                    or value["specification"] != specification or len(models) != 4):
                raise ValueError("mixed revision")
            selected = value["selected"]
            model = next(m for m in models if m["reference"] == selected["model_reference"])
            path = model["desired_path"]
            if not re.fullmatch(r"/p/[a-z0-9]+(?:-[a-z0-9]+)*/", path) or model["permanent_owner"] is not None:
                raise ValueError("not a private model path")
            member = next(m for m in model["members"] if m["product_id"] == selected["product_id"])
            if (not SLUG.fullmatch(member["selector"]) or selected["selector"] != member["selector"]
                    or selected["label"] != member["label"] or selected["product_id"] in request["pending_product_ids"]):
                raise ValueError("selection binding")
            key = (path, selected["selector"])
            if key in states or selected["product_id"] in seen:
                raise ValueError("duplicate selection")
            seen.add(selected["product_id"])
            projection = selected["projection"]
            if projection is not None and projection["image"] != identity.get("image"):
                raise ValueError("selected image binding")
            states[key] = {"selected": selected, "identity": identity}
        expected = {(m["desired_path"], v["selector"]) for m in models for v in m["members"]}
        if set(states) != expected or any(len(m["members"]) != 2 for m in models):
            raise ValueError("incomplete model set")
        return {"models": models, "states": states, "observed_at": doc["observed_at"]}


def document(title, body, canonical=None):
    html = build.page(title, body, base="/", noindex=True)
    # Remove consent/analytics entirely in this tool, without changing production.
    for markup in (analytics_consent.head_markup(), analytics_consent.body_markup(), analytics_consent.footer_link()):
        html = html.replace(markup, "")
    # Existing mobile CSS hides the visible menu text. Keep its accessible name.
    html = html.replace('<details class="sp-menu"><summary>', '<details class="sp-menu"><summary aria-label="Meny">')
    if canonical:
        html = html.replace("</head>", f'<link rel="canonical" href="{escape(canonical, quote=True)}"></head>')
    # All commercial buttons terminate locally, even with previously approved consent.
    html = re.sub(r'href="[^"]*/go/[^\"]+"', 'href="/butikk/"', html)
    if any(s in html for s in ("/go/", "tgt_", "googletagmanager", "GTM-")):
        raise ValueError("operative output refused")
    return html


def render(bundle, path, selector, origin):
    model = next(m for m in bundle["models"] if m["desired_path"] == path)
    state = bundle["states"].get((path, selector)) if selector is not None else None
    if selector is not None and state is None:
        raise KeyError("unknown color")
    choices = [(v["label"], path + "?farge=" + v["selector"], v["selector"] == selector)
               for v in model["members"]]
    projection = state["selected"]["projection"] if state else None
    identity = copy.deepcopy(state["identity"]) if projection is not None else {}
    identity["local_name"] = model["name"]
    comparison = copy.deepcopy(projection["comparison"]) if projection is not None else {
        "offers": [], "excluded": [], "lowest_item_price": None, "lowest_known_total_price": None}
    # Existing renderer receives ONLY this selected projection, no mixed prices/images.
    comparison["identity"] = identity
    label = state["selected"]["label"] if state else None
    summary = "Farge: " + label if label else "Velg farge for å se bilde og priser."
    if state and projection is None:
        summary += " Vare- og fargekoblingen er ikke dokumentert. Bilde og tilbud vises ikke."
    presentation = {"variants": choices, "summary": summary}
    body = build.product_body({"local_name": model["name"]}, comparison, base="/", presentation=presentation)
    notice = ('<aside class="sp-panel" aria-label="Privat forhåndsvisning"><p>'
              'Privat demonstrasjon · datert øyeblikksbilde. Butikkhandlinger er deaktivert. '
              f'Datagrunnlag: {escape(bundle["observed_at"])}.</p></aside>')
    return document(model["name"] + (" – " + label if label else "") + " – SjekkPris", notice + body, origin + path)


def make_server(reader, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # Do not log private selections or paths.

        def do_GET(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            status, mime = 200, "text/html; charset=utf-8"
            try:
                if self.headers.get("Host") != urlsplit(origin).netloc:
                    raise PermissionError("local host required")
                bundle = reader()
                url = urlsplit(self.path)
                args = parse_qs(url.query, keep_blank_values=True, strict_parsing=True)
                if args and (set(args) != {"farge"} or len(args["farge"]) != 1 or not SLUG.fullmatch(args["farge"][0])):
                    raise KeyError("query refused")
                if url.path == "/robots.txt":
                    mime, body = "text/plain", "User-agent: *\nDisallow: /\n"
                elif url.path == CSS_PATH:
                    mime, body = "text/css", CSS
                elif url.path == "/butikk/":
                    body = document("Privat forhåndsvisning", '<h1>Butikkhandlinger er deaktivert</h1><p>Ingen butikk åpnes i demonstrasjonen.</p><a href="/">Til modellene</a>')
                elif url.path in {"/", "/search/", "/kategori/"}:
                    links = ''.join(f'<li><a href="{escape(m["desired_path"])}">{escape(m["name"])}</a></li>' for m in bundle["models"])
                    body = document("Privat modelldemonstrasjon – SjekkPris", '<h1>Privat modelldemonstrasjon</h1><p>Velg modell og deretter farge. Ingen produktaktivering eller butikkhandlinger.</p><ul>' + links + '</ul>')
                elif url.path == "/search-index.json":
                    mime = "application/json"
                    body = json.dumps([{"name": m["name"], "url": m["desired_path"], "price": None} for m in bundle["models"]])
                else:
                    body = render(bundle, url.path, args.get("farge", [None])[0], origin)
            except (KeyError, StopIteration, ValueError) as error:
                status = 404 if isinstance(error, (KeyError, StopIteration)) else 503
                body = document("Forhåndsvisning utilgjengelig", '<h1>Forhåndsvisning utilgjengelig</h1><p>Ukjent farge eller datagrunnlaget må kontrolleres på nytt.</p>')
            except (OSError, PermissionError):
                status, body = 503, document("Forhåndsvisning utilgjengelig", '<h1>Forhåndsvisning utilgjengelig</h1>')
            except Exception:
                # Core refusals/malformed private files must not leak diagnostics
                # or leave an old selected comparison visible in a partial response.
                status, body = 503, document("Forhåndsvisning utilgjengelig", '<h1>Forhåndsvisning utilgjengelig</h1>')
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            # Only existing controlled image delivery may leave loopback.
            image_origin = os.environ.get("CHILLOUT_ORIGIN", "")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' https://sjekkpris.no " + image_origin + "; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--core-checkout", required=True, type=Path)
    parser.add_argument("--image-origin", required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if args.bundle.resolve().is_relative_to(ROOT):
        parser.error("private catalogue input must remain outside the repository")
    image = urlsplit(args.image_origin)
    if image.scheme != "https" or image.path or image.query or image.fragment or image.username or image.password or re.search(r"[\s;]", args.image_origin):
        parser.error("a controlled HTTPS image origin is required")
    os.environ["CHILLOUT_ORIGIN"] = args.image_origin
    reader = BundleReader(args.bundle, args.sha256, core_verifier(args.core_checkout))
    reader()  # fail before opening a socket
    server = make_server(reader, args.port)
    print(f"Private preview: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
