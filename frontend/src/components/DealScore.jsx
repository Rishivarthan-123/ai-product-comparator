import React from "react";

export default function DealScore({ score }) {
  if (score === null || score === undefined) return null;
  const cls = score >= 70 ? "high" : score >= 40 ? "mid" : "low";
  const emoji = score >= 70 ? "🔥" : score >= 40 ? "👍" : "⚠️";
  return (
    <span className={`score-badge ${cls}`}>
      {emoji} Deal Score: {score.toFixed(1)}/100
    </span>
  );
}
