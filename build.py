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
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
{robots}
<title>{e(title)}</title>
<link rel="stylesheet" href="{e(base)}style.css">
</head>
<body>
<header>
<div class="container">
<a class="brand" href="{e(base)}">SjekkPris.no</a>
<span class="beta">Beta</span>
</div>
</header>
<main>
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
    return f'<a class="shop" href="{e(href)}" rel="sponsored nofollow">Til {advertiser}</a>'



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
    offers = body.get("offers") or []
    excluded = body.get("excluded") or []
    head = (
        "<tr><th>Butikk</th><th>Pris</th><th>Frakt</th><th>Totalpris</th>"
        "<th>Lager</th><th>Merknad</th><th></th></tr>"
    )

    parts = []
    parts.append(f'<p><a href="{e(base)}">← Tilbake til produkter</a></p>')
    parts.append(f"<h1>{e(name)}</h1>")

    # Identity metadata
    meta_parts = []
    if identity.get("local_brand"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Merke:</strong> {e(identity['local_brand'])}</span>")
    if identity.get("local_category"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Kategori:</strong> {e(identity['local_category'])}</span>")
    if identity.get("local_pack_size"):
        meta_parts.append(f"<span class=\"text-sm\"><strong>Pakning:</strong> {e(identity['local_pack_size'])}</span>")
    if meta_parts:
        parts.append(f"<div style=\"display: flex; flex-direction: column; gap: 4px; margin-bottom: 24px;\">{' '.join(meta_parts)}</div>")

    if not offers and not excluded:
        parts.append("<p>Ingen tilbud akkurat nå.</p>")
    else:
        if offers:
            rows = "\n".join(offer_row(o, lowest=lowest, excluded=False) for o in offers)
            parts.append(f"<h2>Tilbud</h2>\n<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")
        if excluded:
            rows = "\n".join(offer_row(o, lowest=None, excluded=True) for o in excluded)
            parts.append("<h2>Ikke sammenlignbare tilbud</h2>")
            parts.append(f"<table>\n<thead>{head}</thead>\n<tbody>\n{rows}\n</tbody>\n</table>")

    return "\n".join(parts)


STYLE = """
/* CSS Design Tokens & Layout Foundation
 * SjekkPris Frontend v1 – D05 Design Bible
 */

/* Root tokens: colors, spacing, typography */
:root {
  /* Colors: calm Scandinavian palette */
  --color-text-primary: #1d1f22;
  --color-text-secondary: #5f6368;
  --color-text-muted: #80868b;
  --color-background: #ffffff;
  --color-surface: #f8f9fa;
  --color-border: #dadce0;
  --color-accent-teal: #0d9488;
  --color-accent-teal-light: #d1fae5;
  --color-status-success: #059669;
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

/* Responsive table for mobile */
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
    margin-bottom: var(--space-xl);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    display: block;
    padding: var(--space-lg);
  }

  td {
    border: none;
    padding: var(--space-md) 0;
    text-align: right;
    display: block;
    padding-left: 50%;
    position: relative;
  }

  td:before {
    content: attr(data-label);
    position: absolute;
    left: var(--space-lg);
    font-weight: 600;
    text-align: left;
    color: var(--color-text-secondary);
  }

  tbody tr:hover {
    background-color: inherit;
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
