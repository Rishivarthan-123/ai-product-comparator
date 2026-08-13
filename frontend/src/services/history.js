import { getCurrentUser } from "./auth.js";

// localStorage-based comparison history per user
const STORAGE_PREFIX = "ai_comparator_history_";
const GUEST_KEY = "ai_comparator_history_guest";
const MAX_ITEMS = 10;

function getStorageKey() {
  const user = getCurrentUser();
  return user ? `${STORAGE_PREFIX}${user.username.toLowerCase()}` : GUEST_KEY;
}

export function saveComparison(result) {
  try {
    const history = getHistory();
    const entry = {
      id:        Date.now(),
      timestamp: new Date().toISOString(),
      listing_count: result.listing_count,
      domains:   result.listings.map((l) => {
        try { return new URL(l.source_url).hostname.replace("www.", ""); }
        catch { return l.source_url; }
      }),
      best_name: result.recommendation?.product_name ||
                 result.listings[result.recommendation?.best_listing_index ?? 0]?.product_name ||
                 "Unknown product",
      final_score: result.ranked_deals?.find(d => d.rank === 1)?.final_score ?? 0,
      result,
    };
    const updated = [entry, ...history].slice(0, MAX_ITEMS);
    localStorage.setItem(getStorageKey(), JSON.stringify(updated));
  } catch (e) {
    // localStorage unavailable — ignore
  }
}

export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(getStorageKey()) || "[]");
  } catch {
    return [];
  }
}

export function clearHistory() {
  try {
    localStorage.removeItem(getStorageKey());
  } catch {}
}
