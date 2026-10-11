# sjekkpris-no

The SjekkPris.no beta frontend: a static site built from Chillout's read API
and published to GitHub Pages. Intentionally simple — this is the integration
proof, not the design.

## How it works

- `build.py` reads `GET /api/v1/properties/sjekkpris-no/catalogue` for the
  product list, and `…/catalogue/{namespace}/{slug}/offers` for each product
  page. It runs **only in GitHub Actions**; the browser never calls Chillout.
- `check_output.py` fails the build if the output contains `apk_`, the key
  itself, the Chillout origin's hostname, a `prd_` platform id, or `/go/`.
- A failed read fails the build, and a failed build never replaces the site
  that is already published.

## Configuration (repository settings, never files)

| Name | Kind | Value |
|---|---|---|
| `CHILLOUT_READ_KEY` | Actions **secret** | the `sjekkpris-no` read key |
| `CHILLOUT_ORIGIN` | Actions variable | Chillout's base URL |
| `BASE_PATH` | Actions variable | `/sjekkpris-no/` for the github.io preview; `/` once `sjekkpris.no` points here |

Pages source: **GitHub Actions**.

## Not yet

- **No clickout links.** `/go/` is not live on sjekkpris.no; offers show
  "Butikklenke kommer", and a provider URL is never rendered in its place.
- **No custom domain.** No `CNAME` until DNS cutover, so the github.io
  preview keeps working.
- **noindex** on every page while in beta.

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
