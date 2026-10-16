# Design status – 16 October 2026

Branch: `category-design-v1`, PR #4. No deployment or URL decision.

## Implemented presentation

- Shared header, navigation, autocomplete, category navigation and product cards.
- Responsive search/category results, mobile filter sheet, active filters, sorting, zero results and reset.
- Product offer comparison and known/unknown shipping states.
- Optional gallery with working thumbnails, variant links, attributes, price-history chart and accessible observation table.
- Optional product content, use cases, value alternatives, accessory information and FAQ.
- Preview-only homepage discovery rails and editorial cards.
- Preview-only needs-search highlight layout, loading skeletons and error state.

Run `python tools/preview_design.py`, then serve `.design-preview`. Its banner links to all example journeys. Example facts, stores and prices must not be used as real catalogue data. The guide is a typography/link fixture, not finished editorial content.

## Verification

83 unit tests pass. Browser checks cover 360, 390, 768 and 1280 px; gallery interaction, FAQ, filtering, zero results, reset, sorting, image loading, JavaScript errors and horizontal overflow. Screenshots are in the Design journey preview workflow artifact. The separate Category preview workflow checks real API data at 360, 390, 430 and 1280 px.

Reviewed product desktop/mobile, homepage mobile, needs-search desktop and component states mobile. Corrected highlighted-card typography after screenshot inspection.

## Remaining integration and acceptance

`product_body(..., presentation=...)` is the optional display seam; no new production API fields are inferred. Real gallery, variant, history and product-knowledge adapters still need agreed source data. Home popularity/history and needs-based selection are fixture-only. No AI recommendation service is implemented. Production search continues to describe its actual name-search capability.

This pass is not a certified 95% fidelity or full WCAG audit. Detailed comparison with every approved reference and production-data integration remain acceptance work. Advanced account, alerts and comparison functionality remain outside v1. Final category/URL decisions remain deferred until the 100,000-product test.
