import React from "react";

const FALLBACK =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='200' height='160'><rect width='100%' height='100%' fill='%231c2033'/><text x='50%' y='50%' font-family='sans-serif' font-size='12' fill='%234a5568' text-anchor='middle' dy='.3em'>No image</text></svg>`
  );

function fmt(amount, currency) {
  if (amount == null) return "—";
  const sym = currency === "INR" ? "₹" : currency ? `${currency} ` : "";
  return `${sym}${Number(amount).toLocaleString("en-IN")}`;
}

function getDomain(url) {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return url; }
}

function StarRating({ rating, count }) {
  if (!rating) return null;
  const full = Math.floor(rating);
  const half = rating - full >= 0.4;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, marginTop: 4 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} style={{ color: i < full ? "#f59e0b" : (i === full && half ? "#f59e0b" : "#374151"), fontSize: 13 }}>
          {i < full ? "★" : (i === full && half ? "⯨" : "☆")}
        </span>
      ))}
      <span style={{ color: "var(--text-secondary)", fontWeight: 700 }}>{rating.toFixed(1)}</span>
      {count && <span style={{ color: "var(--text-muted)" }}>({count.toLocaleString()} reviews)</span>}
    </div>
  );
}

export default function ProductCard({ listing, deal, isWinner }) {
  return (
    <div className={`card product-card ${isWinner ? "winner" : ""}`}>
      <div className="img-wrap">
        <img
          src={listing.image || FALLBACK}
          alt={listing.product_name || "Product"}
          onError={(e) => (e.target.src = FALLBACK)}
        />
      </div>

      <div className="listing-domain-tag">
        <a href={listing.source_url} target="_blank" rel="noopener noreferrer">
          🔗 {getDomain(listing.source_url)}
        </a>
      </div>

      <h4>
        {listing.product_name || (
          <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Name unavailable</span>
        )}
        {isWinner && <span className="winner-badge">🏆 BEST</span>}
      </h4>

      <div className="card-price">{fmt(deal?.effective_price, listing.currency)}</div>

      <StarRating rating={listing.customer_rating} count={listing.customer_rating_count} />

      <div className="card-seller" style={{ marginTop: 6 }}>
        {listing.seller_name || getDomain(listing.source_url)}
        {listing.seller_rating != null && ` · Seller ${listing.seller_rating}/5`}
      </div>
    </div>
  );
}
