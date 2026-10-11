"""Presentation adapters: translate Chillout contract to explicit, safe view-data.

This layer creates an explicit, allowlist-based view-data model from the API
response. It validates all references, resolves winner lookups, and separates
pricing logic. No raw response fields leak into the output; only safe,
documented view-data is rendered.

Rules:
- Never mutate the raw response; create new view-data objects.
- Never compute your own winner (use API's lowest_item_price/lowest_known_total_price).
- Always validate winner references exist in the offers list.
- Always validate clickout gate (all 3 parts).
- Never assume shipping is free, unknown total is OK, or unknown availability means in-stock.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """Safe currency representation. Always from API; never computed."""
    minor: int
    currency: str

    @classmethod
    def from_api(cls, data: dict | None) -> Money | None:
        if not data:
            return None
        if not isinstance(data, dict):
            return None
        minor = data.get("minor")
        currency = data.get("currency")
        if minor is None or currency is None:
            return None
        return cls(int(minor), str(currency))


@dataclass(frozen=True)
class ProductIdentity:
    """Product metadata from identity block."""
    local_name: str
    local_slug: str
    namespace: str
    local_brand: str | None = None
    local_category: str | None = None
    local_pack_size: str | None = None
    image_url: str | None = None

    @classmethod
    def from_api(cls, api_identity: dict | None, *, product_fallback: dict | None = None) -> ProductIdentity | None:
        """Extract identity from detail response identity block, with fallback to catalog product."""
        if not api_identity and not product_fallback:
            return None

        identity = api_identity or {}
        fallback = product_fallback or {}

        name = identity.get("local_name") or fallback.get("local_name")
        if not name:
            return None

        slug = identity.get("local_slug") or fallback.get("local_slug")
        namespace = identity.get("namespace") or fallback.get("namespace")

        if not slug or not namespace:
            return None

        image_url = None
        if identity.get("image"):
            image_data = identity["image"]
            if isinstance(image_data, dict):
                image_url = image_data.get("url")

        return cls(
            local_name=str(name),
            local_slug=str(slug),
            namespace=str(namespace),
            local_brand=_safe_str(identity.get("local_brand")),
            local_category=_safe_str(identity.get("local_category")),
            local_pack_size=_safe_str(identity.get("local_pack_size")),
            image_url=image_url,
        )


@dataclass(frozen=True)
class Shipping:
    """Shipping cost and status."""
    state: str | None  # "confirmed_free", "known_amount", "not_provided", etc.
    amount: Money | None
    is_test_data: bool = False

    @classmethod
    def from_api(cls, api_shipping: dict | None) -> Shipping:
        """Extract shipping from offer's shipping block."""
        if not api_shipping:
            return cls(state=None, amount=None)

        state = api_shipping.get("state")
        amount = Money.from_api(api_shipping.get("amount"))

        is_test_data = (
            (api_shipping.get("terms") or {}).get("is_test_data") == True
        )

        return cls(
            state=str(state) if state else None,
            amount=amount,
            is_test_data=is_test_data,
        )


@dataclass(frozen=True)
class Availability:
    """Availability status."""
    status: str

    @classmethod
    def from_api(cls, api_availability: dict | None) -> Availability:
        """Extract availability from offer's availability block."""
        if not api_availability:
            return cls(status="unknown")

        status = api_availability.get("status")
        return cls(status=str(status) if status else "unknown")


@dataclass(frozen=True)
class OfferView:
    """Safe view-data for a single offer."""
    offer_id: str
    advertiser: str
    item_price: Money | None
    known_total_price: Money | None
    shipping: Shipping
    availability: Availability
    is_stale: bool
    stale_since: str | None  # ISO date
    is_withdrawn: bool
    is_excluded: bool = False
    exclusion_reason: str | None = None
    is_clickout_eligible: bool = False
    clickout_url: str | None = None
    is_item_price_winner: bool = False
    is_total_price_winner: bool = False

    @classmethod
    def from_api(
        cls,
        api_offer: dict,
        *,
        lowest_item_id: str | None = None,
        lowest_total_id: str | None = None,
        excluded: bool = False,
    ) -> OfferView:
        """Create OfferView from API offer object."""
        offer_id = api_offer.get("offer_id", "")
        advertiser = api_offer.get("advertiser") or "Ukjent annonsør"
        item_price = Money.from_api(api_offer.get("item_price"))
        total_price = Money.from_api(api_offer.get("known_total_price"))
        shipping = Shipping.from_api(api_offer.get("shipping"))
        availability = Availability.from_api(api_offer.get("availability"))

        is_stale = bool(api_offer.get("stale"))
        stale_since = api_offer.get("last_confirmed_at") if is_stale else None

        is_withdrawn = bool(api_offer.get("withdrawn"))

        # Clickout gate: all 3 parts must pass
        is_clickout_eligible = False
        clickout_url = None
        if not excluded:
            link = api_offer.get("link") or {}
            if link.get("clickout_available"):
                path = link.get("clickout_url")
                ranking = (api_offer.get("ranking") or {}).get("item_price") or {}
                if (
                    path
                    and isinstance(path, str)
                    and _is_valid_clickout_path(path)
                    and ranking.get("ranking_eligible") is True
                ):
                    is_clickout_eligible = True
                    clickout_url = path

        exclusion_reason = None
        if excluded:
            comparison_status = api_offer.get("comparison_status")
            if comparison_status == "excluded_currency_mismatch":
                exclusion_reason = "Annen valuta – ikke sammenlignbar"
            elif comparison_status == "excluded_vat_basis_unknown":
                exclusion_reason = "Ukjent mva-grunnlag – ikke sammenlignbar"
            else:
                exclusion_reason = "Ikke sammenlignbar"

        is_item_winner = not excluded and offer_id == lowest_item_id
        is_total_winner = not excluded and offer_id == lowest_total_id

        return cls(
            offer_id=offer_id,
            advertiser=str(advertiser),
            item_price=item_price,
            known_total_price=total_price,
            shipping=shipping,
            availability=availability,
            is_stale=is_stale,
            stale_since=stale_since,
            is_withdrawn=is_withdrawn,
            is_excluded=excluded,
            exclusion_reason=exclusion_reason,
            is_clickout_eligible=is_clickout_eligible,
            clickout_url=clickout_url,
            is_item_price_winner=is_item_winner,
            is_total_price_winner=is_total_winner,
        )


@dataclass(frozen=True)
class ProductComparisonView:
    """Safe view-data for a product detail page."""
    identity: ProductIdentity
    offers: list[OfferView]
    excluded_offers: list[OfferView]
    lowest_item_price_winner: OfferView | None
    lowest_total_price_winner: OfferView | None

    @classmethod
    def from_api(cls, api_response: dict, *, fallback_product: dict | None = None) -> ProductComparisonView:
        """Create ProductComparisonView from /offers detail response.

        Args:
            api_response: Response from GET /api/v1/properties/sjekkpris-no/catalogue/{ns}/{slug}/offers
            fallback_product: Catalog product entry (for fallback name/slug if detail identity is incomplete)
        """
        identity_data = api_response.get("identity") or {}
        identity = ProductIdentity.from_api(identity_data, product_fallback=fallback_product)
        if not identity:
            raise ValueError("Could not extract product identity from response")

        # Resolve offers and find winner references
        offers = api_response.get("offers") or []
        excluded = api_response.get("excluded") or []

        lowest_item_id = api_response.get("lowest_item_price")
        lowest_total_id = api_response.get("lowest_known_total_price")

        # Build offer views
        offer_views = []
        for offer_data in offers:
            view = OfferView.from_api(
                offer_data,
                lowest_item_id=lowest_item_id,
                lowest_total_id=lowest_total_id,
                excluded=False,
            )
            offer_views.append(view)

        excluded_views = []
        for offer_data in excluded:
            view = OfferView.from_api(
                offer_data,
                lowest_item_id=None,  # Never winner in excluded
                lowest_total_id=None,
                excluded=True,
            )
            excluded_views.append(view)

        # Find actual winner objects (or None if reference doesn't resolve)
        lowest_item_winner = None
        if lowest_item_id:
            matching = [o for o in offer_views if o.offer_id == lowest_item_id]
            if matching:
                lowest_item_winner = matching[0]

        lowest_total_winner = None
        if lowest_total_id:
            matching = [o for o in offer_views if o.offer_id == lowest_total_id]
            if matching and matching[0].known_total_price:
                # Validate total-price winner: shipping must not be test data
                winner = matching[0]
                if not winner.shipping.is_test_data:
                    lowest_total_winner = winner

        return cls(
            identity=identity,
            offers=offer_views,
            excluded_offers=excluded_views,
            lowest_item_price_winner=lowest_item_winner,
            lowest_total_price_winner=lowest_total_winner,
        )


@dataclass(frozen=True)
class ProductCardView:
    """Safe view-data for a product card in a grid/list."""
    name: str
    slug: str
    namespace: str
    lowest_item_price: Money | None
    lowest_item_price_confirmed_at: str | None  # ISO date or None
    offer_count: int

    @classmethod
    def from_api(cls, api_product: dict) -> ProductCardView:
        """Create ProductCardView from catalog product entry."""
        name = api_product.get("local_name") or api_product.get("local_slug") or "Ukjent produkt"
        slug = api_product.get("local_slug")
        namespace = api_product.get("namespace")

        if not slug or not namespace:
            raise ValueError("Product missing slug or namespace")

        price = Money.from_api(api_product.get("lowest_item_price"))
        confirmed_at = api_product.get("lowest_item_price_confirmed_at")

        # offer_count includes both offers and excluded; show raw count
        offer_count = int(api_product.get("offer_count") or 0)

        return cls(
            name=str(name),
            slug=slug,
            namespace=namespace,
            lowest_item_price=price,
            lowest_item_price_confirmed_at=confirmed_at,
            offer_count=offer_count,
        )


# -- Utility functions ---


def _safe_str(value: object) -> str | None:
    """Convert value to string or None."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if value else None
    return str(value) if value else None


def _is_valid_clickout_path(path: str) -> bool:
    """Validate clickout path format: /go/tgt_[26 Crockford chars]."""
    import re

    pattern = re.compile(r"^/go/tgt_[0-9A-HJKMNP-TV-Z]{26}$")
    return bool(pattern.match(path))
