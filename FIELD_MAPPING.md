# SjekkPris Frontend v1 – Field Mapping

**Document Purpose:** Track which API response fields map to which UI display elements, with handling rules for nulls, missing data, and edge cases.

**API Version:** Chillout v1 (read-scoped)  
**Brief Reference:** Sections 3, 6, 10

---

## Catalog Response: GET /api/v1/properties/sjekkpris-no/catalogue

### Response Structure

```json
{
  "property_id": "sjekkpris-no",
  "products": [
    {
      "namespace": "catalogue",
      "local_slug": "product-slug",
      "local_name": "Product Name",
      "lowest_item_price": {"minor": 129900, "currency": "NOK"},
      "offer_count": 5,
      "lowest_item_price_confirmed_at": "2026-10-11T04:15:00+00:00"
    },
    ...
  ]
}
```

### Field → UI Mapping

| API Field | Type | UI Component | Handling | Test Cases |
|-----------|------|--------------|----------|-----------|
| `namespace` | string | Product URL path | Validate with SAFE_SEGMENT regex; used in `/p/{ns}/` | "catalogue" ✓ |
| `local_slug` | string | Product URL path | Validate with SAFE_SEGMENT regex; used in `/p/{ns}/{slug}/` | "fixture-lamp" ✓ |
| `local_name` | string | Card title | HTML-escape; trim; no max length (test long names) | "FIXTURE Lamp <b>" → escaped ✓ |
| `lowest_item_price` | object\|null | Card price display | Call `money()` function; null → "Ingen pris" | `{"minor": 129900, "currency": "NOK"}` → "NOK 1 299,-" ✓ |
| `offer_count` | integer | "X tilbud" badge | Show count; "1 tilbud" singular, "3 tilbud" plural | 0 → "0 tilbud", 1 → "1 tilbud" |
| `lowest_item_price_confirmed_at` | ISO 8601\|null | Confirmation date | Call `day()` function; null → omit field | "2026-10-11T04:15:00+00:00" → "11.10.2026" ✓ |

### Edge Cases Tested

- ✓ `local_name` with HTML tags: escaped to `&lt;b&gt;`
- ✓ `lowest_item_price` as null: displayed as "Ingen pris"
- ✓ `lowest_item_price_confirmed_at` as null: date column left empty
- ✓ `offer_count` as 0: shown as "0 tilbud"

---

## Detail Response: GET /api/v1/properties/sjekkpris-no/catalogue/{namespace}/{slug}/offers

### Response Structure

```json
{
  "property_id": "sjekkpris-no",
  "product_id": "prd_FIXTURE",
  "identity": {
    "local_name": "Product Name",
    "local_slug": "product-slug",
    "namespace": "catalogue",
    "local_brand": "Brand Name or null",
    "local_category": "Category Name or null",
    "local_pack_size": "Size Description or null",
    "image": {
      "url": "https://...",
      "basis": "property_selected"
    } // or null
  },
  "offers": [
    {
      "offer_id": "o-1",
      "advertiser": "Shop Name",
      "provider": "Tradedoubler",
      "item_price": {"minor": 129900, "currency": "NOK"},
      "known_total_price": {"minor": 139900, "currency": "NOK"},
      "comparison_status": "sorted_last_unknown_total",
      "shipping": {
        "state": "known_amount",
        "amount": {"minor": 10000, "currency": "NOK"},
        "imported_amount": null,
        "terms": {
          "is_test_data": false
        }
      },
      "availability": {
        "status": "in_stock",
        "raw_value": null
      },
      "last_confirmed_at": "2026-10-11T04:15:00+00:00",
      "stale": false,
      "withdrawn": false,
      "deselected": false,
      "ranking": {
        "item_price": {
          "availability_status": "in_stock",
          "ranking_eligible": true,
          "ineligibility_reasons": []
        },
        "total_price": {
          "availability_status": "in_stock",
          "ranking_eligible": false,
          "ineligibility_reasons": ["unknown_total"]
        }
      },
      "link": {
        "clickout_available": true,
        "clickout_url": "/go/tgt_01FXTVRE0000000000000WA"
      }
    },
    ...
  ],
  "excluded": [
    // Same structure as offers[], but with comparison_status reasons
  ],
  "lowest_item_price": "o-1",
  "lowest_known_total_price": null,
  "basis": "item_price"
}
```

### Identity Block Mapping

| API Field | Type | UI Use | Handling |
|-----------|------|--------|----------|
| `identity.local_name` | string | Product page title (h1) | HTML-escape; required |
| `identity.local_slug` | string | (URL already has this) | — |
| `identity.namespace` | string | (URL already has this) | — |
| `identity.local_brand` | string\|null | Product hero metadata line | Show only if non-null; label "Merke:" or similar |
| `identity.local_category` | string\|null | Product hero metadata line | Show only if non-null; **NOT a category browser** (see brief note: "One local_category field is not a categorization system") |
| `identity.local_pack_size` | string\|null | Product hero metadata line | Show only if non-null; **NOT a variant selector** |
| `identity.image` | object\|null | Product hero image | If null: "Bilde mangler" placeholder. If object: validate `url` field reachable; use object-fit:contain; store `basis` for reference but don't expose in UI |

### Pricing & Ranking Block Mapping

| API Field | Type | UI Logic | Handling | Rules |
|-----------|------|----------|----------|-------|
| `lowest_item_price` | offer_id\|null | Winner badge on offers list | Lookup this offer_id in offers[]; mark with "Laveste pris" badge | **Never compute min; always use API's designation** |
| `lowest_known_total_price` | offer_id\|null | Hero price highlight | See pricing validation logic below | Must pass 3-part gate |
| `basis` | string? | (informational) | Show user what basis ranking uses; do not override ranking | Typical: "item_price" or "total_price" |

### Pricing Validation Logic (Section 6)

**Hero Price Selection:**

1. Attempt to use `lowest_known_total_price`:
   - Lookup in offers[]
   - Offer must have `known_total_price` (non-null)
   - Offer's `ranking.total_price.ranking_eligible` must be true
   - Offer's `shipping.terms.is_test_data` must be false
   - If all valid: show "Laveste kjente totalpris" + offer details

2. If (1) fails, fallback to `lowest_item_price`:
   - Lookup in offers[]
   - Show item price with label "Laveste varepris"
   - Add note: "Frakt ukjent" or "Totalpris ukjent"

3. If (2) fails (no winner at all):
   - No price hero badge
   - Show offers list as-is with availability/shipping/total notes

**Rules:**

- ✗ Never show item_price as total_price
- ✗ Never compute local min(); always use API's lowest_*_price references
- ✓ Show "Totalpris ukjent" if total is null or terms.is_test_data=true
- ✓ Show offer's own item_price, shipping, total consistently across hero and list
- ✓ Mark shipping as "Frakt ukjent" if state ≠ "confirmed_free" and state ≠ "known_amount"

### Offer Object Mapping

| API Field | Type | UI Component | Handling | Test Cases |
|-----------|------|--------------|----------|-----------|
| `offer_id` | string | Badge target | Compare to lowest_item_price, lowest_known_total_price | "o-1" ✓ |
| `advertiser` | string | Shop name (row/card header) | HTML-escape; fallback "Ukjent annonsør" if null | "FIXTURE Winner Shop" ✓ |
| `item_price` | {minor, currency}\|null | Item price cell | Call `money()`; null → "Ingen pris" | null → "Ingen pris" ✓ |
| `known_total_price` | {minor, currency}\|null | Total price cell | Call `money()`; null → "Totalpris ukjent" | null → "Totalpris ukjent" ✓ |
| `shipping.state` | string | Shipping cell | See shipping mapping below | "known_amount", "confirmed_free", (else) |
| `shipping.amount` | {minor, currency}\|null | Shipping detail | Used only if state="known_amount"; format with `money()` | {"minor": 10000, "currency": "NOK"} → "NOK 100,-" |
| `shipping.terms.is_test_data` | boolean | Shipping confidence gate | If true: override to "Frakt ikke bekreftet"; block total-price claims | true → "Frakt ikke bekreftet" ✓ |
| `availability.status` | string | Availability cell | Map to Norwegian label (AVAILABILITY dict) | in_stock → "På lager" ✓ |
| `last_confirmed_at` | ISO 8601 | Stale date in notes | Call `day()` | "2026-10-01T04:15:00+00:00" → "01.10.2026" ✓ |
| `stale` | boolean | "Ikke bekreftet nylig" note | If true: add note + date | true + date → "Ikke bekreftet nylig (sist 01.10.2026)" ✓ |
| `withdrawn` | boolean | "Ikke lenger i annonsørens feed" note | If true: add note | true → "Ikke lenger i annonsørens feed" ✓ |
| `ranking.item_price.ranking_eligible` | boolean | Clickout gate (part 3/3) | Required true for /go/ link | true ✓ |
| `link.clickout_available` | boolean | Clickout gate (part 1/3) | If false: no link | true ✓ |
| `link.clickout_url` | string\|null | Clickout gate (part 2/3) | Validate regex `/^\/go\/tgt_[0-9A-HJKMNP-TV-Z]{26}$/` | "/go/tgt_01FXTVRE0000000000000WA" ✓ |
| Computed link | — | CTA href | `https://sjekkpris.no` + clickout_url; rel="sponsored nofollow" | "https://sjekkpris.no/go/tgt_…" ✓ |

### Shipping Mapping Logic

| shipping.state | shipping.terms.is_test_data | Display |
|---|---|---|
| "confirmed_free" | false | "Fri frakt" |
| "known_amount" | false | "Frakt {amount}" |
| "known_amount" | true | "Frakt ikke bekreftet" |
| (anything else) | false | "Frakt ukjent" |
| (anything else) | true | "Frakt ikke bekreftet" |

**Test Cases:**

- ✓ confirmed_free + false → "Fri frakt"
- ✓ known_amount + amount + false → "Frakt NOK 100,-"
- ✓ (no state) + false → "Frakt ukjent"
- ✓ known_amount + true (test data) → "Frakt ikke bekreftet"

### Availability Mapping

| API availability.status | Display (AVAILABILITY dict) |
|---|---|
| "in_stock" | "På lager" |
| "out_of_stock" | "Ikke på lager" |
| "preorder" | "Forhåndsbestilling" |
| "backorder" | "Restordre" |
| "unknown" or missing | "Lagerstatus ukjent" |

**Test Cases:**

- ✓ "in_stock" → "På lager"
- ✓ "out_of_stock" → "Ikke på lager"
- ✓ unknown → "Lagerstatus ukjent"

### Excluded Offers Mapping

| API Field | UI Change |
|-----------|-----------|
| `comparison_status` (in excluded[]) | Map to EXCLUSION reason (dict): |
| "excluded_currency_mismatch" | "Annen valuta – ikke sammenlignbar" |
| "excluded_vat_basis_unknown" | "Ukjent mva-grunnlag – ikke sammenlignbar" |
| (other/unknown) | "Ikke sammenlignbar" |
| Clickout link | **Never** render; always show "Ingen lenke" |
| Badge | **Never** show "Laveste pris" on excluded offers |

---

## Edge Cases & Test Scenarios

### Product Card (Catalog)

1. ✓ Long product name (100+ chars): No truncation; test wrapping
2. ✓ HTML in product name: Escaped (`<b>` → `&lt;b&gt;`)
3. ✓ Missing price (lowest_item_price=null): Show "Ingen pris"
4. ✓ Missing confirmation date: Omit date column
5. ✓ Zero offer_count: Show "0 tilbud"

### Product Detail

#### Image

- null image: "Bilde mangler" placeholder
- image.url returns 404: Show "Bilde mangler" (client-side fallback)
- Valid image: Display with object-fit: contain

#### Pricing

1. ✓ Lowest total price = lowest item price: Both exist, show both
2. ✓ Total price ≠ item price (higher due to shipping): Show both, highlight total
3. ✓ Total price unknown: Show "Totalpris ukjent"; fallback to item price
4. ✓ Item price null but total known: Show total only (rare case)
5. ✓ All prices null: "Ingen pris" (no hero badge)
6. ✓ lowest_item_price ref doesn't exist in offers: Don't badge; render as fallback

#### Offers

1. ✓ Single offer: Show in list; apply all logic
2. ✓ Multiple offers: Sort by API ranking (basis); badge lowest
3. ✓ Stale offer (stale=true): Note + date; no "Laveste pris" badge
4. ✓ Out-of-stock (availability="out_of_stock"): Show status; no badge; no link (ranking_eligible=false)
5. ✓ Unknown availability: "Lagerstatus ukjent" (no optimistic "in stock")
6. ✓ Test data shipping: Override to "Frakt ikke bekreftet"; block total-price hero
7. ✓ Withdrawn (withdrawn=true): Note; no badge; no link
8. ✓ Excluded offer: Separate section; never clickable; show reason

#### Clickout Links

1. ✓ All gates pass (link.clickout_available=true + valid /go/tgt_… + ranking_eligible=true): Full href
2. ✓ link.clickout_available=false: "Ingen lenke"
3. ✓ Bad clickout_url (not /go/tgt_…): "Ingen lenke"
4. ✓ ranking_eligible=false (stale/out-of-stock): "Ingen lenke" (but offer still visible)
5. ✓ No link object: "Ingen lenke"

---

## Summary

**Rule of thumb:** API tells the truth. Frontend trusts it and translates it faithfully.

- ✗ Never guess, compute, or fill missing data
- ✗ Never show optimistic defaults (assume in-stock if unknown, assume free shipping if unknown, etc.)
- ✓ Always respect API's ranking decisions (lowest_item_price, lowest_known_total_price)
- ✓ Always validate clickout gate (all 3 parts)
- ✓ Always escape HTML in names and user-visible strings
- ✓ Always format currency with `money()` function
- ✓ Always show null prices as "Ingen pris", not "0 kr"
- ✓ Always separate stale/withdrawn/excluded offers with notes or sections
