# Category design preview — 15 October 2026

Category membership, Norwegian display names and ancestor paths come directly from Chillout. The frontend groups existing memberships; it does not classify products. A product in several supplied categories is counted once per ancestor.

Implemented: shared category navigation, category overview, linked product breadcrumbs, child category links, desktop filter column and three-column product grid, compact mobile product rows, full-height mobile filter dialog, active filter chips, price range and brand filtering, item-price sorting. Unknown prices sort last. Filters only use supplied data. The homepage still hides its hero image on mobile.

Preview URLs use `/kategori/<norwegian-name>/`. These are noindex and are NOT an approved permanent URL scheme: the Web Profile source still marks URL policy draft/open. Route collisions fail explicitly instead of silently combining categories. Product URLs remain unchanged.

The category preview workflow builds actual API data and captures screenshots without deploying. No fake ratings, popularity, feature attributes or editorial category claims have been added. Existing product design has already been published separately.

Validation: 83 Python tests locally. Browser verification and screenshot review recorded in the PR after CI completes.
