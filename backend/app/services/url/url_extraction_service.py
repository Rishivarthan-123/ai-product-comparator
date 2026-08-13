"""URLExtractionService

Responsible for fetching a product webpage and pulling out whatever
product information is available using a layered strategy:

    1. Schema.org / JSON-LD <script type="application/ld+json">
    2. OpenGraph meta tags (og:title, og:image, og:price:amount, ...)
    3. Generic <meta> tags (itemprop, twitter:*, etc.)
    4. Visible HTML heuristics (title tag, common price/seller classes)

The service never crashes on malformed pages, never invents data, and
never fabricates a price of 0 - unknown values are always returned as
None so downstream services can treat them correctly.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.utils.errors import InvalidURLError, WebsiteUnreachableError
from app.utils.text_utils import clean_whitespace, parse_currency, parse_price, parse_rating, safe_str

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
        "Gecko/20100101 Firefox/126.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
]

def _make_headers(user_agent: str, url: str) -> dict:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    }

REQUEST_TIMEOUT_SECONDS = 20

# Phrases that strongly suggest the page did not actually render
# meaningful product content (JS-gated / anti-bot pages).
JS_BLOCKED_MARKERS = [
    "javascript is disabled",
    "enable javascript",
    "please enable cookies",
    "to discuss automated access",
    "captcha",
    "are you a robot",
    "access denied",
    "request unsuccessful",
    "to continue, please click the box",
    "robot or automated",
]


class URLExtractionService:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        # Enable cookie persistence across requests (helps with session-based sites)
        self.session.cookies.update({})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate_url(self, url: str) -> str:
        url = (url or "").strip()
        if not url:
            raise InvalidURLError("Please provide a valid product URL.")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise InvalidURLError("Please provide a valid product URL.")
        return url

    def fetch_html(self, url: str) -> str:
        last_exc: Optional[Exception] = None
        for attempt, ua in enumerate(USER_AGENTS):
            try:
                headers = _make_headers(ua, url)
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    allow_redirects=True,
                )
                if response.status_code == 200:
                    return response.text or ""
                if response.status_code in (403, 429, 503) and attempt < len(USER_AGENTS) - 1:
                    # Retry with a different user agent
                    import time as _time
                    _time.sleep(1)
                    continue
                if response.status_code >= 400:
                    raise WebsiteUnreachableError(
                        f"Unable to access the product webpage (HTTP {response.status_code}). "
                        "The site may be blocking automated access."
                    )
                return response.text or ""
            except WebsiteUnreachableError:
                raise
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                continue
            except requests.exceptions.SSLError as exc:
                raise WebsiteUnreachableError("Could not establish a secure connection to the website.") from exc
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                continue
        raise WebsiteUnreachableError(
            "Unable to access the product webpage after multiple attempts."
        ) from last_exc

    def extract(self, url: str) -> Dict[str, Any]:
        """Fetch and extract everything we can from a product URL using
        BeautifulSoup only. Returns a dict of raw (not yet normalized)
        fields plus a list of extraction_notes describing what happened."""
        url = self.validate_url(url)
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        # Derive a human-readable seller name from the domain as a fallback
        parsed_url = urlparse(url)
        domain_seller = parsed_url.netloc.replace("www.", "").split(".")[0].title()

        notes: List[str] = []
        data: Dict[str, Any] = {
            "source_url": url,
            "raw_source": self._truncate(html),
            # Pre-seed seller from domain so we always show something
            "seller_name": domain_seller,
        }

        jsonld_data = self._extract_json_ld(soup)
        if jsonld_data:
            notes.append("Extracted structured data from JSON-LD.")
            data.update(jsonld_data)

        og_data = self._extract_opengraph(soup)
        for key, value in og_data.items():
            if not data.get(key) and value:
                data[key] = value
        if og_data:
            notes.append("Supplemented fields from OpenGraph metadata.")

        meta_data = self._extract_meta_tags(soup)
        for key, value in meta_data.items():
            if not data.get(key) and value:
                data[key] = value

        html_data = self._extract_visible_html(soup)
        for key, value in html_data.items():
            if not data.get(key) and value:
                data[key] = value
        if html_data.get("product_name") and "product_name" not in jsonld_data and "product_name" not in og_data:
            notes.append("Used visible HTML heuristics for missing fields.")

        if self._looks_js_blocked(soup, data):
            notes.append(
                "This page may rely on JavaScript rendering or anti-bot protection; "
                "extraction may be incomplete."
            )

        data["extraction_notes"] = notes
        return data

    # ------------------------------------------------------------------
    # JSON-LD
    # ------------------------------------------------------------------
    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        scripts = soup.find_all("script", type=lambda v: v and "ld+json" in v)
        for script in scripts:
            raw = script.string or script.get_text() or ""
            if not raw.strip():
                continue
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            candidates = parsed if isinstance(parsed, list) else [parsed]
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                graph = candidate.get("@graph")
                nodes = graph if isinstance(graph, list) else [candidate]
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    node_type = node.get("@type")
                    type_list = node_type if isinstance(node_type, list) else [node_type]
                    if not any(t and "product" in str(t).lower() for t in type_list):
                        continue
                    result.update(self._parse_product_jsonld(node))
        return {k: v for k, v in result.items() if v not in (None, "", [])}

    def _parse_product_jsonld(self, node: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        out["product_name"] = clean_whitespace(node.get("name"))
        out["description"] = clean_whitespace(node.get("description"))
        out["image"] = self._first(node.get("image"))

        brand = node.get("brand")
        if isinstance(brand, dict):
            out["brand"] = clean_whitespace(brand.get("name"))
        else:
            out["brand"] = clean_whitespace(brand)

        out["model"] = clean_whitespace(node.get("model") or node.get("mpn") or node.get("sku"))

        offers = node.get("offers")
        offer = offers[0] if isinstance(offers, list) and offers else offers
        if isinstance(offer, dict):
            out["price"] = parse_price(offer.get("price") or offer.get("lowPrice"))
            out["currency"] = parse_currency(offer.get("priceCurrency"))
            out["availability"] = clean_whitespace(offer.get("availability"))
            seller = offer.get("seller")
            if isinstance(seller, dict):
                out["seller_name"] = clean_whitespace(seller.get("name"))
            shipping = offer.get("shippingDetails") or offer.get("deliveryLeadTime")
            if isinstance(shipping, dict):
                cost = shipping.get("shippingRate", {})
                if isinstance(cost, dict):
                    out["delivery_charge"] = parse_price(cost.get("value"))
            warranty = offer.get("warranty") or node.get("warranty")
            out["warranty"] = clean_whitespace(warranty)
            condition = offer.get("itemCondition")
            if condition:
                out["condition"] = self._simplify_condition(str(condition))

        # aggregateRating on a Product schema.org node is the CUSTOMER/PRODUCT
        # review rating — not the seller rating.
        rating = node.get("aggregateRating")
        if isinstance(rating, dict):
            out["customer_rating"] = parse_rating(rating.get("ratingValue"))
            count = rating.get("reviewCount") or rating.get("ratingCount")
            if count is not None:
                try:
                    out["customer_rating_count"] = int(float(str(count).replace(",", "")))
                except (ValueError, TypeError):
                    pass

        return out

    # ------------------------------------------------------------------
    # OpenGraph
    # ------------------------------------------------------------------
    def _extract_opengraph(self, soup: BeautifulSoup) -> Dict[str, Any]:
        og: Dict[str, Any] = {}
        mapping = {
            "og:title": "product_name",
            "og:description": "description",
            "og:image": "image",
            "product:price:amount": "price",
            "og:price:amount": "price",
            "product:price:currency": "currency",
            "og:price:currency": "currency",
            "product:brand": "brand",
            "product:availability": "availability",
            "product:condition": "condition",
        }
        for tag in soup.find_all("meta"):
            prop = safe_str(tag.get("property")) or safe_str(tag.get("name"))
            if not prop or prop not in mapping:
                continue
            field = mapping[prop]
            content = safe_str(tag.get("content"))
            if not content:
                continue
            if field == "price":
                og[field] = parse_price(content)
            elif field == "currency":
                og[field] = parse_currency(content)
            elif field == "condition":
                og[field] = self._simplify_condition(content)
            else:
                og[field] = clean_whitespace(content)
        return og

    # ------------------------------------------------------------------
    # Generic meta tags / itemprop
    # ------------------------------------------------------------------
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        itemprop_map = {
            "name": "product_name",
            "price": "price",
            "priceCurrency": "currency",
            "brand": "brand",
            "model": "model",
            "sku": "model",
            "image": "image",
            "description": "description",
            "ratingValue": "customer_rating",   # itemprop ratingValue = product review rating
            "reviewCount": "customer_rating_count",
            "ratingCount": "customer_rating_count",
            "availability": "availability",
        }
        for tag in soup.find_all(attrs={"itemprop": True}):
            prop = safe_str(tag.get("itemprop"))
            if prop not in itemprop_map:
                continue
            field = itemprop_map[prop]
            content = safe_str(tag.get("content")) or clean_whitespace(tag.get_text())
            if not content:
                continue
            if field == "price":
                result[field] = parse_price(content)
            elif field == "currency":
                result[field] = parse_currency(content)
            elif field == "customer_rating":
                result[field] = parse_rating(content)
            elif field == "customer_rating_count":
                try:
                    result[field] = int(float(content.replace(",", "")))
                except (ValueError, TypeError):
                    pass
            else:
                result[field] = clean_whitespace(content)

        title_tag = soup.find("title")
        if title_tag and not result.get("product_name"):
            result["product_name"] = clean_whitespace(title_tag.get_text())

        return result

    # ------------------------------------------------------------------
    # Visible HTML heuristics (last resort before AI)
    # ------------------------------------------------------------------
    def _extract_visible_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # --- Product name: try multiple heading patterns ---
        if not result.get("product_name"):
            for selector in [
                ("span", {"id": "productTitle"}),   # Amazon
                ("h1", {"class": re.compile(r"product.?title|product.?name|pdp.?title", re.I)}),
                ("h1", {}),
            ]:
                tag = soup.find(selector[0], selector[1])
                if tag:
                    name = clean_whitespace(tag.get_text())
                    if name and len(name) > 3:
                        result["product_name"] = name
                        break

        # --- Price: try various common patterns ---
        if not result.get("price"):
            price_candidates = []
            # 1. data-price attribute
            for tag in soup.find_all(attrs={"data-price": True}):
                p = parse_price(tag.get("data-price"))
                if p and p > 0:
                    price_candidates.append(p)
            # 2. class-based price tags (Amazon, Flipkart, etc.)
            price_class = re.compile(r"(price|amount|cost|offer.?price|selling.?price|final.?price)", re.IGNORECASE)
            for tag in soup.find_all(class_=price_class):
                text = clean_whitespace(tag.get_text())
                if text:
                    p = parse_price(text)
                    if p and p > 10:  # Ignore tiny values like ratings
                        price_candidates.append(p)
                        if not result.get("currency"):
                            result["currency"] = parse_currency(None, text)
                        break
            # 3. Amazon-specific
            amazon_price = soup.find("span", {"class": re.compile(r"a-price-whole", re.I)})
            if amazon_price:
                fraction = soup.find("span", {"class": re.compile(r"a-price-fraction", re.I)})
                whole = clean_whitespace(amazon_price.get_text())
                frac = clean_whitespace(fraction.get_text()) if fraction else "0"
                if whole:
                    try:
                        price_candidates.append(float(f"{whole.replace(',','')}.{frac.replace(',','')}"))
                        result["currency"] = "INR"
                    except ValueError:
                        pass
            if price_candidates:
                result["price"] = min(price_candidates)  # Take the lowest (sale price)

        # --- Customer rating from visible star elements ---
        if not result.get("customer_rating"):
            for attr in ["data-rating", "data-score", "data-average"]:
                for tag in soup.find_all(attrs={attr: True}):
                    r = parse_rating(tag.get(attr))
                    if r and 0 < r <= 5:
                        result["customer_rating"] = r
                        break
                if result.get("customer_rating"):
                    break

            # Try text patterns like "4.3 out of 5" or "4.3/5"
            if not result.get("customer_rating"):
                rating_class = re.compile(r"(rating|review.?score|star.?rating|average.?rating)", re.I)
                for tag in soup.find_all(class_=rating_class):
                    text = clean_whitespace(tag.get_text())
                    if text:
                        r = parse_rating(text)
                        if r and 0 < r <= 5:
                            result["customer_rating"] = r
                            break

        # --- Review count ---
        if not result.get("customer_rating_count"):
            count_class = re.compile(r"(review.?count|rating.?count|num.?ratings?|total.?review)", re.I)
            for tag in soup.find_all(class_=count_class):
                text = clean_whitespace(tag.get_text())
                if text:
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        try:
                            result["customer_rating_count"] = int(nums[0].replace(",", ""))
                            break
                        except ValueError:
                            pass

        # --- Seller name from common patterns ---
        if not result.get("seller_name"):
            seller_tag = soup.find(
                attrs={"class": re.compile(r"seller|sold.?by|merchant", re.I)}
            )
            if seller_tag:
                result["seller_name"] = clean_whitespace(seller_tag.get_text())

        # --- Image ---
        if not result.get("image"):
            # Try product-specific images first
            for img in soup.find_all("img"):
                src = safe_str(img.get("src")) or safe_str(img.get("data-src")) or safe_str(img.get("data-lazy-src"))
                if src and not src.startswith("data:") and len(src) > 10:
                    result["image"] = src
                    break

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _first(value: Any) -> Optional[str]:
        if isinstance(value, list):
            return safe_str(value[0]) if value else None
        return safe_str(value)

    @staticmethod
    def _simplify_condition(value: str) -> str:
        lowered = value.lower()
        if "refurb" in lowered:
            return "refurbished"
        if "used" in lowered:
            return "used"
        if "new" in lowered:
            return "new"
        return clean_whitespace(value) or "unknown"

    @staticmethod
    def _truncate(html: str, limit: int = 60000) -> str:
        return html[:limit]

    @staticmethod
    def _looks_js_blocked(soup: BeautifulSoup, data: Dict[str, Any]) -> bool:
        text = soup.get_text(" ", strip=True).lower()[:3000]
        if any(marker in text for marker in JS_BLOCKED_MARKERS):
            return True
        return not data.get("product_name") and not data.get("price")
