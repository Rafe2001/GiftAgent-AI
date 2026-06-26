"""
Search Service — uses LangChain's TavilySearch (primary) and DuckDuckGo (fallback).
Finds real purchasable products from the web.
"""

import re
import logging
from typing import List

from langchain_tavily import TavilySearch

from app.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """
    Product search using Tavily (via LangChain, primary) with DuckDuckGo fallback.
    Extracts product information including price from search results.
    """

    def __init__(self):
        self._tavily = None
        if settings.TAVILY_API_KEY:
            self._tavily = TavilySearch(
                max_results=5,
                search_depth="advanced",
                include_domains=["amazon.in", "flipkart.com", "amazon.com", "myntra.com",
                                 "igp.com", "fnp.com", "nykaa.com", "croma.com", "etsy.com"],
            )
            logger.info("Tavily search initialized via LangChain")

    async def search_products(
        self,
        query: str,
        country: str = "India",
        max_results: int = 5,
    ) -> List[dict]:
        """
        Search for real products matching the query.

        Returns list of dicts with: title, url, price, snippet, store, source_query
        """
        results = []

        # Try Tavily first
        if self._tavily:
            try:
                results = await self._search_tavily(query)
                if results:
                    logger.info("Tavily returned %d results for: %s", len(results), query)
                    return self._enrich_results(results, query)
            except Exception as e:
                logger.warning("Tavily search failed: %s. Falling back to DuckDuckGo.", str(e))

        # Fallback to DuckDuckGo
        try:
            results = await self._search_duckduckgo(query, max_results)
            logger.info("DuckDuckGo returned %d results for: %s", len(results), query)
        except Exception as e:
            logger.error("DuckDuckGo search also failed: %s", str(e))

        return self._enrich_results(results, query)

    async def _search_tavily(self, query: str) -> List[dict]:
        """Search using Tavily via LangChain."""
        response = await self._tavily.ainvoke({"query": query})

        # TavilySearch returns a list of result dicts or a string
        if isinstance(response, str):
            # Sometimes returns a plain string summary
            return []

        if isinstance(response, dict) and "results" in response:
            items = response["results"]
        elif isinstance(response, list):
            items = response
        else:
            items = [response]

        results = []
        for r in items:
            if isinstance(r, dict):
                results.append({
                    "title": r.get("title", r.get("content", "")[:80]),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "store": self._extract_store(r.get("url", "")),
                })

        return results

    async def _search_duckduckgo(self, query: str, max_results: int) -> List[dict]:
        """Search using DuckDuckGo (no API key needed)."""
        import asyncio

        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.error("duckduckgo-search not installed — DDG fallback unavailable")
            return []

        def _sync_search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "store": self._extract_store(r.get("href", "")),
                    }
                    for r in results
                ]

        return await asyncio.get_event_loop().run_in_executor(None, _sync_search)

    def _enrich_results(self, results: List[dict], query: str) -> List[dict]:
        """Add price extraction and source query to results."""
        enriched = []
        for r in results:
            r["source_query"] = query
            r["price"] = self._extract_price(r.get("title", "") + " " + r.get("snippet", ""))
            r["price_numeric"] = self._parse_price_numeric(r.get("price", ""))
            enriched.append(r)
        return enriched

    def _extract_store(self, url: str) -> str:
        """Extract the store name from a URL."""
        url_lower = url.lower()
        store_map = {
            "amazon.in": "Amazon India",
            "amazon.com": "Amazon",
            "flipkart.com": "Flipkart",
            "myntra.com": "Myntra",
            "igp.com": "IGP",
            "fnp.com": "Ferns N Petals",
            "nykaa.com": "Nykaa",
            "tatacliq.com": "Tata CLiQ",
            "ajio.com": "AJIO",
            "croma.com": "Croma",
            "meesho.com": "Meesho",
            "etsy.com": "Etsy",
            "ebay.com": "eBay",
        }
        for domain, name in store_map.items():
            if domain in url_lower:
                return name
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            store = hostname.replace("www.", "").split(".")[0].title()
            return store
        except Exception:
            return "Online Store"

    def _extract_price(self, text: str) -> str:
        """Extract price from text using regex patterns."""
        patterns = [
            r'₹\s*[\d,]+(?:\.\d{2})?',
            r'Rs\.?\s*[\d,]+(?:\.\d{2})?',
            r'INR\s*[\d,]+(?:\.\d{2})?',
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'USD\s*[\d,]+(?:\.\d{2})?',
            r'(?:Price|MRP|Cost)[\s:]*₹?\$?\s*[\d,]+(?:\.\d{2})?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return ""

    def _parse_price_numeric(self, price_str: str) -> float:
        """Convert a price string to a numeric value."""
        if not price_str:
            return 0.0
        cleaned = re.sub(r'[₹$,\s]', '', price_str)
        cleaned = re.sub(r'^(Rs\.?|INR|USD|Price|MRP|Cost)[\s:]*', '', cleaned, flags=re.IGNORECASE)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


# Singleton instance
search_service = SearchService()
