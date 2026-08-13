import React, { useEffect, useRef } from "react";

const SCORE_ROWS = [
  { key: "price_score",           label: "Price",           weight: "40%" },
  { key: "customer_rating_score", label: "Customer Rating", weight: "25%" },
  { key: "seller_score",          label: "Seller Quality",  weight: "15%" },
  { key: "warranty_score",        label: "Warranty",        weight: "12%" },
  { key: "condition_score",       label: "Condition",       weight: "8%"  },
];

function barClass(score) {
  if (score >= 70) return "high";
  if (score >= 40) return "mid";
  return "low";
}

function getDomain(url) {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return url; }
}

function ScoreCard({ listing, deal }) {
  const fillRefs = useRef([]);

  // Animate bars on mount
  useEffect(() => {
    const timeouts = SCORE_ROWS.map((row, i) => {
      return setTimeout(() => {
        const el = fillRefs.current[i];
        if (el) el.style.width = `${deal[row.key] ?? 0}%`;
      }, 80 + i * 80);
    });
    return () => timeouts.forEach(clearTimeout);
  }, [deal]);

  const overall = deal?.final_score ?? 0;
  const overallClass = overall >= 70 ? "high" : overall >= 40 ? "mid" : "low";
  const domain = getDomain(listing.source_url);

  return (
    <div className="card score-chart-card">
      <div className="score-chart-title">Score Breakdown</div>
      <div className="score-chart-domain">
        <span>{domain}</span>
        {deal?.rank === 1 && <span className="winner-badge">🏆 #1</span>}
      </div>

      {SCORE_ROWS.map((row, i) => {
        const val = deal?.[row.key] ?? 0;
        return (
          <div className="score-row" key={row.key}>
            <div className="score-row-header">
              <span className="score-row-label">
                {row.label}
                <span style={{ color: "var(--text-muted)", fontWeight: 500, marginLeft: 4 }}>
                  ({row.weight})
                </span>
              </span>
              <span className="score-row-value">{val.toFixed(1)}</span>
            </div>
            <div className="score-bar-track">
              <div
                ref={(el) => (fillRefs.current[i] = el)}
                className={`score-bar-fill ${barClass(val)}`}
                style={{ width: "0%" }}
              />
            </div>
          </div>
        );
      })}

      <div className="overall-score-display">
        <span className="overall-score-label">Overall Score</span>
        <span className={`overall-score-number ${overallClass}`}>
          {overall.toFixed(1)}
          <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-muted)" }}>/100</span>
        </span>
      </div>
    </div>
  );
}

export default function ScoreChart({ listings, deals }) {
  return (
    <div className="score-chart-grid">
      {listings.map((listing, i) => (
        <ScoreCard
          key={i}
          listing={listing}
          deal={deals.find((d) => d.listing_index === i)}
        />
      ))}
    </div>
  );
}
