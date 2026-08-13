"""PlaywrightExtractionService

A fallback HTML fetcher that uses a real headless Chromium browser via
Playwright. Runs in a separate worker thread to avoid conflicting with
FastAPI's running asyncio event loop.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

logger = logging.getLogger("ai_product_comparator.playwright")

_BROWSER_TIMEOUT_MS = 30_000   # 30 seconds page load timeout
_WAIT_AFTER_LOAD_MS = 2_500    # Let JS hydrate after initial load


class PlaywrightExtractionService:
    """Fetches rendered HTML using a headless Chromium browser in a separate thread."""

    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch the fully-rendered HTML of *url* using Chromium in a separate thread.

        Returns None if the fetch fails or times out.
        """
        q = queue.Queue()
        thread = threading.Thread(target=self._worker, args=(q, url))
        thread.start()
        thread.join(timeout=45.0)  # max wait 45 seconds

        if thread.is_alive():
            logger.warning("Playwright worker thread timed out for %s", url)
            return None

        try:
            status, res = q.get_nowait()
            if status == "OK":
                return res
            else:
                logger.warning("Playwright fetch error for %s: %s", url, res)
                return None
        except queue.Empty:
            return None

    def _worker(self, q: queue.Queue, url: str) -> None:
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )

                # Viewport and user-agent to mimic a real desktop browser
                context = browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                    ),
                    locale="en-IN",
                    timezone_id="Asia/Kolkata",
                    java_script_enabled=True,
                    extra_http_headers={
                        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
                        "Accept": (
                            "text/html,application/xhtml+xml,application/xml;"
                            "q=0.9,image/avif,image/webp,*/*;q=0.8"
                        ),
                    },
                )

                try:
                    from playwright_stealth import stealth_sync  # noqa: PLC0415
                    page = context.new_page()
                    stealth_sync(page)
                except ImportError:
                    page = context.new_page()

                page.goto(
                    url,
                    timeout=_BROWSER_TIMEOUT_MS,
                    wait_until="domcontentloaded",
                )

                # Wait for JS hydration
                page.wait_for_timeout(_WAIT_AFTER_LOAD_MS)

                # Scroll to load lazy elements
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                page.wait_for_timeout(500)

                html = page.content()
                browser.close()
                q.put(("OK", html))
        except Exception as exc:  # noqa: BLE001
            q.put(("ERR", str(exc)))

    def close(self) -> None:
        pass
