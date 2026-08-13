import React, { useState } from "react";
import URLInput from "../components/URLInput.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { compareProducts } from "../services/api.js";

export default function Home({ onResult }) {
  const [urls, setUrls]       = useState(["", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  function handleChange(index, value) {
    setUrls((prev) => prev.map((u, i) => (i === index ? value : u)));
  }

  function handleAdd() {
    if (urls.length < 6) setUrls((prev) => [...prev, ""]);
  }

  function handleRemove(index) {
    setUrls((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const filled = urls.filter((u) => u.trim());
    if (filled.length < 2) {
      setError("Please enter at least 2 product URLs.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await compareProducts(filled);
      onResult(result);
    } catch (err) {
      setError(err?.detail || err?.message || "Comparison failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div>
      {/* Hero */}
      <div className="hero">
        <div className="hero-badge">✨ AI-Powered · 5-Factor Scoring</div>
        <h1>
          Find the <span className="gradient-text">Best Deal</span>
          <br />Across Any Store
        </h1>
        <p>
          Paste product URLs from any e-commerce site. Our AI compares price,
          customer ratings, seller quality, warranty, and condition to find
          the smartest buy.
        </p>
      </div>

      {/* URL Input Form */}
      <div className="url-form-wrapper">
        <form className="card url-form" onSubmit={handleSubmit}>
          {error && (
            <div className="form-error">
              <span>⚠️</span> {error}
            </div>
          )}

          <URLInput
            urls={urls}
            onChange={handleChange}
            onAdd={handleAdd}
            onRemove={handleRemove}
          />

          <button
            id="compare-btn"
            type="submit"
            className="compare-btn"
            disabled={urls.filter((u) => u.trim()).length < 2}
          >
            ⚡ Compare Products
          </button>
        </form>

        {/* What we score */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginTop: 20 }}>
          {[
            { emoji: "💰", label: "Price",          weight: "40%" },
            { emoji: "⭐", label: "Customer Rating", weight: "25%" },
            { emoji: "🏪", label: "Seller Quality",  weight: "15%" },
            { emoji: "🛡️",  label: "Warranty",        weight: "12%" },
            { emoji: "📦", label: "Condition",       weight: "8%"  },
          ].map((item) => (
            <div
              key={item.label}
              className="card"
              style={{ padding: "14px 10px", textAlign: "center", fontSize: 12 }}
            >
              <div style={{ fontSize: 20, marginBottom: 4 }}>{item.emoji}</div>
              <div style={{ fontWeight: 700, marginBottom: 2 }}>{item.label}</div>
              <div style={{ color: "var(--accent)", fontWeight: 800 }}>{item.weight}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
