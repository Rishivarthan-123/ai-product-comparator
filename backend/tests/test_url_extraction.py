import pytest

from app.services.url.url_extraction_service import URLExtractionService
from app.utils.errors import InvalidURLError
from app.utils.text_utils import parse_currency, parse_price, parse_rating, safe_str


def test_validate_url_accepts_valid_https_url():
    service = URLExtractionService()
    assert service.validate_url("https://example.com/product") == "https://example.com/product"


@pytest.mark.parametrize("bad_url", ["", "   ", "not-a-url", "ftp://example.com", None])
def test_validate_url_rejects_invalid_urls(bad_url):
    service = URLExtractionService()
    with pytest.raises(InvalidURLError):
        service.validate_url(bad_url)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("₹47,999", 47999.0),
        ("Rs. 47,999", 47999.0),
        ("INR 47999", 47999.0),
        (47999, 47999.0),
        (47999.5, 47999.5),
        (None, None),
        ("Price unavailable", None),
    ],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize(
    "raw,fallback,expected",
    [
        ("INR", None, "INR"),
        (None, "₹4,999", "INR"),
        ("USD", None, "USD"),
        (None, "$49.99", "USD"),
        (None, None, None),
    ],
)
def test_parse_currency(raw, fallback, expected):
    assert parse_currency(raw, fallback) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4.5", 4.5),
        ("4.5 out of 5", 4.5),
        ("9/10", 4.5),
        (None, None),
    ],
)
def test_parse_rating(raw, expected):
    assert parse_rating(raw) == expected


def test_safe_str_handles_list_values_without_crashing():
    # Simulates BeautifulSoup returning an AttributeValueList for
    # multi-valued attributes.
    assert safe_str(["free", "shipping"]) == "free shipping"
    assert safe_str([]) is None
    assert safe_str(None) is None
