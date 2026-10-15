# Launch design journey

Status: implemented preview, pending visual approval. Not published.

Run `python tools/preview_design.py`, then `python -m http.server 8765 --directory .design-preview`. Open http://localhost:8765/. The separate output contains a homepage, search, TV category, priced product, empty product and a simulated store destination. All pages are noindex and labelled as examples. The preview does not use API credentials. The production build never imports the example catalogue or illustration.

The homepage and search/category pages share `render_product_card()`. The preview uses the actual product renderer. The category component is ready for a curated product list; production category routes are not enabled. Current search matches names, with price/brand filters and sorting. It does not imply natural-language understanding, popularity, reviews or deals.

## Presentation data needed from Chillout

Existing catalogue fields: namespace, local_slug, local_name, lowest_item_price (minor/currency), offer_count and confirmation timestamp. Optional presentation fields prepared here: image.url and local_brand. These additions are a frontend view-model proposal, not a claim that the current catalogue API supplies them. Product pages continue using the existing identity and offer contracts.

Before activation, agree the catalogue image/brand mapping and curated category identifiers. Images must be published through the agreed property image pipeline. Missing pictures/prices remain explicit. Descriptions, specifications and real history still need their own data contract before populated sections can be enabled.

The fixture TV illustration comes from the approved HTML prototype; it is not a photograph verified against any real product. The six preview products and all prices/stores are invented. Preview store links stop on a local explanatory page.

Desktop uses the existing navy/green visual system, image cards, left filters and three result columns. Mobile keeps search prominent, hides the homepage hero artwork, uses two card columns and collapsible filters. Full-height mobile filter panel from the older reference remains a later fidelity refinement; this version uses accessible native disclosure.
