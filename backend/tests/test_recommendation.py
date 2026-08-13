from app.schemas.product import NormalizedProduct, RankedDeal
from app.services.recommendation.recommendation_service import RecommendationService


def make_listing(**overrides):
    base = {"source_url": "https://example.com/1", "product_name": "Test Product"}
    base.update(overrides)
    return NormalizedProduct(**base)


def make_deal(**overrides):
    base = dict(
        rank=1,
        listing_index=0,
        product_name="Test Product",
        seller_name="Example Store",
        price=1000.0,
        delivery_charge=0.0,
        effective_price=1000.0,
        price_score=100.0,
        seller_score=90.0,
        warranty_score=90.0,
        condition_score=100.0,
        final_score=95.0,
    )
    base.update(overrides)
    return RankedDeal(**base)


def test_recommendation_picks_rank_one_and_explains_advantages():
    service = RecommendationService()
    listings = [make_listing(), make_listing(source_url="https://example.com/2", product_name="Rival Product")]
    best = make_deal(rank=1, listing_index=0)
    worse = make_deal(
        rank=2,
        listing_index=1,
        product_name="Rival Product",
        effective_price=1200.0,
        price_score=83.3,
        seller_score=60.0,
        warranty_score=40.0,
        condition_score=50.0,
        final_score=65.0,
    )
    recommendation = service.recommend(listings, [best, worse])

    assert recommendation.best_listing_index == 0
    assert "lowest effective price" in recommendation.explanation
    assert recommendation.savings == 200.0


def test_recommendation_does_not_claim_null_seller_is_best():
    service = RecommendationService()
    listings = [make_listing(seller_name=None)]
    deal = make_deal(seller_name=None, seller_score=0.0)
    recommendation = service.recommend(listings, [deal])

    assert "None is the best seller" not in recommendation.explanation
    assert recommendation.explanation  # still produces a valid sentence


def test_recommendation_uses_ordinal_when_name_missing():
    service = RecommendationService()
    listings = [make_listing(product_name=None)]
    deal = make_deal(product_name=None)
    recommendation = service.recommend(listings, [deal])
    assert "second listing" not in recommendation.explanation  # only one listing => "first"
    assert recommendation.explanation.startswith("The first listing")
