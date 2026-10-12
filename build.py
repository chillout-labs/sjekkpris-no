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
    body = client.get(f"/api/v1/properties/{PROPERTY}/catalogue")
    return list(body.get("products") or [])


def comparison(client: Chillout, namespace: str, slug: str) -> dict:
    ns = urllib.parse.quote(namespace, safe="")
    local = urllib.parse.quote(slug, safe="")
    return client.get(f"/api/v1/properties/{PROPERTY}/catalogue/{ns}/{local}/offers")


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
        return f"{grouped} kr" if cents == 0 else f"{grouped},{cents:02d} kr"
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
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
{robots}
<title>{e(title)}</title>
<link rel="stylesheet" href="{e(base)}style.css">
</head>
<body>
<header>
<div class="container topbar">
<a class="brand" href="{e(base)}" aria-label="SjekkPris"><span>S</span>jekkPris</a>
<p class="tagline">Smartere valg. Mer for pengene.</p>
<button id="menu-toggle" class="menu-button" aria-expanded="false" aria-controls="menu-panel">
<svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"/></svg>
<span>Meny</span>
</button>
<nav id="menu-panel" class="menu-panel" aria-label="Hovedmeny" hidden>
<a href="#prices">Butikker og priser</a>
<a href="#history">Prishistorikk</a>
<a href="#about">Om produktet</a>
<a href="#specifications">Spesifikasjoner</a>
</nav>
</div>
<div class="search-bar">
<div class="container">
<form id="search-form" role="search" class="search-form-horizontal">
<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
</svg>
<input id="query" aria-label="Søk etter produkter" placeholder="Søk etter produkter, merker, kategorier …" autocomplete="off">
<button aria-label="Søk"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
<path d="m5 12 7-7 7 7"/></svg></button>
</form>
<div id="search-result" class="search-result" role="status" hidden></div>
</div>
</div>
<div class="categories">
<div class="container">
<span><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h8v8H3zm10 0h8v8h-8zm0 10h8v8h-8zM3 13h8v8H3z"/></svg>Alle kategorier</span>
<span>Elektronikk</span><span>Hjem og husholdning</span><span>Sport og fritid</span>
<span>Skjønnhet og helse</span><span>Barn og familie</span><span>Hage og utemiljø</span>
</div>
</div>
</header>
<main class="container" id="product">
<div class="main-container">
{body}
</div>
</main>
<footer>
<div class="container">
<p>Prisene hentes fra annonsørenes produktfeeder. Beta – innholdet er under utvikling.</p>
</div>
</footer>
</body>
</html>
"""


def index_body(products: list[dict], *, base: str) -> str:
    if not products:
        return "<h1>Hva vil du sammenligne?</h1>\n<p>Søk etter et produkt, eller beskriv hva du trenger.</p>\n<p>Ingen produkter er publisert ennå.</p>"

    # Build example chips from diverse products in the catalog
    # Select products for example chips (e.g., first, middle, last)
    example_indices = [0]
    if len(products) > 2:
        example_indices.append(len(products) // 2)
    if len(products) > 1:
        example_indices.append(len(products) - 1)
    example_indices = list(dict.fromkeys(example_indices))  # Remove duplicates while preserving order

    example_chips = []
    for idx in example_indices[:3]:  # Limit to 3 example chips
        if idx < len(products):
            product = products[idx]
            name = product.get("local_name") or product.get("local_slug")
            ns, slug = segment(product["namespace"]), segment(product["local_slug"])
            href = f"{base}p/{ns}/{slug}/"
            example_chips.append(f'<a href="{e(href)}" class="chip">{e(name)}</a>')

    examples_html = "\n".join(example_chips)

    # Build product table
    rows = []
    for product in products:
        ns, slug = segment(product["namespace"]), segment(product["local_slug"])
        href = f"{base}p/{ns}/{slug}/"
        price = money(product.get("lowest_item_price"))
        confirmed = day(product.get("lowest_item_price_confirmed_at"))
        count = int(product.get("offer_count") or 0)
        offer_text = "1 tilbud" if count == 1 else f"{count} tilbud"
        rows.append(
            "<tr>"
            f'<td><a href="{e(href)}">{e(product.get("local_name") or slug)}</a></td>'
            f"<td>{e(price) if price else '<span class=\"muted\">Ingen pris</span>'}</td>"
            f"<td>{e(confirmed) if confirmed else ''}</td>"
            f"<td><span class=\"text-sm\">{e(offer_text)}</span></td>"
            "</tr>"
        )

    table_html = (
        "<h2>Produkter</h2>\n<p class=\"text-sm\">Søket finner foreløpig produkter etter navn. Kategoribrowsing og behovssøk kommer når datagrunnlaget er klart.</p>\n<table>\n"
        "<thead><tr><th>Produkt</th><th>Laveste pris</th><th>Pris bekreftet</th>"
        "<th>Tilbud</th></tr></thead>\n<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>"
    )

    # Build the complete homepage HTML
    return (
        "<section class=\"search-section\">"
        "<h1>Hva vil du sammenligne?</h1>"
        "<p>Søk etter et produkt, eller beskriv hva du trenger.</p>"
        "<div class=\"search-form-container\">"
        '<form id="search-form" class="search-form">'
        '<input type="text" id="search-input" class="search-input" placeholder="Søk eller beskriv hva du ser etter …" autocomplete="off">'
        '<button type="submit" class="search-button" aria-label="Søk">🔍</button>'
        "</form>"
        '<div id="autocomplete-results" class="autocomplete-results" role="listbox" aria-label="Søkeforslag"></div>'
        "</div>"
        "<div class=\"examples\">"
        f"<p><strong>Prøv for eksempel:</strong></p>"
        f"<div class=\"chips\">{examples_html}</div>"
        "</div>"
        "</section>"
        + table_html +
        "<script>" +
        """
        (function() {
            const searchInput = document.getElementById('search-input');
            const searchForm = document.getElementById('search-form');
            const autocompleteResults = document.getElementById('autocomplete-results');
            const chips = document.querySelectorAll('.chip');
            let searchIndex = null;
            let selectedIndex = -1;

            // Load search index
            fetch('""" + e(base) + """search-index.json')
                .then(r => r.json())
                .then(data => { searchIndex = data; })
                .catch(err => console.error('Failed to load search index:', err));

            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            function performSearch(query) {
                if (!searchIndex) return [];
                const lower = query.toLowerCase();
                return searchIndex.filter(item =>
                    item.name.toLowerCase().includes(lower)
                ).slice(0, 8);
            }

            function renderAutocomplete(results) {
                autocompleteResults.innerHTML = '';
                selectedIndex = -1;
                if (!results.length) return;

                results.forEach((item, idx) => {
                    const div = document.createElement('div');
                    div.className = 'autocomplete-item';
                    div.textContent = item.name;
                    div.setAttribute('data-url', item.url);
                    div.setAttribute('data-index', idx);
                    div.addEventListener('click', () => window.location.href = item.url);
                    autocompleteResults.appendChild(div);
                });
                autocompleteResults.classList.add('visible');
            }

            function setSelectedIndex(idx) {
                const items = autocompleteResults.querySelectorAll('.autocomplete-item');
                items.forEach(item => item.classList.remove('selected'));
                if (idx >= 0 && idx < items.length) {
                    items[idx].classList.add('selected');
                    items[idx].scrollIntoView({ block: 'nearest' });
                }
                selectedIndex = idx;
            }

            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                if (query.length < 1) {
                    autocompleteResults.classList.remove('visible');
                    return;
                }
                const results = performSearch(query);
                renderAutocomplete(results);
            });

            searchInput.addEventListener('keydown', (e) => {
                const items = autocompleteResults.querySelectorAll('.autocomplete-item');
                if (!items.length) return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setSelectedIndex(Math.min(selectedIndex + 1, items.length - 1));
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    setSelectedIndex(Math.max(selectedIndex - 1, -1));
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (selectedIndex >= 0 && selectedIndex < items.length) {
                        window.location.href = items[selectedIndex].getAttribute('data-url');
                    } else {
                        // Show results page with all matches
                        const query = searchInput.value.trim();
                        if (query.length > 0) {
                            window.location.href = '""" + e(base) + """search?q=' + encodeURIComponent(query);
                        }
                    }
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    autocompleteResults.classList.remove('visible');
                    selectedIndex = -1;
                }
            });

            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query.length > 0) {
                    window.location.href = '""" + e(base) + """search?q=' + encodeURIComponent(query);
                }
            });

            chips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.preventDefault();
                    window.location.href = chip.getAttribute('href');
                });
            });
        })();
        """ +
        "</script>"
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


def find_offer_by_id(offers: list[dict], excluded: list[dict], offer_id: str | None) -> dict | None:
    """Find an offer by offer_id from both active and excluded lists."""
    if not offer_id:
        return None
    for o in offers:
        if o.get("offer_id") == offer_id:
            return o
    for o in excluded:
        if o.get("offer_id") == offer_id:
            return o
    return None


def find_lowest_total_price_offer(offers: list[dict], lowest_total_id: str | None) -> dict | None:
    """Find the lowest total price offer, validating it has a known total price.

    Per brief section 6.1: reference must exist, total must be known, ranking for
    total_price must allow claim, and shipping.terms.is_test_data must not be true.
    """
    if not lowest_total_id:
        return None

    offer = find_offer_by_id(offers, [], lowest_total_id)
    if not offer:
        return None

    # Check if total price is known
    if offer.get("known_total_price") is None:
        return None

    # Check shipping terms (test data not allowed)
    shipping = offer.get("shipping") or {}
    if (shipping.get("terms") or {}).get("is_test_data"):
        return None

    # Check ranking eligibility for total price
    ranking = offer.get("ranking") or {}
    total_ranking = (ranking.get("total_price") or {}).get("ranking_eligible")
    if total_ranking is not True:
        return None

    return offer


def find_hero_offer(offers: list[dict], lowest_total_id: str | None, lowest_item_id: str | None) -> tuple[dict | None, str]:
    """Find the best offer for the price hero, with fallback logic per Brief §6.

    Returns (offer, price_type) where price_type is "total", "item", or "none".

    Priority:
    1. Valid lowest_known_total_price (label: "Laveste totalpris på")
    2. Valid lowest_item_price with item_price ranking (label: "Laveste varepris", with shipping status)
    3. None (label: no winner)
    """
    # Try total price first
    total_offer = find_lowest_total_price_offer(offers, lowest_total_id)
    if total_offer:
        return (total_offer, "total")

    # Fallback to item price
    if lowest_item_id:
        item_offer = find_offer_by_id(offers, [], lowest_item_id)
        if item_offer:
            # Check if item price is ranking eligible
            ranking = item_offer.get("ranking") or {}
            item_ranking = (ranking.get("item_price") or {}).get("ranking_eligible")
            if item_ranking is True:
                # Check shipping terms aren't test data
                shipping = item_offer.get("shipping") or {}
                if not (shipping.get("terms") or {}).get("is_test_data"):
                    return (item_offer, "item")

    return (None, "none")


def render_product_image(identity: dict) -> str:
    """Render the product image or fallback 'Bilde mangler' placeholder.

    Left column of 3-column hero (desktop) or top (mobile).
    """
    image = identity.get("image") or {}
    url = image.get("url")

    if url:
        return (
            '<div class="product-image">'
            f'<img src="{e(url)}" alt="Produktbilde" style="object-fit: contain; width: 100%; height: auto;">'
            '</div>'
        )
    else:
        return (
            '<div class="product-image" style="display: flex; align-items: center; justify-content: center; '
            'background-color: var(--color-surface); border-radius: var(--radius-md); min-height: 300px;">'
            '<div style="text-align: center; color: var(--color-text-muted);">'
            '<p style="margin: 0; font-size: var(--font-size-lg);">Bilde mangler</p>'
            '</div>'
            '</div>'
        )


def render_price_hero(offer: dict, price_type: str) -> str:
    """Render the price hero card (right column of 3-column hero).

    price_type: "total" (total price winner), "item" (item price fallback), or "none" (no winner)

    Per Brief §6:
    - Total: show "Laveste totalpris på" with total price and "Inkl. frakt"
    - Item: show "Laveste varepris" with item price and shipping status
    - None: show empty/no-winner state
    """
    advertiser = e(offer.get("advertiser") or "butikken")
    item_price = money(offer.get("item_price"))
    total_price = money(offer.get("known_total_price"))
    availability = AVAILABILITY.get(
        (offer.get("availability") or {}).get("status"), "Lagerstatus ukjent"
    )
    href = shop_href(offer, excluded=False)

    # Build the hero card HTML
    html_parts = [
        '<div class="price-hero">',
        '<div class="price-header">',
    ]

    # Determine label and price display based on type
    if price_type == "total":
        html_parts.append('<span class="badge badge-lowest-total">Laveste kjente totalpris</span>')
        price_html = f'<div class="price-amount">{e(total_price)}</div>'
        item_info = f'Varepris + frakt · {e(advertiser)}'
    elif price_type == "item":
        html_parts.append('<span class="badge badge-lowest-item">Laveste varepris</span>')
        price_html = f'<div class="price-amount">{e(item_price)}</div>'
        item_info = e(advertiser)
    else:
        html_parts.append('<span class="badge" style="background-color: var(--color-surface);">Pris ukjent</span>')
        price_html = '<div class="price-amount" style="color: var(--color-text-muted);">Ingen vinner</div>'
        item_info = ''

    html_parts.append('</div>')

    # Price display (large, centered)
    html_parts.append('<div class="price-display">')
    html_parts.append(price_html)
    html_parts.append('</div>')

    # Item info on single line
    if item_info:
        html_parts.append(f'<div class="price-info">{e(item_info)}</div>')

    if price_type != "none":
        # Info row: shipping, availability, confirmed date (all on one line)
        info_parts = []

        # Shipping
        shipping_label = shipping_text(offer)
        if shipping_label:
            info_parts.append(e(shipping_label))

        # Availability
        if availability:
            info_parts.append(e(availability))

        # Last confirmed
        confirmed = day(offer.get("last_confirmed_at"))
        if confirmed:
            info_parts.append(f"Bekreftet {e(confirmed)}")

        if info_parts:
            html_parts.append(f'<div class="price-info-row">{" · ".join(info_parts)}</div>')

        # Add CTA button
        html_parts.append('<div class="hero-cta">')
        if href:
            html_parts.append(
                f'<a href="{e(href)}" class="shop shop-hero" rel="sponsored nofollow">'
                f'Gå til butikken</a>'
            )
        else:
            html_parts.append('<div class="text-sm muted">Lenke ikke tilgjengelig</div>')
        html_parts.append('</div>')

    html_parts.append('</div>')

    return "\n".join(html_parts)


def offer_row(offer: dict, *, lowest: str | None, excluded: bool) -> str:
    price = money(offer.get("item_price"))
    availability = AVAILABILITY.get(
        (offer.get("availability") or {}).get("status"), "Lagerstatus ukjent"
    )
    marks = notes(offer)
    if excluded:
        marks.insert(0, EXCLUSION.get(offer.get("comparison_status"), "Ikke sammenlignbar"))
    badge = (
        ' <span class="badge badge-price">Laveste pris</span>'
        if not excluded and lowest and offer.get("offer_id") == lowest
        else ""
    )
    marks_html = (
        '<div class="text-xs">' + '<br>'.join(e(m) for m in marks) + '</div>'
        if marks else ''
    )
    return (
        "<tr>"
        f"<td>{e(offer.get('advertiser') or 'Ukjent annonsør')}</td>"
        f"<td>{e(price) if price else '<span class=\"muted\">Ingen pris</span>'}{badge}</td>"
        f"<td><span class=\"text-sm\">{e(shipping_text(offer))}</span></td>"
        f"<td><span class=\"text-sm\">{e(total_text(offer))}</span></td>"
        f"<td><span class=\"text-sm\">{e(availability)}</span></td>"
        f"<td>{marks_html}</td>"
        f"<td>{shop_cell(offer, excluded=excluded)}</td>"
        "</tr>"
    )


def shop_cell(offer: dict, *, excluded: bool) -> str:
    href = shop_href(offer, excluded=excluded)
    if href is None:
        return '<span class="text-sm muted">Ingen lenke</span>'
    advertiser = e(offer.get('advertiser') or 'butikken')
    return f'<a class="shop" href="{e(href)}" rel="sponsored nofollow">Gå til {advertiser}</a>'



def search_results_body(*, base: str) -> str:
    """Generate the search results page that uses client-side filtering."""
    return (
        "<section id=\"search-results-section\">"
        "<h1>Søkeresultater</h1>"
        '<form id="search-form-results" class="search-form" style="margin-bottom: var(--space-xl);">'
        '<input type="text" id="search-input-results" class="search-input" placeholder="Søk etter et produkt …" autocomplete="off">'
        '<button type="submit" class="search-button" aria-label="Søk">🔍</button>'
        "</form>"
        '<div id="results-container" style="margin-top: var(--space-xl);"></div>'
        "</section>"
        "<script>" +
        """
        (function() {
            const searchInput = document.getElementById('search-input-results');
            const resultsContainer = document.getElementById('results-container');
            const searchForm = document.getElementById('search-form-results');
            let searchIndex = null;

            // Get query from URL parameters
            const params = new URLSearchParams(window.location.search);
            const initialQuery = params.get('q') || '';

            // Load search index
            fetch('""" + e(base) + """search-index.json')
                .then(r => r.json())
                .then(data => {
                    searchIndex = data;
                    searchInput.value = initialQuery;
                    if (initialQuery) {
                        performSearch(initialQuery);
                    } else {
                        resultsContainer.innerHTML = '<p>Skriv inn et søk for å komme i gang.</p>';
                    }
                })
                .catch(err => {
                    console.error('Failed to load search index:', err);
                    resultsContainer.innerHTML = '<p>Kunne ikke laste søkdata. Vennligst prøv igjen.</p>';
                });

            function performSearch(query) {
                if (!searchIndex) return;
                const lower = query.toLowerCase();
                const results = searchIndex.filter(item =>
                    item.name.toLowerCase().includes(lower)
                );

                if (results.length === 0) {
                    resultsContainer.innerHTML = '<p>Ingen produkter funnet for "' +
                        query.replace(/</g, '&lt;').replace(/>/g, '&gt;') +
                        '". Prøv en annen søketerm.</p>' +
                        '<p><a href="""" + e(base) + """">← Tilbake til oversikt</a></p>';
                } else {
                    const rows = results.map(item => {
                        return '<tr>' +
                            '<td><a href="' + item.url.replace(/"/g, '&quot;') + '">' +
                            item.name.replace(/</g, '&lt;').replace(/>/g, '&gt;') +
                            '</a></td>' +
                            '</tr>';
                    }).join('');
                    resultsContainer.innerHTML = '<p>' + results.length + ' produkt(er) funnet:</p>' +
                        '<table><thead><tr><th>Produkt</th></tr></thead><tbody>' + rows + '</tbody></table>';
                }
            }

            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const query = searchInput.value.trim();
                if (query.length > 0) {
                    window.history.pushState({}, '', '""" + e(base) + """search?q=' + encodeURIComponent(query));
                    performSearch(query);
                }
            });
        })();
        """ +
        "</script>"
    )


def product_body(product: dict, body: dict, *, base: str) -> str:
    name = (body.get("identity") or {}).get("local_name") or product.get("local_name")
    identity = body.get("identity") or {}
    lowest = body.get("lowest_item_price")
    lowest_total = body.get("lowest_known_total_price")
    offers = body.get("offers") or []
    excluded = body.get("excluded") or []
    head = (
        "<tr><th>Butikk</th><th>Pris</th><th>Frakt</th><th>Totalpris</th>"
        "<th>Lager</th><th>Merknad</th><th></th></tr>"
    )

    parts = []

    # Breadcrumb navigation
    parts.append('<nav class="breadcrumb" aria-label="Brødsmulesti">')
    parts.append('<span>Hjem</span>')
    if identity.get("local_category"):
        parts.append(f'<span>{e(identity["local_category"])}</span>')
    parts.append(f'<span>{e(name)}</span>')
    parts.append('</nav>')

    # Hero section: 3-column layout on desktop, single column on mobile
    hero_parts = []
    hero_parts.append('<section class="product-hero">')

    # Identity metadata (computed once for both mobile and desktop)
    meta_parts = []
    if identity.get("local_brand"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Merke:</strong> {e(identity['local_brand'])}</span>")
    if identity.get("local_category"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Kategori:</strong> {e(identity['local_category'])}</span>")
    if identity.get("local_pack_size"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Pakning:</strong> {e(identity['local_pack_size'])}</span>")

    # Mobile: product name before image
    hero_parts.append('<div class="hero-title-mobile">')
    hero_parts.append(f"<h1>{e(name)}</h1>")
    if meta_parts:
        hero_parts.append(f"<div class=\"product-meta\">{' '.join(meta_parts)}</div>")
    hero_parts.append('</div>')

    # Left column: product image
    hero_parts.append('<div class="hero-column hero-image">')
    hero_parts.append(render_product_image(identity))
    hero_parts.append('</div>')

    # Middle column: product info (desktop only)
    hero_parts.append('<div class="hero-column hero-info-column">')
    hero_parts.append(f"<h1 class=\"hidden-mobile\">{e(name)}</h1>")
    # No duplicate metadata here - reuse on desktop via CSS display control

    hero_parts.append('</div>')

    # Right column: price hero
    # Use fallback logic per Brief §6: total price → item price → no winner
    if offers:
        hero_offer, price_type = find_hero_offer(offers, lowest_total, lowest)
        if hero_offer or price_type == "none":
            hero_parts.append('<div class="hero-column hero-price">')
            if hero_offer:
                hero_parts.append(render_price_hero(hero_offer, price_type))
            else:
                # No offers qualify, show empty state
                hero_parts.append(render_price_hero({}, "none"))
            hero_parts.append('</div>')

    hero_parts.append('</section>')

    parts.append("\n".join(hero_parts))

    # Section navigation
    parts.append('<nav class="section-nav" aria-label="Produktseksjoner">')
    parts.append('<a href="#prices">Priser</a>')
    parts.append('<a href="#history">Prishistorikk</a>')
    parts.append('<a href="#about">Om produktet</a>')
    parts.append('<a href="#specifications">Spesifikasjoner</a>')
    parts.append('</nav>')

    # Offers section with anchor
    if not offers and not excluded:
        parts.append("<h2 id=\"prices\">Butikker og priser</h2>")
        parts.append("<p>Ingen tilbud akkurat nå.</p>")
    else:
        parts.append("<h2 id=\"prices\">Butikker og priser</h2>")
        if offers:
            rows = "\n".join(offer_row(o, lowest=lowest, excluded=False) for o in offers)
            parts.append(f"<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")
        if excluded:
            rows = "\n".join(offer_row(o, lowest=None, excluded=True) for o in excluded)
            parts.append("<h3>Ikke sammenlignbare tilbud</h3>")
            parts.append(f"<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")

    # Price history section (empty state)
    parts.append("<h2 id=\"history\">Prishistorikk</h2>")
    parts.append('<div class="empty-history">')
    parts.append('<svg aria-hidden="true" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">')
    parts.append('<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>')
    parts.append('</svg>')
    parts.append('<p>Prishistorikk kommer snart</p>')
    parts.append('</div>')

    # About section
    parts.append("<h2 id=\"about\">Om produktet</h2>")
    parts.append('<div class="empty-about">')
    parts.append('<p>Mer informasjon om produktet kommer snart</p>')
    parts.append('</div>')

    # Specifications section
    parts.append("<h2 id=\"specifications\">Spesifikasjoner</h2>")
    parts.append('<div class="empty-specs">')
    parts.append('<p>Spesifikasjoner kommer snart</p>')
    parts.append('</div>')

    return "\n".join(parts)


STYLE = """
/* CSS Design Tokens & Layout Foundation
 * SjekkPris Frontend v1 – Approved design package
 */

/* Root tokens: design-package approved colors */
:root {
  /* Primary colors from approved design */
  --ink: #10203b;
  --muted: #586780;
  --green: #006454;
  --mint: #edf8f4;
  --line: #e2e8ef;
  --surface: #f5f8fb;
  --radius: 12px;

  /* Deprecated: keeping for compatibility */
  --color-text-primary: #10203b;
  --color-text-secondary: #586780;
  --color-text-muted: #586780;
  --color-background: #ffffff;
  --color-surface: #f5f8fb;
  --color-border: #e2e8ef;
  --color-accent-teal: #006454;
  --color-accent-teal-light: #edf8f4;
  --color-status-success: #006454;
  --color-status-warning: #d97706;
  --color-status-error: #dc2626;

  /* Spacing scale: 4/8 base */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 24px;
  --space-2xl: 32px;
  --space-3xl: 48px;

  /* Border radius */
  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 24px;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 15px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
  --font-size-2xl: 32px;
  --font-size-3xl: 48px;

  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Shadows: very subtle */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 2px 4px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.1);

  /* Responsive: mobile-first */
  --content-max-width: 1280px;
  --container-padding: var(--space-md);
}

/* Mobile medium breakpoint: 390px */
@media (min-width: 390px) {
  :root {
    --container-padding: var(--space-lg);
  }
}

/* Desktop breakpoint: 1024px */
@media (min-width: 1024px) {
  :root {
    --container-padding: var(--space-xl);
  }
}

/* Dark mode support (basic; extends light token values) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-text-primary: #e8eaed;
    --color-text-secondary: #aab0b6;
    --color-text-muted: #808a90;
    --color-background: #202124;
    --color-surface: #292a2d;
    --color-border: #3f4144;
  }
}

/* Base styles */
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  margin: 0;
  padding: 0;
}

/* Typography */
h1 {
  font-size: var(--font-size-2xl);
  line-height: var(--line-height-tight);
  margin: var(--space-lg) 0 var(--space-md);
  font-weight: 600;
}

@media (min-width: 1024px) {
  h1 {
    font-size: var(--font-size-3xl);
    margin: var(--space-xl) 0 var(--space-lg);
  }
}

h2 {
  font-size: 22px;
  line-height: var(--line-height-tight);
  margin: var(--space-lg) 0 var(--space-md);
  font-weight: 600;
}

/* Header styles from approved design package */
header {
  background-color: #ffffff;
  border-bottom: 1px solid var(--line);
}

header .container.topbar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px var(--container-padding);
  max-width: 1280px;
  margin: 0 auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
  text-decoration: none;
  white-space: nowrap;
}

.brand span {
  font-size: 24px;
  background: linear-gradient(135deg, var(--green), var(--ink));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  display: none;
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}

@media (min-width: 768px) {
  .tagline {
    display: block;
  }
}

.search-bar {
  background-color: #ffffff;
  border-bottom: 1px solid var(--line);
  padding: 12px 0;
}

.search-bar .container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--container-padding);
}

.search-form-horizontal {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 8px 12px;
}

.search-form-horizontal svg {
  width: 18px;
  height: 18px;
  color: var(--muted);
  flex-shrink: 0;
}

#query {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  min-width: 200px;
}

.search-form-horizontal button {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: var(--muted);
  display: flex;
  align-items: center;
}

.search-result {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid var(--line);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  max-height: 300px;
  overflow-y: auto;
  z-index: 10;
}

.menu-button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--ink);
  font-size: 14px;
  font-weight: 500;
  margin-left: auto;
}

@media (min-width: 768px) {
  .menu-button {
    display: none;
  }
}

.menu-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  display: flex;
  flex-direction: column;
  padding: 60px 20px;
  z-index: 5;
}

.menu-panel[hidden] {
  display: none !important;
}

.menu-panel a {
  padding: 16px 0;
  color: var(--ink);
  text-decoration: none;
  font-weight: 500;
  border-bottom: 1px solid var(--line);
}

@media (min-width: 768px) {
  .menu-panel {
    position: static;
    background: transparent;
    padding: 0;
    gap: 24px;
    flex-direction: row;
  }

  .menu-panel a {
    padding: 0;
    font-weight: 400;
    font-size: 14px;
    border: none;
  }
}

.categories {
  display: none;
  background-color: var(--surface);
  border-bottom: 1px solid var(--line);
  padding: 12px 0;
}

@media (min-width: 768px) {
  .categories {
    display: block;
  }
}

.categories .container {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 0 var(--container-padding);
  font-size: 13px;
  color: var(--ink);
  max-width: 1280px;
  margin: 0 auto;
}

.categories span {
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

@media (min-width: 1024px) {
  h2 {
    font-size: 26px;
  }
}

h3 {
  font-size: var(--font-size-lg);
  line-height: var(--line-height-tight);
  margin: var(--space-md) 0 var(--space-sm);
  font-weight: 600;
}

p {
  margin: var(--space-md) 0;
}

a {
  color: var(--color-accent-teal);
  text-decoration: none;
}

a:visited {
  color: var(--color-accent-teal);
}

a:hover {
  text-decoration: underline;
}

a:focus {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 2px;
}

/* Layout containers */
.container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: 0 var(--container-padding);
}

/* Header */
header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-md) 0;
}

header .container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}

.brand {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.brand:focus {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 4px;
  border-radius: var(--radius-sm);
}

.beta {
  font-size: var(--font-size-xs);
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  background-color: var(--color-accent-teal-light);
  color: var(--color-status-success);
  font-weight: 600;
  white-space: nowrap;
}

/* Main content */
main {
  min-height: calc(100vh - 200px);
}

.main-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-lg) var(--container-padding);
}

@media (min-width: 390px) {
  .main-container {
    padding: var(--space-xl) var(--container-padding);
  }
}

/* Footer */
footer {
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: var(--space-xl) 0;
  margin-top: var(--space-3xl);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

footer .container {
  text-align: center;
}

footer p {
  margin: 0;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

th {
  background-color: var(--color-surface);
  color: var(--color-text-secondary);
  font-weight: 600;
  text-align: left;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

td {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}

tbody tr:hover {
  background-color: var(--color-surface);
}

/* Responsive table for mobile: card layout */
@media (max-width: 767px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }

  thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  tbody tr {
    margin-bottom: var(--space-lg);
    border: 1px solid var(--line);
    border-radius: var(--radius-sm);
    display: flex;
    flex-direction: column;
    padding: var(--space-lg);
    background-color: #ffffff;
  }

  /* Merchant name and total price at top (side by side) */
  td:first-child {
    order: 1;
    padding: 0 0 var(--space-md) 0;
    border-bottom: 1px solid var(--line);
    font-weight: 600;
    text-align: left;
  }

  td:nth-child(4) {
    order: 2;
    padding: var(--space-md) 0;
    border-bottom: 1px solid var(--line);
    text-align: left;
    font-size: 14px;
  }

  /* Shipping and price details in middle */
  td:nth-child(2),
  td:nth-child(3) {
    order: 3;
    padding: var(--space-md) 0;
    border: none;
    text-align: left;
    display: flex;
    justify-content: space-between;
  }

  /* Availability */
  td:nth-child(5) {
    order: 4;
    padding: var(--space-md) 0;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    text-align: left;
  }

  /* Notes */
  td:nth-child(6) {
    order: 5;
    padding: var(--space-md) 0;
    border: none;
    text-align: left;
    font-size: 12px;
  }

  /* Shop button at bottom */
  td:last-child {
    order: 6;
    padding: var(--space-md) 0 0 0;
    border: none;
    text-align: center;
  }

  td:before {
    content: attr(data-label);
    font-weight: 600;
    text-align: left;
    color: var(--muted);
    font-size: 12px;
    display: none;
  }

  tbody tr:hover {
    background-color: inherit;
    border-color: var(--line);
  }
}

/* Badges */
.badge {
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  margin-left: var(--space-md);
}

.badge-price {
  background-color: var(--color-status-success);
  color: #ffffff;
}

/* Utility classes */
.muted {
  color: var(--color-text-muted);
}

.text-sm {
  font-size: var(--font-size-sm);
}

.text-xs {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Empty states for sections */
.empty-history,
.empty-about,
.empty-specs {
  background-color: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: var(--space-xl);
  text-align: center;
  color: var(--muted);
}

.empty-history svg,
.empty-about svg,
.empty-specs svg {
  display: block;
  margin: 0 auto var(--space-lg);
  color: var(--line);
}

.empty-history p,
.empty-about p,
.empty-specs p {
  margin: 0;
  font-size: var(--font-size-sm);
}

/* Links */
.shop {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  min-width: 44px;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-sm);
  background-color: var(--color-accent-teal);
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  font-size: var(--font-size-sm);
  transition: opacity 0.2s ease;
}

.shop:hover {
  opacity: 0.9;
  text-decoration: none;
}

.shop:focus {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 2px;
}

.shop:active {
  opacity: 0.8;
}

/* Focus visible for keyboard nav */
:focus-visible {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 2px;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Print styles */
@media print {
  header, footer {
    display: none;
  }
}

/* Search section */
.search-section {
  padding: var(--space-xl) 0;
  text-align: center;
  background: linear-gradient(135deg, var(--color-accent-teal-light) 0%, #e0f2fe) 0% 0% / 100% 100%;
}

.search-section h1 {
  font-size: var(--font-size-2xl);
  margin: 0 0 var(--space-md) 0;
  color: var(--color-text-primary);
}

@media (min-width: 768px) {
  .search-section h1 {
    font-size: var(--font-size-3xl);
  }
}

.search-section > p {
  margin: 0 0 var(--space-xl) 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.search-form-container {
  max-width: 500px;
  margin: 0 auto var(--space-2xl);
  position: relative;
}

.search-form {
  display: flex;
  gap: var(--space-sm);
}

.search-input {
  flex: 1;
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  color: var(--color-text-primary);
  background-color: var(--color-background);
  min-height: 44px;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-accent-teal);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.search-button {
  min-width: 44px;
  min-height: 44px;
  padding: var(--space-md) var(--space-lg);
  border: none;
  border-radius: var(--radius-sm);
  background-color: var(--color-accent-teal);
  color: #ffffff;
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.search-button:hover {
  opacity: 0.9;
}

.search-button:focus {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 2px;
}

.search-button:active {
  opacity: 0.8;
}

/* Autocomplete results */
.autocomplete-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  max-height: 400px;
  overflow-y: auto;
  display: none;
  z-index: 10;
  box-shadow: var(--shadow-lg);
}

.autocomplete-results.visible {
  display: block;
}

.autocomplete-item {
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.15s ease;
}

.autocomplete-item:last-child {
  border-bottom: none;
}

.autocomplete-item:hover {
  background-color: var(--color-surface);
}

.autocomplete-item.selected {
  background-color: var(--color-accent-teal-light);
  color: var(--color-text-primary);
  font-weight: 500;
}

/* Example chips */
.examples {
  margin-bottom: var(--space-2xl);
}

.examples p {
  margin: 0 0 var(--space-md) 0;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  justify-content: center;
}

.chip {
  display: inline-block;
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--color-accent-teal);
  border-radius: var(--radius-md);
  background: var(--color-background);
  color: var(--color-accent-teal);
  text-decoration: none;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.chip:hover {
  background-color: var(--color-accent-teal);
  color: #ffffff;
  text-decoration: none;
}

.chip:focus {
  outline: 2px solid var(--color-accent-teal);
  outline-offset: 2px;
}

/* Breadcrumb navigation */
.breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
  font-size: 12px;
  color: var(--muted);
  padding: 25px 0;
}

.breadcrumb span::after {
  content: " / ";
  margin: 0 6px;
  color: var(--line);
}

.breadcrumb span:last-child::after {
  content: "";
  margin: 0;
}

/* Section navigation */
.section-nav {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--space-3xl);
  padding: 0;
}

.section-nav a {
  flex: 1;
  padding: 12px 16px;
  font-size: 14px;
  text-decoration: none;
  color: var(--ink);
  border-right: 1px solid var(--line);
  text-align: center;
  transition: background-color 0.2s;
}

.section-nav a:last-child {
  border-right: none;
}

.section-nav a:hover {
  background-color: var(--surface);
}

@media (max-width: 599px) {
  .section-nav {
    font-size: 12px;
  }

  .section-nav a {
    padding: 10px 12px;
  }
}

/* Product hero section: 3-column desktop, single column mobile */
.product-hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  margin-bottom: var(--space-3xl);
}

.hero-title-mobile {
  display: block;
}

@media (min-width: 1000px) {
  .hero-title-mobile {
    display: none;
  }
}

.hidden-mobile {
  display: none;
}

@media (min-width: 1000px) {
  .hidden-mobile {
    display: block;
  }
}

.hero-column {
  flex: 1;
}

.hero-image {
  min-height: 300px;
  display: flex;
  align-items: center;
}

.product-image {
  width: 100%;
}

.product-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-lg);
  font-size: var(--font-size-sm);
}

.product-meta span {
  display: block;
}

/* Desktop 3-column layout per approved design package (1000px+) */
@media (min-width: 1000px) {
  .product-hero {
    display: grid;
    grid-template-columns: 1.05fr 1fr 1fr;
    gap: 28px;
    align-items: start;
  }

  .hero-column {
    flex: none;
  }
}

/* Price hero card - approved mint background */
.price-hero {
  background-color: var(--mint);
  border: none;
  border-radius: 12px;
  padding: 16px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.price-header {
  display: flex;
  gap: 8px;
}

.price-display {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.price-amount {
  font-size: clamp(28px, 5vw, 36px);
  font-weight: 700;
  color: var(--ink);
  line-height: 1.2;
}

.price-info {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.4;
}

.price-info-row {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.3;
}

.hero-cta {
  margin-top: 4px;
}

.price-header {
  margin-bottom: var(--space-md);
}

.badge-lowest-total {
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  background-color: var(--color-accent-teal-light);
  color: var(--color-accent-teal);
}

.badge-lowest-item {
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  background-color: #fef3c7;
  color: #d97706;
}

.price-display {
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.price-amount {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
  margin-bottom: var(--space-md);
}

@media (min-width: 1024px) {
  .price-amount {
    font-size: 32px;
  }
}

.price-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.info-badge {
  font-size: var(--font-size-sm);
  padding: var(--space-sm) var(--space-md);
  background-color: var(--color-background);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.hero-cta {
  display: flex;
  gap: var(--space-md);
}

.shop-hero {
  width: 100%;
  justify-content: center;
  min-height: 44px;
}

.shop-hero:hover {
  opacity: 0.9;
}
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

    # Generate search index: simple name-based catalogue search
    search_index = []
    for product in products:
        ns, slug = segment(product["namespace"]), segment(product["local_slug"])
        name = product.get("local_name") or slug
        search_index.append({
            "name": name,
            "slug": slug,
            "namespace": ns,
            "url": f"{base}p/{ns}/{slug}/"
        })
    (out / "search-index.json").write_text(json.dumps(search_index), encoding="utf-8")

    (out / "index.html").write_text(
        page("SjekkPris.no", index_body(products, base=base), base=base, noindex=noindex),
        encoding="utf-8",
    )

    # Generate search results page
    search_dir = out / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    (search_dir / "index.html").write_text(
        page("Søkeresultater – SjekkPris.no", search_results_body(base=base), base=base, noindex=noindex),
        encoding="utf-8",
    )

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
