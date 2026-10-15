"""Build the SjekkPris.no beta site from Chillout's read API.

Build time only. The browser never calls Chillout: every page is static HTML
rendered here, and the read key exists only in this process's environment.

Inputs, all from the environment:

- `CHILLOUT_ORIGIN`   Chillout's base URL (a GitHub Actions variable).
- `CHILLOUT_READ_KEY` the property-scoped read key (a GitHub Actions secret).
                      Sent only as an `Authorization` header. Never printed,
                      never written to a file.
- `BASE_PATH`         where the site is served: `/sjekkpris-no/` for the
                      GitHub Pages preview, `/` once sjekkpris.no points here.
- `ROBOTS_NOINDEX`    `1` (default) marks every page noindex while in beta.

Truthfulness rules this file follows, because the platform's data carries them:

- A `null` price is "no price", never 0.
- An offer marked stale or out of stock says so; nothing is shown as in stock
  unless the source positively stated it.
- "Laveste pris" is shown only on the offer the API names as holding the
  claim. This file never computes a minimum of its own.
- A shop link is rendered only where Chillout says the offer can be reached
  (`link.clickout_available` and a well-formed `clickout_url`) **and** the
  offer is eligible to hold the lowest-price claim. Stale, out-of-stock,
  withdrawn and excluded offers stay visible and are not clickable. The link
  is `https://sjekkpris.no` + Chillout's relative `clickout_url`, used exactly;
  a provider URL is never rendered.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from catalogue_media import image_markup, category_markup

PROPERTY = "sjekkpris-no"
#: Where `/go/` is served. Clickout links are absolute on this origin even on
#: the github.io preview, because the edge exists only here.
SITE_ORIGIN = "https://sjekkpris.no"
#: Chillout's `clickout_url`, exactly: `/go/` and a target token (`tgt_` and a
#: 26-character ULID). Anything else renders no link.
CLICKOUT_PATH = re.compile(r"^/go/tgt_[0-9A-HJKMNP-TV-Z]{26}$")
TIMEOUT_SECONDS = 30
OSLO = ZoneInfo("Europe/Oslo")

#: Currencies whose minor unit is 1/100. Anything else fails the build rather
#: than rendering an amount at the wrong scale.
TWO_DECIMAL_CURRENCIES = {"NOK", "SEK", "DKK", "EUR"}

#: What a property may use as a path segment. The API's slugs already satisfy
#: this; anything else fails the build instead of producing a broken URL.
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

AVAILABILITY = {
    "in_stock": "På lager",
    "out_of_stock": "Ikke på lager",
    "preorder": "Forhåndsbestilling",
    "backorder": "Restordre",
    "unknown": "Lagerstatus ukjent",
}

EXCLUSION = {
    "excluded_currency_mismatch": "Annen valuta – ikke sammenlignbar",
    "excluded_vat_basis_unknown": "Ukjent mva-grunnlag – ikke sammenlignbar",
}


class BuildError(RuntimeError):
    """A reason the build must stop. Never carries the key."""


# -- reading ---------------------------------------------------------------


class Chillout:
    def __init__(self, origin: str, key: str) -> None:
        if not origin:
            raise BuildError("CHILLOUT_ORIGIN is not set")
        if not key:
            raise BuildError("CHILLOUT_READ_KEY is not set")
        self._origin = origin.rstrip("/")
        self._key = key
        self.requests = 0

    def get(self, path: str) -> dict:
        request = urllib.request.Request(
            self._origin + path,
            headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json"},
        )
        self.requests += 1
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # The path only: it carries no credential, and the origin's
            # hostname is kept out of logs as it is out of output.
            raise BuildError(f"{path} answered HTTP {exc.code}") from None
        except urllib.error.URLError as exc:
            raise BuildError(f"{path} could not be reached ({exc.reason})") from None


def catalogue(client: Chillout) -> list[dict]:
    body = client.get(f"/api/v1/properties/{PROPERTY}/catalogue?locale=nb")
    return list(body.get("products") or [])


def comparison(client: Chillout, namespace: str, slug: str) -> dict:
    ns = urllib.parse.quote(namespace, safe="")
    local = urllib.parse.quote(slug, safe="")
    return client.get(f"/api/v1/properties/{PROPERTY}/catalogue/{ns}/{local}/offers?locale=nb")


# -- formatting ------------------------------------------------------------


def money(amount: dict | None) -> str | None:
    """`{"minor": 47500, "currency": "NOK"}` as `NOK 475,-`. `None` stays `None`."""
    if amount is None:
        return None
    currency = str(amount["currency"])
    if currency not in TWO_DECIMAL_CURRENCIES:
        raise BuildError(f"no rendering rule for currency {currency!r}")
    minor = int(amount["minor"])
    major, cents = divmod(minor, 100)
    if currency == "NOK":
        grouped = f"{major:,}".replace(",", " ")
        return f"NOK {grouped},-" if cents == 0 else f"NOK {grouped},{cents:02d}"
    # Other currencies keep their own convention; the Scandinavian `,-` is
    # never applied mechanically.
    return f"{currency} {major}.{cents:02d}"


def day(iso: str | None) -> str | None:
    if not iso:
        return None
    return datetime.fromisoformat(iso).astimezone(OSLO).strftime("%d.%m.%Y")


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def segment(value: str) -> str:
    if not SAFE_SEGMENT.match(value or ""):
        raise BuildError(f"unexpected identifier {value!r} from the catalogue")
    return value


# -- rendering -------------------------------------------------------------


def page(title: str, body: str, *, base: str, noindex: bool) -> str:
    robots = '<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robots}
<title>{e(title)}</title>
<link rel="stylesheet" href="{e(base)}style.css">
</head>
<body>
<header><a class="brand" href="{e(base)}">SjekkPris.no</a> <span class="beta">Beta</span></header>
<main>
{body}
</main>
<footer>Prisene hentes fra annonsørenes produktfeeder. Beta – innholdet er under utvikling.</footer>
</body>
</html>
"""


def index_body(products: list[dict], *, base: str) -> str:
    if not products:
        return "<h1>Produkter</h1>\n<p>Ingen produkter er publisert ennå.</p>"
    rows = []
    for product in products:
        ns, slug = segment(product["namespace"]), segment(product["local_slug"])
        href = f"{base}p/{ns}/{slug}/"
        price = money(product.get("lowest_item_price"))
        confirmed = day(product.get("lowest_item_price_confirmed_at"))
        count = int(product.get("offer_count") or 0)
        rows.append(
            "<tr>"
            f'<td><a href="{e(href)}">{e(product.get("local_name") or slug)}</a></td>'
            f"<td>{e(price) if price else '<span class=muted>Ingen pris</span>'}</td>"
            f"<td>{e(confirmed) if confirmed else ''}</td>"
            f"<td>{count} tilbud</td>"
            "</tr>"
        )
    return (
        "<h1>Produkter</h1>\n<table>\n"
        "<thead><tr><th>Produkt</th><th>Laveste pris</th><th>Pris bekreftet</th>"
        "<th>Tilbud</th></tr></thead>\n<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>"
    )


def shipping_text(offer: dict) -> str:
    shipping = offer.get("shipping") or {}
    terms = shipping.get("terms") or {}
    state = shipping.get("state")
    if terms.get("is_test_data"):
        # A claim resting on test terms is not a fact a shopper may be shown.
        return "Frakt ikke bekreftet"
    if state == "confirmed_free":
        return "Fri frakt"
    if state == "known_amount" and shipping.get("amount"):
        return f"Frakt {money(shipping['amount'])}"
    return "Frakt ukjent"


def total_text(offer: dict) -> str:
    total = offer.get("known_total_price")
    shipping = offer.get("shipping") or {}
    if total is None or (shipping.get("terms") or {}).get("is_test_data"):
        return "Totalpris ukjent"
    return money(total) or "Totalpris ukjent"


def notes(offer: dict) -> list[str]:
    found = []
    if offer.get("stale"):
        when = day(offer.get("last_confirmed_at"))
        found.append(f"Ikke bekreftet nylig{f' (sist {when})' if when else ''}")
    if offer.get("withdrawn"):
        found.append("Ikke lenger i annonsørens feed")
    return found


def shop_href(offer: dict, *, excluded: bool) -> str | None:
    """The offer's clickout link, or `None` where it must not be clickable."""
    link = offer.get("link") or {}
    path = link.get("clickout_url")
    if not link.get("clickout_available") or not isinstance(path, str):
        return None
    if not CLICKOUT_PATH.match(path):
        return None
    eligible = ((offer.get("ranking") or {}).get("item_price") or {}).get("ranking_eligible")
    if excluded or eligible is not True:
        return None
    return SITE_ORIGIN + path


def offer_row(offer: dict, *, lowest: str | None, excluded: bool) -> str:
    price = money(offer.get("item_price"))
    availability = AVAILABILITY.get(
        (offer.get("availability") or {}).get("status"), "Lagerstatus ukjent"
    )
    marks = notes(offer)
    if excluded:
        marks.insert(0, EXCLUSION.get(offer.get("comparison_status"), "Ikke sammenlignbar"))
    badge = (
        ' <span class="badge">Laveste pris</span>'
        if not excluded and lowest and offer.get("offer_id") == lowest
        else ""
    )
    return (
        "<tr>"
        f"<td>{e(offer.get('advertiser') or 'Ukjent annonsør')}</td>"
        f"<td>{e(price) if price else '<span class=muted>Ingen pris</span>'}{badge}</td>"
        f"<td>{e(shipping_text(offer))}</td>"
        f"<td>{e(total_text(offer))}</td>"
        f"<td>{e(availability)}</td>"
        f"<td>{'<br>'.join(e(m) for m in marks)}</td>"
        f"<td>{shop_cell(offer, excluded=excluded)}</td>"
        "</tr>"
    )


def shop_cell(offer: dict, *, excluded: bool) -> str:
    href = shop_href(offer, excluded=excluded)
    if href is None:
        return '<span class="muted">Ingen lenke</span>'
    return f'<a class="shop" href="{e(href)}" rel="sponsored nofollow">Til butikken</a>'



def product_body(product: dict, body: dict, *, base: str) -> str:
    name = (body.get("identity") or {}).get("local_name") or product.get("local_name")
    lowest = body.get("lowest_item_price")
    offers = body.get("offers") or []
    excluded = body.get("excluded") or []
    head = (
        "<tr><th>Butikk</th><th>Pris</th><th>Frakt</th><th>Totalpris</th>"
        "<th>Lager</th><th>Merknad</th><th></th></tr>"
    )
    parts = [f'<p><a href="{e(base)}">← Alle produkter</a></p>', f"<h1>{e(name)}</h1>"]
    identity = body.get("identity") or {}
    image = image_markup(identity.get("image"), name, sizes="(max-width: 600px) 100vw, 360px", eager=True)
    if image:
        parts.append(f'<div class="product-image">{image}</div>')
    if identity.get("local_brand"):
        parts.append(f'<p>Merke: {e(identity["local_brand"])}</p>')
    parts.append(category_markup(identity.get("categories"), full=True))
    if not offers and not excluded:
        parts.append("<p>Ingen tilbud akkurat nå.</p>")
    if offers:
        rows = "\n".join(offer_row(o, lowest=lowest, excluded=False) for o in offers)
        parts.append(f"<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")
    if excluded:
        rows = "\n".join(offer_row(o, lowest=None, excluded=True) for o in excluded)
        parts.append("<h2>Ikke sammenlignbare tilbud</h2>")
        parts.append(f"<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")
    return "\n".join(parts)


STYLE = """
.product-image { max-width:360px; margin:24px 0 }
.product-image img { display:block; width:100%; max-height:360px; object-fit:contain }

body{font:16px/1.5 system-ui,sans-serif;margin:0;color:#1d1d1f;background:#fff}
header,main,footer{max-width:960px;margin:0 auto;padding:16px}
header{border-bottom:1px solid #ddd}
.brand{font-weight:700;color:inherit;text-decoration:none}
.beta,.badge{font-size:12px;padding:2px 6px;border-radius:4px;background:#eef;color:#224}
.badge{background:#e6f4ea;color:#14532d;margin-left:6px}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:8px;border-bottom:1px solid #eee;vertical-align:top}
.muted{color:#777}
.shop{display:inline-block;padding:4px 10px;border-radius:4px;background:#1d4ed8;color:#fff;text-decoration:none}
footer{color:#777;font-size:14px;border-top:1px solid #ddd}
"""


# -- the build -------------------------------------------------------------


def normalise_base(value: str) -> str:
    value = "/" + value.strip().strip("/") + "/"
    return "/" if value == "//" else value


def build(client: Chillout, out: Path, *, base: str, noindex: bool) -> int:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "style.css").write_text(STYLE.lstrip(), encoding="utf-8")

    products = catalogue(client)
    from home_release import write_home
    (out / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).resolve().parent / 'assets' / 'sjekkpris-startside.webp', out / 'assets' / 'sjekkpris-startside.webp')
    write_home(products, out, base=base, noindex=noindex, day=day, segment=segment)
    for product in products:
        ns, slug = segment(product["namespace"]), segment(product["local_slug"])
        body = comparison(client, ns, slug)
        target = out / "p" / ns / slug
        target.mkdir(parents=True, exist_ok=True)
        title = f"{product.get('local_name') or slug} – SjekkPris.no"
        (target / "index.html").write_text(
            page(title, product_body(product, body, base=base), base=base, noindex=noindex),
            encoding="utf-8",
        )
    (out / "404.html").write_text(
        page("Fant ikke siden – SjekkPris.no", "<h1>Fant ikke siden</h1>", base=base,
             noindex=True),
        encoding="utf-8",
    )
    return len(products)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="_site")
    args = parser.parse_args(argv)
    base = normalise_base(os.environ.get("BASE_PATH", "/"))
    noindex = os.environ.get("ROBOTS_NOINDEX", "1") != "0"
    try:
        client = Chillout(
            os.environ.get("CHILLOUT_ORIGIN", ""), os.environ.get("CHILLOUT_READ_KEY", "")
        )
        count = build(client, Path(args.out), base=base, noindex=noindex)
    except BuildError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1
    print(f"built {count} product page(s) at base {base} with {client.requests} request(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())


