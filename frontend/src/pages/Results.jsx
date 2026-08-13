import React, { useState } from "react";
import ProductCard from "../components/ProductCard.jsx";
import ComparisonTable from "../components/ComparisonTable.jsx";
import DealScore from "../components/DealScore.jsx";
import RecommendationCard from "../components/RecommendationCard.jsx";
import ScoreChart from "../components/ScoreChart.jsx";

const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect width='100%' height='100%' fill='%231c2033'/><text x='50%' y='50%' font-family='sans-serif' font-size='14' fill='%234a5568' text-anchor='middle' dy='.3em'>No image</text></svg>`
  );

function formatMoney(amount, currency) {
  if (amount === null || amount === undefined) return "Unknown";
  const symbol = currency === "INR" ? "₹" : currency ? `${currency} ` : "";
  return `${symbol}${Number(amount).toLocaleString("en-IN")}`;
}

function getDomain(url) {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch {
    return url;
  }
}

function isDataSparse(listing) {
  return !listing.product_name && listing.price === null;
}

export default function Results({ result, onReset }) {
  const { listings, ranked_deals: deals, recommendation, matched_listing_count, listing_count } = result;
  const [showNotes, setShowNotes] = useState(false);

  const winnerIndex = recommendation?.best_listing_index ?? 0;
  const winnerListing = listings[winnerIndex];
  const winnerDeal = deals.find((d) => d.listing_index === winnerIndex);

  const allNotes = listings.flatMap((l, i) =>
    (l.extraction_notes || []).map((note) => ({ note, domain: getDomain(l.source_url), index: i }))
  );

  const sparseListings = listings.filter(isDataSparse);
  const hasSparseData = sparseListings.length > 0;

  return (
    <div className="container">
      <div className="results-header">
        <button className="back-btn" onClick={onReset}>
          ← New Comparison
        </button>
        <div className="match-badge">
          📊 {matched_listing_count} of {listing_count} listings matched as comparable
        </div>
      </div>

      {hasSparseData && (
        <div className="extraction-warning">
          <div className="extraction-warning-header">
            <span>⚠️ Partial Product Details Extracted</span>
            <button
              className="notes-toggle"
              onClick={() => setShowNotes((s) => !s)}
            >
              {showNotes ? "Hide details ▲" : "Show details ▼"}
            </button>
          </div>
          <p>
            Some e-commerce sites (like Amazon, Flipkart, Croma) block automated text requests or require full JavaScript execution. We attempted lightweight scraping and Playwright browser rendering. Add a <strong>GEMINI_API_KEY</strong> in your environment if you haven't already to enable AI extraction fallbacks.
          </p>
          {showNotes && allNotes.length > 0 && (
            <ul className="extraction-notes-list">
              {allNotes.map(({ note, domain, index }, i) => (
                <li key={i}>
                  <strong>Listing {index + 1} ({domain}):</strong> {note}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="best-deal-banner">🏆 BEST DEAL RECOMMENDATION</div>

      <div className="card best-deal-card glow" style={{ marginBottom: "32px" }}>
        <div className="product-image-wrap">
          <img
            src={winnerListing.image || FALLBACK_IMAGE}
            alt={winnerListing.product_name || "Best deal product"}
            onError={(e) => (e.target.src = FALLBACK_IMAGE)}
          />
        </div>
        <div className="best-deal-info">
          <div className="listing-domain-tag">
            <a href={winnerListing.source_url} target="_blank" rel="noopener noreferrer">
              🔗 {getDomain(winnerListing.source_url)}
            </a>
          </div>
          <h2>
            {winnerListing.product_name || (
              <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Product name unavailable</span>
            )}
          </h2>
          <div className="best-deal-meta">
            {winnerListing.brand ? `${winnerListing.brand} · ` : ""}
            {winnerListing.model || ""}
          </div>

          <div className="price-row">
            <span className="price-effective">{formatMoney(winnerDeal?.effective_price, winnerListing.currency)}</span>
            {winnerListing.delivery_charge != null && winnerListing.delivery_charge > 0 && (
              <span className="price-original">
                (Base price: {formatMoney(winnerListing.price, winnerListing.currency)} + {formatMoney(winnerListing.delivery_charge, winnerListing.currency)} delivery)
              </span>
            )}
          </div>

          <div className="pill-row">
            <span className="pill">🏪 Seller: {winnerListing.seller_name || getDomain(winnerListing.source_url)}</span>
            <span className="pill">
              ⭐ Customer Rating: {winnerListing.customer_rating != null ? `${winnerListing.customer_rating.toFixed(1)}/5` : "N/A"}
            </span>
            <span className="pill">🛡️ Warranty: {winnerListing.warranty || "N/A"}</span>
            <span className="pill">📦 Condition: {winnerListing.condition || "unknown"}</span>
            <span className="pill">🏆 Rank #{winnerDeal?.rank ?? 1}</span>
          </div>

          <div style={{ marginTop: "12px" }}>
            <DealScore score={winnerDeal?.final_score} />
          </div>
        </div>
      </div>

      <RecommendationCard recommendation={recommendation} />

      <h3 className="section-title">📊 Deal Scores Comparison</h3>
      <ScoreChart listings={listings} deals={deals} />

      <h3 className="section-title">🛍️ All Listings</h3>
      <div className="product-grid">
        {listings.map((listing, index) => (
          <ProductCard
            key={index}
            listing={listing}
            deal={deals.find((d) => d.listing_index === index)}
            isWinner={index === winnerIndex}
          />
        ))}
      </div>

      <h3 className="section-title">📋 Full Specifications & Comparison</h3>
      <ComparisonTable listings={listings} deals={deals} winnerIndex={winnerIndex} />
    </div>
  );
}
