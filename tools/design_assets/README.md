The TV illustration is extracted from the user-approved SjekkPris-produktside.html design package. It is illustrative preview content, not a verified merchant product photograph. Only tools/preview_design.py copies it into its separate demo output. Do not copy these fixtures into a production catalogue.

## Baby Brezza retailer proposal (18 October 2026)

`babybrezza-snapshot.json` is a fixed, beta-only snapshot of 15 unique public
SjekkPris product pages that contained an offer from advertiser `babybrezza` on
2026-10-18. It contains product source URLs, observed item prices, editorial
product groups and locally encoded WebP copies of the catalogue images. Image
source URLs are retained for provenance. The logo comes from the retailer's
public website; its source URL is retained too. Brand/product artwork remains
the property of its respective owners and is used to identify the retailer and
products in the proposal.

`tools/store_preview.py` decodes the images at build time so the static design
and browser checks do not depend on a third-party image request. No collection
runs in CI, and this snapshot must not be mistaken for a live feed adapter.
Prices and source date are explicitly labelled. Counts represent product pages,
including distinct variants, and do not represent the retailer's full range.
The page has no invented click metrics, reviews, price-history or cheapest-store
claims. Product links open the real SjekkPris catalogue; retailer actions remain inactive until verified affiliate destinations are
provided by Chillout. No direct merchant-link fallback is allowed. The beta remains noindex.

Future integration: use stable advertiser identity and active offer joins;
maintain source and checked-at fields for editorial store facts. SjekkPris and
Chillout manage these fields initially. Advertiser editing, moderation and
30-day outbound-click aggregation are separate future work.
