from app.schemas.product import NormalizedProduct
from app.services.matching.matching_service import MatchingService


def make_product(**overrides):
    base = {
        "source_url": "https://example.com/1",
        "product_name": "Test Wireless Headphones EA-100",
        "brand": "ExampleAudio",
        "model": "EA-100",
    }
    base.update(overrides)
    return NormalizedProduct(**base)


def test_matching_same_product_is_a_match():
    service = MatchingService()
    a = make_product()
    b = make_product(source_url="https://example.com/2", product_name="Test Wireless Headphones EA-100 (New)")
    result = service.compare_pair(a, b)
    assert result.is_match is True
    assert result.confidence > 0.5


def test_matching_different_products_is_not_a_match():
    service = MatchingService()
    a = make_product()
    b = make_product(
        source_url="https://example.com/2",
        product_name="Stainless Steel Water Bottle 1L",
        brand="HydroPlus",
        model=None,
    )
    result = service.compare_pair(a, b)
    assert result.is_match is False
    assert "different products" in result.reason


def test_matching_missing_names_cannot_be_compared():
    service = MatchingService()
    a = make_product(product_name=None)
    b = make_product(source_url="https://example.com/2")
    result = service.compare_pair(a, b)
    assert result.is_match is False
    assert result.confidence == 0.0
