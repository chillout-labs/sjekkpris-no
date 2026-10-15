# sjekkpris-no

The SjekkPris.no beta frontend: a static site built from Chillout's read API
and published to GitHub Pages. Intentionally simple — this is the integration
proof, not the design.

## How it works

- `build.py` reads `GET /api/v1/properties/sjekkpris-no/catalogue` for the
  product list, and `…/catalogue/{namespace}/{slug}/offers` for each product
  page. It runs **only in GitHub Actions**; the browser never calls the read API; public images use its delivery gate.
- `check_output.py` fails the build if the output contains `apk_`, the key
  itself, the Chillout origin's hostname outside validated image attributes, a `prd_` platform id, or `/go/` in
  any form other than a well-formed `https://sjekkpris.no/go/tgt_…` link.
- A failed read fails the build, and a failed build never replaces the site
  that is already published.

## Configuration (repository settings, never files)

| Name | Kind | Value |
|---|---|---|
| `CHILLOUT_READ_KEY` | Actions **secret** | the `sjekkpris-no` read key |
| `CHILLOUT_ORIGIN` | Actions variable | Chillout's base URL |
| `BASE_PATH` | Actions variable | `/sjekkpris-no/` for the github.io preview; `/` once `sjekkpris.no` points here |

Pages source: **GitHub Actions**.

## Clickout links

An offer gets a "Til butikken" link only when Chillout states a servable
target (`link.clickout_available` and a `clickout_url` of exactly
`/go/tgt_…`) **and** the offer is eligible to hold the lowest-price claim
(`ranking.item_price.ranking_eligible`). The link is `https://sjekkpris.no` +
that `clickout_url`, unchanged, with `rel="sponsored nofollow"`. Stale,
out-of-stock, withdrawn and excluded offers stay listed with "Ingen lenke".
A provider URL is never rendered.

## Still in beta

- **noindex** on every page.

## Truthfulness

A `null` price is shown as "Ingen pris", never 0. Stale and out-of-stock
offers say so. "Laveste pris" marks only the offer the API names as holding
the claim — the site never computes a minimum of its own. Unknown shipping
gives an unknown total.

## Tests

```
python -m unittest discover -s tests
```

They run against a localhost stub with fixture data and need no key.


## Product delivery and publication (2026-10-15)

Chillout supplies approved property products, known brand, translated shared
categories and public image variants. New products remain drafts until approved
in Chillout. Existing catalogue visibility is preserved by its migration.
Approval/withdrawal affects the next successful website build; the backoffice
does not claim the static website has updated already. Automated import-triggered
rebuilds are a later step.

The browser loads images through the public image delivery gate; images are not
copied to this deployment. The API key stays in the build. The leak check permits
validated public image URLs only in img src/srcset attributes, and still checks
credentials and internal product IDs everywhere. Price and clickout rules remain
unchanged. Categories are descriptive labels, not a new navigation/URL tree.
