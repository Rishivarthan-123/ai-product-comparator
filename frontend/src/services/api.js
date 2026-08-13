import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

/**
 * Extracts a friendly error message from an Axios error, falling back to a
 * generic message if the backend didn't return a `detail` field.
 */
function extractErrorMessage(error) {
  if (error.response && error.response.data && error.response.data.detail) {
    const detail = error.response.data.detail;
    if (Array.isArray(detail)) {
      // FastAPI validation errors come back as a list of objects.
      return detail.map((d) => d.msg || JSON.stringify(d)).join(" ");
    }
    return detail;
  }
  if (error.code === "ECONNABORTED") {
    return "The request took too long. Please try again.";
  }
  if (error.message === "Network Error") {
    return "Could not reach the backend. Make sure the server is running.";
  }
  return "Something went wrong. Please try again.";
}

/**
 * Extract product information from a single product URL.
 * @param {string} url
 */
export async function extractProduct(url) {
  try {
    const response = await api.post("/extract-url", { url });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
}

/**
 * Compare multiple product URLs and get ranked deals + a recommendation.
 * @param {string[]} urls
 */
export async function compareProducts(urls) {
  try {
    const response = await api.post("/compare-urls", { urls });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
}

export default api;
