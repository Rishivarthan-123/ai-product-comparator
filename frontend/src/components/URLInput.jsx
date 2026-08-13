import React from "react";

export default function URLInput({ urls, onChange, onAdd, onRemove }) {
  return (
    <div>
      <div className="url-form-title">
        🔗 Paste Product URLs
      </div>
      {urls.map((url, index) => (
        <div className="url-row" key={index}>
          <div className="url-index">{index + 1}</div>
          <input
            id={`url-input-${index}`}
            type="url"
            value={url}
            placeholder={`https://www.example.com/product-${index + 1}`}
            onChange={(e) => onChange(index, e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
          {urls.length > 2 && (
            <button
              type="button"
              className="url-remove-btn"
              onClick={() => onRemove(index)}
              aria-label={`Remove URL ${index + 1}`}
            >
              ✕
            </button>
          )}
        </div>
      ))}
      <button type="button" className="add-url-btn" onClick={onAdd}>
        + Add another URL
      </button>
    </div>
  );
}
