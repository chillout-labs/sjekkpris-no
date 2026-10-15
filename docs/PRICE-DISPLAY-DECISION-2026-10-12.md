# Price display — approved decision, 12 October 2026

The user approved item price excluding shipping as the default, with an
"Inkluder frakt" switch above the offer list controlling both the list and hero.
This supersedes the earlier total-price-first UI decision in the frontend brief.

- Default/off: hero uses the valid `lowest_item_price` reference; primary offer
  prices and numeric display order use item price. Shipping remains visible.
- On: hero uses the valid `lowest_known_total_price` reference; primary prices
  and numeric display order use backend-provided known total price.
- No valid total winner: show "Ingen kjent totalpris"; never quietly show an
  item price as the total-mode winner.
- Unknown or test-data totals sort after known totals. They remain visible and
  are labelled "Totalpris ukjent"; never treat unknown shipping as free.
- The two winners may be different merchants. CTA and merchant belong to the
  currently visible winner. Existing clickout eligibility gates are unchanged.
- Item-price display on homepage/catalogue stays unchanged.
- Start each page in item mode. No cookies or persistent preference introduced.
- Without JavaScript: usable item-price page, shipping separately, no dead switch.

## Implementation boundary

Chillout still owns claim eligibility and both winner references. Inspection of
`src/chillout/api/offers.py` found no exposed sort-basis parameter on the current
property catalogue endpoint. The approved display sort is therefore computed at
build time from the returned amounts; ties retain backend order and excluded
offers remain separate. It does not compute new winners, totals or eligibility.
Only ordinal sort positions are exposed for client-side reordering, no internal
offer IDs or raw API payload. Mixed currencies in the comparable sort fail the
build rather than being ranked as if comparable.

## Verification

74 Python tests pass. Three Node-level interaction tests pass (default/reset,
switch on/back synchronization and empty-page behavior). Node tests use a DOM
stub; they do not certify real browser rendering or keyboard behavior.

Screenshot review required: both modes at 390px and 1280px with DIFFERENT API
winners, a paid-shipping breakdown, confirmed free shipping, unknown shipping,
and no total winner. Test Space on the focused switch and confirm visible hero,
store link, amount, table order and live status all change together. Do not
follow tracking links in fixture tests. No merge/deploy until visual approval.
