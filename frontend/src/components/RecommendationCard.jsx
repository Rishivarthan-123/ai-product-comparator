import React from "react";

export default function RecommendationCard({ recommendation }) {
  if (!recommendation) return null;

  return (
    <div className="card recommendation-card">
      <h3>💡 Why this is the best deal</h3>
      <p>{recommendation.explanation}</p>

      {recommendation.advantages?.length > 0 && (
        <ul className="advantage-list">
          {recommendation.advantages.map((a, i) => (
            <li key={i}>{a.charAt(0).toUpperCase() + a.slice(1)}</li>
          ))}
        </ul>
      )}

      {recommendation.savings != null && recommendation.savings > 0 && (
        <p style={{ marginTop: 14, color: "var(--success)", fontWeight: 700, fontSize: 15 }}>
          💰 You save ₹{Number(recommendation.savings).toLocaleString("en-IN")} vs the next best option.
        </p>
      )}

      {recommendation.disadvantages?.length > 0 && (
        <div className="disadvantage-note">
          {recommendation.disadvantages.map((d, i) => (
            <div key={i}>⚠ {d}</div>
          ))}
        </div>
      )}
    </div>
  );
}
