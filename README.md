# AI Product Comparator

An AI-powered full-stack application that lets a user paste product URLs from
different e-commerce websites and automatically extracts, normalizes,
matches, scores, ranks, and recommends the best overall deal — no manual
data entry required.

## Problem Statement

Online shopping makes it hard to compare the same (or similar) product
across multiple sellers, because price, delivery charges, seller rating,
warranty, and condition are all presented differently on every website.
This project automates that comparison: **paste product links → click
compare → AI does the rest.**

## Features

- Paste 2+ product URLs — no manual entry of product name, price, seller, etc.
- Generic, non-Amazon-specific extraction: JSON-LD → OpenGraph → meta tags →
  visible HTML → Gemini AI fallback (in that priority order)
- Normalizes price, currency, seller rating, warranty, and condition into a
  common structure across any website
- Determines whether pasted listings are actually the same/comparable product
- Calculates effective price (price + delivery, never invents delivery cost)
- Weighted deal score: Price 50%, Seller 25%, Warranty 15%, Condition 10%
- Ranks listings and recommends the best deal with a human-readable explanation
- Clean, modern, responsive UI with a full attribute comparison table
- Robust error handling — never exposes raw tracebacks; every failure mode
  (invalid URL, unreachable site, AI quota exceeded, malformed AI response,
  etc.) returns a clear JSON error

## Architecture

```
User pastes URLs (React frontend)
        │
        ▼
POST /compare-urls (FastAPI backend)
        │
        ▼
URLExtractionService  → fetch page, parse JSON-LD / OpenGraph / meta / HTML
        │
        ▼
GeminiService (fallback only, when structural extraction is incomplete)
        │
        ▼
NormalizationService  → common NormalizedProduct structure
        │
        ▼
MatchingService        → is_match + confidence between listings
        │
        ▼
DealScoringService      → price/seller/warranty/condition scores + final score
        │
        ▼
RecommendationService   → best deal + plain-English explanation
        │
        ▼
JSON response → rendered by React frontend
```

## Technology Stack

**Backend:** Python, FastAPI, Uvicorn, Pydantic, Requests, BeautifulSoup4,
python-dotenv, Google Gemini SDK (`google-genai`), Pytest

**Frontend:** React, Vite, Axios, plain CSS (no UI framework)

## Project Structure

```
ai-product-comparator/
├── backend/
│   ├── app/
│   │   ├── main.py                       FastAPI app, routes, error handlers
│   │   ├── schemas/product.py            Pydantic request/response models
│   │   ├── services/
│   │   │   ├── url/url_extraction_service.py
│   │   │   ├── gemini/gemini_service.py
│   │   │   ├── normalization/normalization_service.py
│   │   │   ├── matching/matching_service.py
│   │   │   ├── scoring/deal_scoring_service.py
│   │   │   └── recommendation/recommendation_service.py
│   │   └── utils/
│   │       ├── errors.py                 Custom exception types
│   │       └── text_utils.py             Safe price/currency/rating parsing
│   ├── tests/                            Pytest suite with mocked HTML fixtures
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/                   URLInput, ProductCard, ComparisonTable,
    │   │                                  DealScore, RecommendationCard, LoadingState
    │   ├── pages/                        Home.jsx, Results.jsx
    │   ├── services/api.js               Axios client (extractProduct, compareProducts)
    │   └── App.jsx
    ├── index.html
    └── package.json
```

## Installation

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set GEMINI_API_KEY=your_real_key
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Environment Variables

Backend `.env` (never commit this file):

```
GEMINI_API_KEY=your_key_here
```

If `GEMINI_API_KEY` is not set, the app still works — it simply skips the
AI fallback step and relies on structural extraction (JSON-LD / OpenGraph /
meta tags / visible HTML) only.

## Running the Application

**Backend:**

```bash
cd backend
uvicorn app.main:app --reload
```
Runs on `http://127.0.0.1:8000`.

**Frontend:**

```bash
cd frontend
npm run dev
```
Runs on `http://localhost:5173`.

Open `http://localhost:5173`, paste 2+ product URLs, and click **Compare Products**.

## API Endpoints

| Method | Path            | Description                                   |
|--------|-----------------|------------------------------------------------|
| GET    | `/`             | Health check                                   |
| GET    | `/health`       | Health status                                  |
| POST   | `/extract-url`  | Extract a single normalized product listing    |
| POST   | `/compare-urls` | Extract, normalize, match, score, rank, recommend across 2+ URLs |

### `POST /extract-url`

```json
{ "url": "https://example.com/product" }
```

### `POST /compare-urls`

```json
{ "urls": ["https://example.com/product1", "https://example.com/product2"] }
```

Response:

```json
{
  "listing_count": 2,
  "listings": [ /* NormalizedProduct[] */ ],
  "comparisons": [ /* MatchResult[] */ ],
  "matched_listing_count": 2,
  "ranked_deals": [ /* RankedDeal[] */ ],
  "recommendation": { /* Recommendation */ }
}
```

## Postman Testing Examples

1. **Health check** — `GET http://127.0.0.1:8000/health`
2. **Extract single listing** — `POST http://127.0.0.1:8000/extract-url`
   Body (raw JSON): `{"url": "https://www.flipkart.com/some-product/p/itm..."}`
3. **Compare listings** — `POST http://127.0.0.1:8000/compare-urls`
   Body (raw JSON):
   ```json
   { "urls": [
       "https://www.flipkart.com/some-product/p/itm...",
       "https://www.croma.com/some-product/p/..."
   ] }
   ```
4. **Invalid URL** — `POST /extract-url` with `{"url": "not-a-url"}` → `400`
5. **Too few URLs** — `POST /compare-urls` with `{"urls": ["one-url"]}` → `422`

## Running Tests

```bash
cd backend
pytest -v
```

Tests cover URL validation, price/currency/rating parsing, JSON-LD/OpenGraph
extraction against mocked HTML fixtures (no live scraping in unit tests),
normalization, product matching, all four scoring functions plus the
weighted final score and ranking, and recommendation-explanation generation
(including edge cases like missing seller/product names).

## Known Limitations

- Websites that heavily rely on JavaScript rendering or active anti-bot/CAPTCHA
  protection may return incomplete data; the app reports this clearly instead
  of failing silently or fabricating data. It never bypasses CAPTCHAs,
  authentication, or paywalls.
- Product matching uses text-similarity heuristics (name/brand/model), not a
  universal product-identity database, so very differently worded listings of
  the same item may occasionally be flagged as "not a match."
- Gemini AI extraction is a best-effort fallback; if the API key is missing,
  quota is exceeded, or the model output isn't valid JSON, the app degrades
  gracefully to structural-extraction-only results rather than failing.

## Future Improvements

- Browser automation (e.g. Playwright) as a legitimate, permission-respecting
  fallback for JS-heavy pages
- Caching extracted listings by URL to avoid re-scraping on repeat comparisons
- Support for official retailer/affiliate APIs where available
- Persisting comparison history per user
- Multi-currency conversion for cross-region comparisons
