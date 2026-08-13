from bs4 import BeautifulSoup

from app.services.url.url_extraction_service import URLExtractionService


def test_extract_json_ld_from_fixture(sample_product_html):
    service = URLExtractionService()
    soup = BeautifulSoup(sample_product_html, "html.parser")
    data = service._extract_json_ld(soup)

    assert data["product_name"] == "Test Wireless Headphones"
    assert data["brand"] == "ExampleAudio"
    assert data["model"] == "EA-100"
    assert data["price"] == 4999.0
    assert data["currency"] == "INR"
    assert data["seller_name"] == "Example Store"
    assert data["condition"] == "new"
    assert data["seller_rating"] == 4.5


def test_extract_opengraph_from_fixture(sample_product_html):
    service = URLExtractionService()
    soup = BeautifulSoup(sample_product_html, "html.parser")
    og = service._extract_opengraph(soup)
    assert og["product_name"] == "Test Wireless Headphones"
    assert og["image"] == "https://example.com/images/headphones.jpg"


def test_extract_handles_missing_json_ld_gracefully():
    service = URLExtractionService()
    soup = BeautifulSoup("<html><head><title>No structured data</title></head><body></body></html>", "html.parser")
    data = service._extract_json_ld(soup)
    assert data == {}


def test_extract_handles_malformed_json_ld_without_crashing():
    html = """
    <html><head>
    <script type="application/ld+json">{ this is not valid json </script>
    </head><body></body></html>
    """
    service = URLExtractionService()
    soup = BeautifulSoup(html, "html.parser")
    data = service._extract_json_ld(soup)
    assert data == {}
