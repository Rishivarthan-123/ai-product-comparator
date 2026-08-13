import React, { useEffect, useRef } from "react";
import { getHistory, clearHistory } from "../services/history.js";

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60)  return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function HistoryPanel({ onClose, onRestore }) {
  const history = getHistory();
  const panelRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    function handleKey(e) { if (e.key === "Escape") onClose(); }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  function handleClear() {
    clearHistory();
    onClose();
  }

  return (
    <>
      <div className="history-overlay" onClick={onClose} />
      <aside className="history-panel" ref={panelRef}>
        <div className="history-panel-header">
          <h3>🕐 History</h3>
          <button className="panel-close-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="history-list">
          {history.length === 0 ? (
            <div className="history-empty">
              <span style={{ fontSize: 32 }}>📋</span>
              <span>No comparisons yet.<br />Run a comparison to see it here.</span>
            </div>
          ) : (
            history.map((entry) => (
              <div
                key={entry.id}
                className="history-item"
                onClick={() => { onRestore(entry.result); onClose(); }}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === "Enter" && (onRestore(entry.result), onClose())}
              >
                <div className="history-item-title">{entry.best_name}</div>
                <div className="history-item-meta">
                  <span className="history-item-count">{entry.listing_count} listings</span>
                  <span>{entry.domains.join(" vs ")}</span>
                  <span style={{ marginLeft: "auto", color: "var(--text-muted)", fontSize: 11 }}>
                    {timeAgo(entry.timestamp)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {history.length > 0 && (
          <div className="history-panel-footer">
            <button className="clear-history-btn" onClick={handleClear}>
              🗑 Clear All History
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
