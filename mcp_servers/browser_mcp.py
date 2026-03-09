"""
Browser MCP Server
──────────────────
Model Context Protocol tool for web browsing, scraping, and research.

Production: Uses Playwright or Selenium.
Demo mode: Returns stub results.

Install: pip install playwright && playwright install chromium
"""

import os
from typing import Optional

from utils.logger import get_logger

log = get_logger("mcp.browser")

DEMO_MODE = os.getenv("BROWSER_DEMO", "true").lower() == "true"


# ── Public MCP Tool Functions ─────────────────────────────────────────────────

def fetch_page(url: str) -> dict:
    """
    Fetch a web page and return its text content.

    Args:
        url: The URL to fetch

    Returns:
        {"success": bool, "url": str, "title": str, "content": str}
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would fetch URL: {url}")
        return {
            "success": True,
            "url": url,
            "title": "Demo Page Title",
            "content": f"[DEMO] Simulated content from {url}",
        }

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            title = page.title()
            content = page.inner_text("body")
            browser.close()
        log.info(f"Fetched page: {url} — {len(content)} chars")
        return {"success": True, "url": url, "title": title, "content": content[:5000]}
    except Exception as e:
        log.error(f"Browser fetch failed for {url}: {e}")
        return {"success": False, "url": url, "title": "", "content": str(e)}


def search_web(query: str, num_results: int = 5) -> list[dict]:
    """
    Search the web and return top results.

    Args:
        query: Search query string
        num_results: Max results to return

    Returns:
        List of {"title": str, "url": str, "snippet": str}
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would search: {query}")
        return [
            {
                "title": f"Demo result for: {query}",
                "url": "https://example.com/result",
                "snippet": f"This is a simulated search result for query: {query}",
            }
        ]

    try:
        from playwright.sync_api import sync_playwright
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(search_url, timeout=15000)
            page.wait_for_selector(".result", timeout=5000)
            items = page.query_selector_all(".result")[:num_results]
            for item in items:
                title_el = item.query_selector(".result__title")
                url_el   = item.query_selector(".result__url")
                snip_el  = item.query_selector(".result__snippet")
                results.append({
                    "title":   title_el.inner_text() if title_el else "",
                    "url":     url_el.inner_text() if url_el else "",
                    "snippet": snip_el.inner_text() if snip_el else "",
                })
            browser.close()
        return results
    except Exception as e:
        log.error(f"Web search failed: {e}")
        return []


def take_screenshot(url: str, output_path: str = "screenshot.png") -> dict:
    """
    Take a screenshot of a URL.

    Returns:
        {"success": bool, "path": str}
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would screenshot: {url}")
        return {"success": True, "path": f"[DEMO] {output_path}"}

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        log.info(f"Screenshot saved: {output_path}")
        return {"success": True, "path": output_path}
    except Exception as e:
        log.error(f"Screenshot failed: {e}")
        return {"success": False, "path": str(e)}
