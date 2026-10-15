# SjekkPris Frontend v1 – Reference Map

**Base SHA:** `58279a6` (Clickout links + beta shell)  
**Brief Version:** SJEKKPRIS-FRONTEND-V1-BRIEF.txt, 11. oktober 2026  
**Created:** 2026-10-11

## Design Image References

| Screen | Design Image | B-ID | SHA256 | File | Approval | Status |
|--------|--------------|------|--------|------|----------|--------|
| Homepage | B002 | `ff928ae2403a505a7a4f1de56577b9327daedc56d88a90643482b44d160ad2e7` | SjekkPris – Låst hjemmesidedesign v1.0.png | D05 locked baseline | ✓ Reference |
| Produktside desktop | B009 | `63361445f59608d3367fba5759d7e83cfa4a1c11a34615b1a51a19388441c7b3` | LG OLED C4 prissammenligning hos SjekkPris.png | D05 | ⚠ Provisional |
| Produktside mobil | B011 | `3211d42cfc307798f3b52d8ce5ad23477f8ca4f6f6e1f62574d8b7980689b5bc` | SjekkPris mobilprodukt-side for LG OLED TV.png | D05 | ✓ Reference |
| Kategori/søk | B008 | — | SjekkPris: OLED-TV sammenligning.png | Design direction | ⏳ Awaiting contract |
| Søk/autocomplete | B005/B006/B007 | — | — | D06 Search v1 | ⏳ Awaiting contract |

## Known Deviations

### By Design (Awaiting Backend Capability)

| Feature | Design Status | Backend Status | Impact | Notes |
|---------|---------------|----|--------|-------|
| **Behovssøk** (intent matching) | D05 first-class | ⏳ Not in v1 API | Search degraded to name-only | Section 4: "Vent på kapabilitet" |
| **Prishistorikk** (price history) | Approved component | ⏳ No time-series data | Hidden until data available | Section 4: "Vent på data" |
| **Kategorier & fasetter** (taxonomy) | D05 hierarchy design | ⏳ No canonical taxonomy in API | Category browsing deferred | Section 4: "Vent på kontrakt" |
| **Nytt og aktuelt** (news/guides) | Editorial content | ⏳ Not sourced | Deferred until curated | Section 4: "Vent på data" |
| **Fortsett der du slapp** (resume) | Design decided | ⏳ No view history tracked | Deferred in v1 | Section 4: "Vent i første leveranse" |
| **Mest søkt akkurat nå** (trending) | Design proposed | ⏳ No popularity data | Deferred in v1 | Section 4: "Vent" |
| **Produkt-bilder** | Identity field optional | ⚠ May be sparse coverage | Fallback: "Bilde mangler" | Section 3: image field must validate |
| **Merke & pakning** | Identity fields | ⚠ Conditional coverage | Show only if present | Section 3: optional local_brand, local_pack_size |

### By Implementation (Current Build)

| Feature | Brief Requirement | Implementation | Status |
|---------|-------------------|-----------------|--------|
| **Søkefelt** | Prominent top | Text-based name search only | ✓ v1 Ready |
| **Låst topp** | Header/logo/search | Static header | ✓ v1 Ready |
| **Produktkort** | Name, price, offer count | Grid layout | ✓ v1 Ready |
| **Prishero** | Lowest known total (valid ref) | Price & shipping logic | ✓ v1 Ready |
| **Tilbudstabell** | Offers with metadata | Responsive table/cards | ✓ v1 Ready |
| **Clickout gate** | link + eligible + /go/tgt_ | Section 6 rules | ✓ Preserved from base |
| **Keyboard nav** | Tab, Escape, Enter | Search + focus states | ⏳ Step 5 |
| **Responsive** | 360–430 mobile, ~1280 desktop | Flexbox/grid layout | ⏳ Step 1–4 |
| **Mobile-first** | Design principle | Progressive enhancement | ✓ Mobile priority |

## Field Mapping: API Response → UI Display

### Catalog Product (GET /catalogue)

| API Field | Data Type | UI Field | Handling |
|-----------|-----------|----------|----------|
| `local_name` | string | Product card title | Required; escape HTML |
| `local_slug` | string | URL path `/p/{ns}/{slug}/` | Safe segment validation |
| `namespace` | string | URL path `/p/{ns}/{slug}/` | Safe segment validation |
| `lowest_item_price` | `{minor, currency}` | Card price display | Format with `money()` |
| `lowest_item_price_confirmed_at` | ISO 8601 | Confirmation date | Format as `DD.MM.YYYY` or omit |
| `offer_count` | integer | "X tilbud" badge | Plural form |
| *(no other fields shown in catalog response)* | — | — | — |

### Detail Product (GET /catalogue/{ns}/{slug}/offers)

#### Identity Block

| API Field | Data Type | UI Use | Handling |
|-----------|-----------|--------|----------|
| `identity.local_name` | string | Product page title | Required; escape |
| `identity.local_slug` | string | Canonical URL | Already in path |
| `identity.namespace` | string | Already in path | — |
| `identity.local_brand` | string? | Product hero (optional) | Show only if non-null |
| `identity.local_category` | string? | Metadata (optional) | Show only if non-null; not a taxonomy |
| `identity.local_pack_size` | string? | Metadata (optional) | Show only if non-null; not a variant selector |
| `identity.image` | `{url, basis}`? | Hero image | Validate URL reachability; fallback to "Bilde mangler" |

#### Pricing & Ranking

| API Field | Data Type | UI Logic | Handling |
|-----------|-----------|----------|----------|
| `lowest_item_price` | offer_id? | Lowest item-price winner badge | Lookup in offers, not computed |
| `lowest_known_total_price` | offer_id? | Lowest total price highlight | Must validate: offer exists + total known + terms.is_test_data=false + ranking.total_price.ranking_eligible |
| `offers[].item_price` | `{minor, currency}` | Per-offer item price | Format; null → "Ingen pris" |
| `offers[].known_total_price` | `{minor, currency}`? | Per-offer total | May be null; show "Totalpris ukjent" |
| `offers[].shipping.state` | string | Shipping label | "known_amount" → show amount; "confirmed_free" → "Fri frakt"; else "Frakt ukjent" |
| `offers[].shipping.amount` | `{minor, currency}`? | Shipping cost | Format if present and state="known_amount" |
| `offers[].ranking.item_price.ranking_eligible` | boolean | Clickout gate | Required for /go/ link + link.clickout_available |
| `basis` | string? | Sort context | Inform (not override) user display of ranking order |

#### Offer Object

| API Field | Data Type | UI Display | Handling |
|-----------|-----------|----------|----------|
| `offer_id` | string | Lowest-price badge target | Compared to lowest_item_price, lowest_known_total_price |
| `advertiser` | string | Shop name in offers list | Fallback: "Ukjent annonsør" |
| `availability.status` | string | Availability text | Map: in_stock → "På lager", out_of_stock → "Ikke på lager", preorder → "Forhåndsbestilling", backorder → "Restordre", unknown → "Lagerstatus ukjent" |
| `stale` | boolean | "Ikke bekreftet nylig" note | Add date if last_confirmed_at exists |
| `last_confirmed_at` | ISO 8601 | Stale date | Format as `DD.MM.YYYY` |
| `withdrawn` | boolean | "Ikke lenger i annonsørens feed" note | Show if true |
| `link.clickout_available` | boolean | Clickout gate (1/3) | Must be true + valid path + ranking_eligible |
| `link.clickout_url` | string | /go/tgt_... token | Validate regex; construct `https://sjekkpris.no{url}` |
| `comparison_status` | string | Excluded reason | If offer in excluded[], show mapped reason (e.g., "excluded_currency_mismatch" → "Annen valuta – ikke sammenlignbar") |
| `shipping.terms.is_test_data` | boolean | Shipping confidence | If true, shipping text = "Frakt ikke bekreftet"; block total-price claims |

#### Excluded Offers

| Field | Handling |
|-------|----------|
| `excluded[]` | Separate section below main offers |
| `comparison_status` | Map to exclusion reason (EXCLUSION dict in build.py) |
| Clickout link | **Never** clickable; show "Ingen lenke" |

## Capability Matrix

### Currently Supported (Section 3 Contract)

✓ Product catalog with lowest item price  
✓ Per-product offers with item price, total price, shipping, availability  
✓ Offer metadata: advertiser, confirmed date, stale/withdrawn status  
✓ Ranking eligibility and item-price winner designation  
✓ Clickout routing (link + token validation)  
✓ Excluded offers with reason  
✓ Brand, category, pack-size optional identity fields  
✓ Image field (property-selected, not canonical)  

### Required for Future Sections (Awaiting Backend)

| Feature | Section | Requirement | Status |
|---------|---------|-------------|--------|
| **Category taxonomy** | 4 (Category mobil/desktop) | Canonical categories, Norwegian labels, filter definitions | ⏳ Awaiting |
| **Search intent parsing** | 4 (Behovssøk) | Tolerate queries like "liten tykktøff dresse" → understand criteria | ⏳ Awaiting |
| **Price history** | 4 (Prishistorikk) | Time-series price data with period/source/update info | ⏳ Awaiting |
| **Trending/popularity** | 4 (Mest søkt akkurat nå) | Search volume or click metrics with period/ranking def | ⏳ Awaiting |
| **Editorial content** | 4 (Nytt og aktuelt) | Curated guides/news; not generated articles | ⏳ Awaiting |
| **View history** | 4 (Fortsett der du slapp) | Tracked recent product views (persisted) | ⏳ Awaiting |
| **Product relations** | 4 (Bruksområder, kompatibelt tilbehør) | Variant graph, accessory relations, compatibility rules | ⏳ Awaiting |
| **Reviews/ratings** | 4 (Anmeldelser) | Structured ratings from shopper feedback | ⏳ Awaiting |
| **Detailed specs** | 4 (Spesifikasjoner) | Structured product attributes + variant selectors | ⏳ Awaiting |
| **Total-price sorting** | 6.6 | Confidence-based ranking when total prices are known | ⏳ Awaiting |

## Current State vs. Design Bible (D05)

**Locked baseline:** D05, 25.09.2026, Design Bible v1.0  
**Approved searches:** D06, Search v1 (extends D05)

### Implemented ✓

- Locked header (Logo + search field)
- Product grid with name + price + offer count
- Responsive mobile-first layout (planned Steps 1–5)
- Clickout links with full gate + security rules (preserved from base)
- Truthful null/stale/withdrawn handling (preserved from base)

### Deferred (Data Awaiting)

- Category browse & filtering
- Trending/best sellers
- News & guides  
- Price history charts
- Intent-aware search suggestions
- View-tracking resume feature
- Detailed specs & variants
- Accessory/compatibility section

### Not in v1 (Per D05 Section 4)

- Account/signin
- Favorites/wishlist
- Price alerts
- Inventory monitoring
- Product comparison matrix
- Advanced search aggregator
- Seller ratings/reviews

---

## Next Steps

1. **Verify payload shape** (Step 0): Fetch live catalog & product detail; confirm field coverage.
2. **Build foundation** (Step 1): CSS + header + footer; establish mobile/desktop responsiveness.
3. **Implement presentation layer** (Step 2): ProductCard, view-data mapping; test edge cases.
4. **Assemble homepage** (Step 3): Search field, catalog grid, interim "Produkter" module.
5. **Detail page** (Step 4): Hero, pricing logic, offers list; visual comparison to B009/B011.
6. **Polish & QA** (Step 5): Keyboard, responsive variants, error states.
