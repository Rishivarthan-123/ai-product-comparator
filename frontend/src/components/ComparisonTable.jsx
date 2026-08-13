import React from "react";

function fmt(value, suffix = "") {
  if (value == null || value === "") return "—";
  return `${value}${suffix}`;
}

function fmtMoney(amount, currency) {
  if (amount == null) return "—";
  const sym = currency === "INR" ? "₹" : currency ? `${currency} ` : "";
  return `${sym}${Number(amount).toLocaleString("en-IN")}`;
}

function StarCell({ rating, count }) {
  if (!rating) return <span>—</span>;
  const stars = "★".repeat(Math.round(rating)) + "☆".repeat(5 - Math.round(rating));
  return (
    <span style={{ whiteSpace: "nowrap" }}>
      <span style={{ color: "#f59e0b" }}>{stars}</span>
      {" "}{rating.toFixed(1)}/5
      {count ? <span style={{ color: "var(--text-muted)", fontSize: 11 }}> ({count.toLocaleString()})</span> : ""}
    </span>
  );
}

export default function ComparisonTable({ listings, deals, winnerIndex }) {
  const dealByIndex = {};
  deals.forEach((d) => { dealByIndex[d.listing_index] = d; });

  const rows = [
    { label: "Product",           render: (l)    => fmt(l.product_name) },
    { label: "Brand",             render: (l)    => fmt(l.brand) },
    { label: "Model",             render: (l)    => fmt(l.model) },
    { label: "Price",             render: (l, d) => fmtMoney(d?.price, l.currency) },
    { label: "Delivery",          render: (l, d) => fmtMoney(d?.delivery_charge, l.currency) },
    { label: "Effective Price",   render: (l, d) => fmtMoney(d?.effective_price, l.currency) },
    { label: "Customer Rating",   render: (l)    => <StarCell rating={l.customer_rating} count={l.customer_rating_count} /> },
    { label: "Seller",            render: (l)    => fmt(l.seller_name) },
    { label: "Seller Rating",     render: (l)    => l.seller_rating != null ? `${l.seller_rating}/5` : "—" },
    { label: "Warranty",          render: (l)    => fmt(l.warranty) },
    { label: "Condition",         render: (l)    => fmt(l.condition) },
    { label: "Availability",      render: (l)    => fmt(l.availability) },
    { label: "─── Scores ───",    render: ()     => "", isHeader: true },
    { label: "Price Score (40%)",           render: (l, d) => fmt(d?.price_score?.toFixed(1)) },
    { label: "Customer Rating Score (25%)", render: (l, d) => fmt(d?.customer_rating_score?.toFixed(1)) },
    { label: "Seller Score (15%)",          render: (l, d) => fmt(d?.seller_score?.toFixed(1)) },
    { label: "Warranty Score (12%)",        render: (l, d) => fmt(d?.warranty_score?.toFixed(1)) },
    { label: "Condition Score (8%)",        render: (l, d) => fmt(d?.condition_score?.toFixed(1)) },
    { label: "Overall Score",               render: (l, d) => d?.final_score != null ? <strong>{d.final_score.toFixed(1)}/100</strong> : "—" },
    { label: "Rank",              render: (l, d) => d?.rank != null ? `#${d.rank}` : "—" },
  ];

  return (
    <div className="table-wrapper">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Attribute</th>
            {listings.map((l, i) => (
              <th key={i} className={i === winnerIndex ? "winner-col" : ""}>
                Listing {i + 1}
                {i === winnerIndex && <span className="winner-badge" style={{ marginLeft: 6 }}>WINNER</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} style={row.isHeader ? { background: "var(--bg-elevated)" } : {}}>
              <td className="row-label" style={row.isHeader ? { color: "var(--text-muted)", fontSize: 11, letterSpacing: "0.05em" } : {}}>
                {row.label}
              </td>
              {listings.map((l, i) => (
                <td key={i} className={i === winnerIndex ? "winner-col" : ""}>
                  {row.isHeader ? "" : row.render(l, dealByIndex[i])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
