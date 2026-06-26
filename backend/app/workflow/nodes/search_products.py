"""
Node 5: Product Search
Executes the LLM-generated search queries against Tavily and DuckDuckGo
to find real, purchasable products.
"""

import logging
from app.models.state import WorkflowState
from app.services.search import search_service

logger = logging.getLogger(__name__)


async def search_products(state: WorkflowState) -> dict:
    """
    Execute each search query and collect all product candidates.
    Aims for 8-15 total products across all queries for good ranking diversity.
    """
    contact = state.get("contact", {})
    gift = contact.get("gift_context", {})
    queries = state.get("search_queries", [])

    if not queries:
        logger.error("No search queries available")
        return {
            "raw_search_results": [],
            "errors": state.get("errors", []) + ["No search queries to execute"],
            "current_step": "search_products",
        }

    country = gift.get("country", "India")
    all_results = []
    seen_urls = set()

    logger.info("Searching products for: %s with %d queries", contact.get("name", ""), len(queries))

    for i, query in enumerate(queries):
        try:
            results = await search_service.search_products(
                query=query,
                country=country,
                max_results=5,
            )

            # Deduplicate by URL
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)

            logger.info("Query %d/%d: '%s' → %d results", i + 1, len(queries), query, len(results))

        except Exception as e:
            logger.warning("Search failed for query '%s': %s", query, str(e))

    logger.info("Total unique products found: %d", len(all_results))

    return {
        "raw_search_results": all_results,
        "current_step": "search_products",
    }
