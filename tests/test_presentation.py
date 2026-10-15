"""Test presentation adapters: view-data models and ProductCard."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from presentation import (
    Money,
    ProductIdentity,
    Shipping,
    Availability,
    OfferView,
    ProductComparisonView,
    ProductCardView,
)


class MoneyTest(unittest.TestCase):
    def test_valid_money_from_api(self):
        data = {"minor": 129900, "currency": "NOK"}
        m = Money.from_api(data)
        self.assertEqual(m.minor, 129900)
        self.assertEqual(m.currency, "NOK")

    def test_none_money_from_api(self):
        self.assertIsNone(Money.from_api(None))

    def test_incomplete_money_from_api(self):
        self.assertIsNone(Money.from_api({"minor": 129900}))
        self.assertIsNone(Money.from_api({"currency": "NOK"}))

    def test_money_immutable(self):
        m = Money(129900, "NOK")
        with self.assertRaises(AttributeError):
            m.minor = 100000


class ProductIdentityTest(unittest.TestCase):
    def test_complete_identity(self):
        api_data = {
            "local_name": "Test Product",
            "local_slug": "test-product",
            "namespace": "catalogue",
            "local_brand": "Brand",
            "local_category": "Category",
            "local_pack_size": "1 pack",
            "image": {"url": "https://example.com/image.jpg"},
        }
        identity = ProductIdentity.from_api(api_data)
        self.assertEqual(identity.local_name, "Test Product")
        self.assertEqual(identity.local_brand, "Brand")
        self.assertEqual(identity.image_url, "https://example.com/image.jpg")

    def test_minimal_identity(self):
        api_data = {
            "local_name": "Test Product",
            "local_slug": "test-product",
            "namespace": "catalogue",
        }
        identity = ProductIdentity.from_api(api_data)
        self.assertIsNotNone(identity)
        self.assertIsNone(identity.local_brand)

    def test_identity_missing_required(self):
        # Missing name
        api_data = {"local_slug": "test-product", "namespace": "catalogue"}
        self.assertIsNone(ProductIdentity.from_api(api_data))

    def test_identity_with_fallback(self):
        identity = ProductIdentity.from_api(
            {},
            product_fallback={
                "local_name": "Fallback Name",
                "local_slug": "fallback-slug",
                "namespace": "catalogue",
            },
        )
        self.assertEqual(identity.local_name, "Fallback Name")

    def test_identity_null_brand_ignored(self):
        api_data = {
            "local_name": "Test",
            "local_slug": "test",
            "namespace": "catalogue",
            "local_brand": None,
        }
        identity = ProductIdentity.from_api(api_data)
        self.assertIsNone(identity.local_brand)

    def test_identity_empty_string_brand_ignored(self):
        api_data = {
            "local_name": "Test",
            "local_slug": "test",
            "namespace": "catalogue",
            "local_brand": "",
        }
        identity = ProductIdentity.from_api(api_data)
        self.assertIsNone(identity.local_brand)


class ShippingTest(unittest.TestCase):
    def test_free_shipping(self):
        shipping_data = {"state": "confirmed_free", "terms": {"is_test_data": False}}
        shipping = Shipping.from_api(shipping_data)
        self.assertEqual(shipping.state, "confirmed_free")
        self.assertFalse(shipping.is_test_data)

    def test_known_amount_shipping(self):
        shipping_data = {
            "state": "known_amount",
            "amount": {"minor": 10000, "currency": "NOK"},
            "terms": {"is_test_data": False},
        }
        shipping = Shipping.from_api(shipping_data)
        self.assertEqual(shipping.state, "known_amount")
        self.assertIsNotNone(shipping.amount)
        self.assertEqual(shipping.amount.minor, 10000)

    def test_test_data_shipping(self):
        shipping_data = {
            "state": "known_amount",
            "amount": {"minor": 10000, "currency": "NOK"},
            "terms": {"is_test_data": True},
        }
        shipping = Shipping.from_api(shipping_data)
        self.assertTrue(shipping.is_test_data)

    def test_missing_shipping(self):
        shipping = Shipping.from_api(None)
        self.assertIsNone(shipping.state)
        self.assertIsNone(shipping.amount)
        self.assertFalse(shipping.is_test_data)


class AvailabilityTest(unittest.TestCase):
    def test_in_stock(self):
        avail_data = {"status": "in_stock"}
        avail = Availability.from_api(avail_data)
        self.assertEqual(avail.status, "in_stock")

    def test_out_of_stock(self):
        avail_data = {"status": "out_of_stock"}
        avail = Availability.from_api(avail_data)
        self.assertEqual(avail.status, "out_of_stock")

    def test_unknown_availability(self):
        avail = Availability.from_api(None)
        self.assertEqual(avail.status, "unknown")

    def test_missing_status(self):
        avail = Availability.from_api({})
        self.assertEqual(avail.status, "unknown")


class OfferViewTest(unittest.TestCase):
    def test_eligible_clickout_offer(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "in_stock"},
            "stale": False,
            "withdrawn": False,
            "link": {
                "clickout_available": True,
                "clickout_url": "/go/tgt_00000000000000000000000000",
            },
            "ranking": {
                "item_price": {"ranking_eligible": True},
            },
        }
        view = OfferView.from_api(offer_data)
        self.assertTrue(view.is_clickout_eligible)
        self.assertEqual(view.clickout_url, "/go/tgt_00000000000000000000000000")

    def test_ineligible_clickout_offer(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "out_of_stock"},
            "stale": False,
            "withdrawn": False,
            "link": {"clickout_available": True, "clickout_url": "/go/tgt_00000000000000000000000000"},
            "ranking": {"item_price": {"ranking_eligible": False}},
        }
        view = OfferView.from_api(offer_data)
        self.assertFalse(view.is_clickout_eligible)
        self.assertIsNone(view.clickout_url)

    def test_stale_offer(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "in_stock"},
            "stale": True,
            "last_confirmed_at": "2026-10-01T04:15:00+00:00",
            "withdrawn": False,
        }
        view = OfferView.from_api(offer_data)
        self.assertTrue(view.is_stale)
        self.assertEqual(view.stale_since, "2026-10-01T04:15:00+00:00")

    def test_winner_marking(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "in_stock"},
            "stale": False,
            "withdrawn": False,
        }
        view = OfferView.from_api(offer_data, lowest_item_id="o-1")
        self.assertTrue(view.is_item_price_winner)
        self.assertFalse(view.is_total_price_winner)

    def test_excluded_offer(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "in_stock"},
            "stale": False,
            "withdrawn": False,
            "comparison_status": "excluded_currency_mismatch",
        }
        view = OfferView.from_api(offer_data, excluded=True)
        self.assertTrue(view.is_excluded)
        self.assertEqual(view.exclusion_reason, "Annen valuta – ikke sammenlignbar")

    def test_bad_clickout_path(self):
        offer_data = {
            "offer_id": "o-1",
            "advertiser": "Shop",
            "item_price": {"minor": 129900, "currency": "NOK"},
            "known_total_price": None,
            "shipping": {"state": "not_provided"},
            "availability": {"status": "in_stock"},
            "stale": False,
            "withdrawn": False,
            "link": {
                "clickout_available": True,
                "clickout_url": "/api/redirect/bad-token",  # Invalid format
            },
            "ranking": {"item_price": {"ranking_eligible": True}},
        }
        view = OfferView.from_api(offer_data)
        self.assertFalse(view.is_clickout_eligible)
        self.assertIsNone(view.clickout_url)


class ProductComparisonViewTest(unittest.TestCase):
    def test_complete_response(self):
        api_response = {
            "identity": {
                "local_name": "Test Product",
                "local_slug": "test-product",
                "namespace": "catalogue",
            },
            "offers": [
                {
                    "offer_id": "o-1",
                    "advertiser": "Shop 1",
                    "item_price": {"minor": 129900, "currency": "NOK"},
                    "known_total_price": None,
                    "shipping": {"state": "not_provided"},
                    "availability": {"status": "in_stock"},
                    "stale": False,
                    "withdrawn": False,
                    "link": {"clickout_available": False},
                    "ranking": {"item_price": {"ranking_eligible": True}},
                }
            ],
            "excluded": [],
            "lowest_item_price": "o-1",
            "lowest_known_total_price": None,
        }
        view = ProductComparisonView.from_api(api_response)
        self.assertEqual(view.identity.local_name, "Test Product")
        self.assertEqual(len(view.offers), 1)
        self.assertIsNotNone(view.lowest_item_price_winner)
        self.assertIsNone(view.lowest_total_price_winner)

    def test_response_with_excluded(self):
        api_response = {
            "identity": {
                "local_name": "Test Product",
                "local_slug": "test-product",
                "namespace": "catalogue",
            },
            "offers": [
                {
                    "offer_id": "o-1",
                    "advertiser": "Shop 1",
                    "item_price": {"minor": 129900, "currency": "NOK"},
                    "known_total_price": None,
                    "shipping": {"state": "not_provided"},
                    "availability": {"status": "in_stock"},
                    "stale": False,
                    "withdrawn": False,
                    "comparison_status": None,
                }
            ],
            "excluded": [
                {
                    "offer_id": "o-2",
                    "advertiser": "Shop 2",
                    "item_price": {"minor": 99900, "currency": "EUR"},
                    "known_total_price": None,
                    "shipping": {"state": "not_provided"},
                    "availability": {"status": "in_stock"},
                    "stale": False,
                    "withdrawn": False,
                    "comparison_status": "excluded_currency_mismatch",
                }
            ],
            "lowest_item_price": "o-1",
            "lowest_known_total_price": None,
        }
        view = ProductComparisonView.from_api(api_response)
        self.assertEqual(len(view.offers), 1)
        self.assertEqual(len(view.excluded_offers), 1)
        self.assertTrue(view.excluded_offers[0].is_excluded)

    def test_missing_winner_reference(self):
        """If lowest_item_price references a non-existent offer, winner is None."""
        api_response = {
            "identity": {
                "local_name": "Test Product",
                "local_slug": "test-product",
                "namespace": "catalogue",
            },
            "offers": [
                {
                    "offer_id": "o-1",
                    "advertiser": "Shop 1",
                    "item_price": {"minor": 129900, "currency": "NOK"},
                    "known_total_price": None,
                    "shipping": {"state": "not_provided"},
                    "availability": {"status": "in_stock"},
                    "stale": False,
                    "withdrawn": False,
                }
            ],
            "excluded": [],
            "lowest_item_price": "o-999",  # References non-existent offer
            "lowest_known_total_price": None,
        }
        view = ProductComparisonView.from_api(api_response)
        self.assertIsNone(view.lowest_item_price_winner)


class ProductCardViewTest(unittest.TestCase):
    def test_complete_card(self):
        product = {
            "local_name": "Test Product",
            "local_slug": "test-product",
            "namespace": "catalogue",
            "lowest_item_price": {"minor": 129900, "currency": "NOK"},
            "lowest_item_price_confirmed_at": "2026-10-11T04:15:00+00:00",
            "offer_count": 5,
        }
        card = ProductCardView.from_api(product)
        self.assertEqual(card.name, "Test Product")
        self.assertIsNotNone(card.lowest_item_price)
        self.assertEqual(card.offer_count, 5)

    def test_card_with_no_price(self):
        product = {
            "local_name": "Test Product",
            "local_slug": "test-product",
            "namespace": "catalogue",
            "lowest_item_price": None,
            "lowest_item_price_confirmed_at": None,
            "offer_count": 1,
        }
        card = ProductCardView.from_api(product)
        self.assertIsNone(card.lowest_item_price)

    def test_card_with_fallback_name(self):
        product = {
            "local_slug": "test-product",
            "namespace": "catalogue",
            "offer_count": 0,
        }
        card = ProductCardView.from_api(product)
        self.assertEqual(card.name, "test-product")

    def test_card_missing_required(self):
        product = {"local_name": "Test"}
        with self.assertRaises(ValueError):
            ProductCardView.from_api(product)


if __name__ == "__main__":
    unittest.main()
