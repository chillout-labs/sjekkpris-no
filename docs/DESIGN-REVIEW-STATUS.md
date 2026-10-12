# Design review checkpoint — 12 October 2026

Status: implementation draft, NOT visually approved. Do not merge or deploy.

Based on frontend-v1-design at c1a39b94b33bcefe38bdf9ac096303daafb682c0.

## Changes

- Shared header with working search form and native disclosure menu; homepage uses only its hero search.
- Product presentation in product_ui.py: mobile title before image, compact price panel, desktop offers/history layout, mobile offer cards, five visual desktop offer columns.
- Product image sizing and header gap aligned with approved HTML values. Automatic legacy dark tokens removed to keep the approved light presentation consistent.
- Homepage in home_ui.py: locked headline/copy, dominant search, catalogue-based examples, ordinary product cards, honest missing-image and no-price states.
- Autocomplete supports keyboard selection, Escape, accessible option state, request-race handling and ordinary form submission fallback.
- Existing API access, winner references, monetary formatting, clickout gates, routes and noindex retained.

## Evidence

66 Python unit tests passed locally, including the existing output guard checks. Homepage JavaScript parsed successfully with Node.
These are code checks, NOT browser interaction tests, overflow checks, accessibility certification or visual comparisons.
Local Chromium installation failed; cloud browser policy blocked local file navigation. No new rendered screenshots were produced.

## Remaining review

Render homepage and product page at 360, 390, 430 and 1280 px. Compare product to the approved SjekkPris-produktside.html and homepage to the locked homepage image/D05.
Check header, spacing, type sizes, product photos, fallback height, overflow and offer rows. Exercise menu, search suggestions (typing/arrows/Enter/Escape), result navigation and section anchors.
Render known total (with item/shipping breakdown), confirmed free shipping, unknown shipping, missing winner and empty offers. Do not follow tracking/clickout links while testing.

## Known differences / data limits

- Homepage has ordinary Products, not unsourced deals/popularity/editorial/history/category modules. Catalogue has no image field; product cards currently use missing-image state.
- Homepage robot artwork is not integrated. No fake microphone, account or favourites action.
- Product page has honest empty history/about sections and only available identity metadata; no invented graph, specifications, variants, delivery times or merchant logos.
- No category navigation is rendered without supported category destinations.
- CSS includes legacy rules for other pages; scoped new components still require a real-browser collision check.
- Search results page retains its previous presentation and is not claimed to match the full search design.

User approval is still required after visual review. This checkpoint does not mark either page as complete.
