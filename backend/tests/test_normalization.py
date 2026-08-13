from app.services.normalization.normalization_service import NormalizationService


def test_normalize_parses_currency_price_and_rating():
    service = NormalizationService()
    raw = {
        "source_url": "https://example.com/product",
        "product_name": "  Test   Product ",
        "price": "₹47,999",
        "seller_rating": "4.6 out of 5",
        "warranty": "1 Year Warranty",
        "condition": "Brand New",
    }
    result = service.normalize(raw)

    assert result.product_name == "Test Product"
    assert result.price == 47999.0
    assert result.currency == "INR"
    assert result.seller_rating == 4.6
    assert result.condition == "new"
    assert result.warranty == "1 Year Warranty"


def test_normalize_missing_fields_become_none_not_zero():
    service = NormalizationService()
    raw = {"source_url": "https://example.com/product"}
    result = service.normalize(raw)

    assert result.price is None
    assert result.delivery_charge is None
    assert result.seller_rating is None
    assert result.condition == "unknown"


def test_normalize_detects_free_delivery_text():
    service = NormalizationService()
    raw = {
        "source_url": "https://example.com/product",
        "description": "Get FREE Delivery on this item",
    }
    result = service.normalize(raw)
    assert result.delivery_charge == 0.0


def test_normalize_does_not_invent_delivery_charge():
    service = NormalizationService()
    raw = {"source_url": "https://example.com/product", "description": "Ships in 3-5 days"}
    result = service.normalize(raw)
    assert result.delivery_charge is None
