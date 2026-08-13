from app.schemas.product import NormalizedProduct
from app.services.scoring.deal_scoring_service import DealScoringService


def make_product(**overrides):
    base = {
        "source_url": "https://example.com/1",
        "product_name": "Test Product",
        "price": 5000.0,
        "delivery_charge": 0.0,
        "seller_rating": 4.0,
        "warranty": "1 Year",
        "condition": "new",
    }
    base.update(overrides)
    return NormalizedProduct(**base)


def test_effective_price_adds_delivery_charge():
    service = DealScoringService()
    product = make_product(price=1000.0, delivery_charge=50.0)
    assert service.effective_price(product) == 1050.0


def test_effective_price_none_when_price_unknown():
    service = DealScoringService()
    product = make_product(price=None)
    assert service.effective_price(product) is None


def test_seller_score_scales_rating_to_100():
    service = DealScoringService()
    assert service._seller_score(4.0) == 80.0
    assert service._seller_score(None) == 0.0
    assert service._seller_score(5.0) == 100.0


def test_warranty_score_tiers():
    service = DealScoringService()
    assert service._warranty_score("2 Year Warranty") == 100.0
    assert service._warranty_score("1 Year Warranty") == 90.0
    assert service._warranty_score("6 Month Warranty") == 70.0
    assert service._warranty_score("3 Month Warranty") == 50.0
    assert service._warranty_score("Limited Warranty") == 40.0
    assert service._warranty_score(None) == 0.0


def test_condition_score_mapping():
    service = DealScoringService()
    assert service._condition_score("new") == 100.0
    assert service._condition_score("refurbished") == 70.0
    assert service._condition_score("used") == 50.0
    assert service._condition_score("unknown") == 0.0
    assert service._condition_score(None) == 0.0


def test_score_all_ranks_lowest_effective_price_highest_price_score():
    service = DealScoringService()
    cheaper = make_product(price=4000.0)
    pricier = make_product(source_url="https://example.com/2", price=6000.0)

    deals = service.score_all([cheaper, pricier])
    cheaper_deal = next(d for d in deals if d.listing_index == 0)
    pricier_deal = next(d for d in deals if d.listing_index == 1)

    assert cheaper_deal.price_score == 100.0
    assert pricier_deal.price_score < 100.0
    assert cheaper_deal.rank == 1
    assert cheaper_deal.final_score > pricier_deal.final_score


def test_final_score_weights_applied_correctly():
    service = DealScoringService()
    product = make_product(price=1000.0, delivery_charge=0.0, seller_rating=5.0, warranty="2 Year", condition="new")
    deals = service.score_all([product])
    deal = deals[0]
    # Sole listing => price_score is 100 (lowest == itself)
    expected = round(100 * 0.5 + 100 * 0.25 + 100 * 0.15 + 100 * 0.10, 2)
    assert deal.final_score == expected == 100.0
