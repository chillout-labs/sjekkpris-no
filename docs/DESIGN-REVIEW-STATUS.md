# Product design review — 15 October 2026

Status: implementation on `frontend-v1-design`, PR #1 remains unmerged. No production deployment.

## Reference

The approved `SjekkPris-designpakke-v1.zip` (12 October), its HTML prototype and desktop/mobile reference PNGs were recovered and inspected. The existing three-column desktop hero, mobile name-before-image order, mint price panel, search header and responsive offers remain the design basis.

The later agreed price decision takes precedence over the prototype: item price by default, synchronized “Inkluder frakt” toggle. Unknown shipping is never zero shipping.

## Changes

- Integrated the catalogue-delivery changes from main without replacing the design renderer.
- Product hero and shared cards use validated public images and supplied responsive variants.
- Catalogue and offer requests ask for Norwegian metadata (`locale=nb`).
- Brand and translated categories render from real data; full category path is expandable.
- Removed duplicate category text in specifications and duplicate mobile item price.
- Added repeatable real-product screenshot capture to the no-deploy product-preview workflow.

## Evidence

Initial integration commit: `003408656c3772d32bf2300025aaed922e8b6644`.
- Local: 79 Python tests and 3 Node tests passed.
- GitHub real-data build and output guard passed: run 38791273280.
- Real images decoded and no horizontal overflow at 390/1280px for Alligator and Baby Brezza Bottle Washer Pro (white and black).
- Twelve full-page screenshots cover the three products, two widths and shipping on/off. Screenshots were inspected, not just generated. The visual review found duplicate category text and mobile item-price repetition, addressed in the follow-up.
- Separate demo journey run 38791273171 passed, including the no-image/no-offer state. No real no-image product was present in the selected catalogue.

## Remaining boundaries

This is not a pixel-identical reproduction of the populated TV reference. Current products have one supplied image; no verified gallery, variant links, descriptions, technical specifications or price history are available in the renderer. These are not invented. Header category navigation from the reference is still absent. Product image sharpness depends on source and delivered image sizes.

The current real examples have unknown shipping, so their shipping-on screenshots show the explicit unknown-total state. Known-total winner changes remain covered by fixture/interaction tests, not by these real-product screenshots.

Visual acceptance and merge approval are still pending.
