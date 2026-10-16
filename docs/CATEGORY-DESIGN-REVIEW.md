# Category design preview — 15 October 2026

Category membership, Norwegian display names and ancestor paths come directly from Chillout. The frontend groups existing memberships; it does not classify products. A product in several supplied categories is counted once per ancestor.

Implemented: shared category navigation, category overview, linked product breadcrumbs, child category links, desktop filter column and three-column product grid, compact mobile product rows, full-height mobile filter dialog, active filter chips, price range and brand filtering, item-price sorting. Unknown prices sort last. Filters only use supplied data. The homepage still hides its hero image on mobile.

Preview URLs use `/kategori/<norwegian-name>/`. These are noindex and are NOT an approved permanent URL scheme: the Web Profile source still marks URL policy draft/open. Route collisions fail explicitly instead of silently combining categories. Product URLs remain unchanged.

The category preview workflow builds actual API data and captures screenshots without deploying. No fake ratings, popularity, feature attributes or editorial category claims have been added. Existing product design has already been published separately.

Validation: 83 Python tests and 3 price-switch Node tests pass locally. The real-data preview passed price filtering, reset, sorting, product navigation, keyboard Escape/focus return and overflow checks at 360, 390, 430 and 1280 px. Sixteen real products appear under the supplied Baby og barn and Hjem og hage roots. Screenshots were inspected; desktop image height and price-field layout were tightened afterward. Final screenshot run recorded in PR #4.

Scope compared with the category template: desktop sidebar and mobile horizontal product rows follow the template. Price fields, available brand filtering and the full-height mobile filter panel are implemented. Categories default to lowest item price (the later agreed pricing rule), while search preserves name sorting. Native brand/sort controls are used for this first version. Category hero imagery, attribute-specific filters, ratings, favourites and editorial guides are not represented without supporting content/functionality.
