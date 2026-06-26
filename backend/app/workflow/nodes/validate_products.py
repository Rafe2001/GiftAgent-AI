"""
Node 6: Product Validation
Filters search results by budget, country, appropriateness, and quality.
Uses LLM to assess professional appropriateness of borderline products.
"""

import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

# Domains/patterns that are clearly not product pages
NON_PRODUCT_PATTERNS = [
    "wikipedia.org", "youtube.com", "reddit.com", "quora.com",
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "medium.com", "blog", "news", "article",
]


async def validate_products(state: WorkflowState) -> dict:
    """
    Filter and validate product candidates:
    1. Remove non-product URLs (articles, social media, etc.)
    2. Filter by budget range
    3. LLM checks professional appropriateness
    4. Track retry count for the retry loop
    """
    contact = state.get("contact", {})
    gift = contact.get("gift_context", {})
    raw_results = state.get("raw_search_results", [])

    budget_min = gift.get("budget_min", 0)
    budget_max = gift.get("budget_max", 5000)
    currency = gift.get("currency", "INR")

    logger.info("Validating %d product candidates", len(raw_results))

    # Step 1: Remove clearly non-product URLs
    product_results = []
    for r in raw_results:
        url = r.get("url", "").lower()
        if any(pattern in url for pattern in NON_PRODUCT_PATTERNS):
            logger.debug("Filtered non-product URL: %s", url)
            continue
        product_results.append(r)

    logger.info("After URL filtering: %d products", len(product_results))

    # Step 2: Filter by price if we have price data
    budget_filtered = []
    no_price = []
    for r in product_results:
        price = r.get("price_numeric", 0)
        if price > 0:
            # Apply currency conversion heuristic for USD/INR mismatch
            if currency == "INR" and price < 200:
                # Likely USD price — rough conversion
                price = price * 85
                r["price_numeric"] = price
                r["price"] = f"~₹{int(price)}"

            if budget_min <= price <= budget_max * 1.15:  # 15% tolerance
                budget_filtered.append(r)
            else:
                logger.debug("Filtered by price: %s (%.0f not in %.0f-%.0f)",
                             r.get("title", ""), price, budget_min, budget_max)
        else:
            # No price extracted — keep it (LLM will assess)
            no_price.append(r)

    # Combine: products with valid price + products without price
    validated = budget_filtered + no_price[:5]  # Cap no-price items

    logger.info("After budget filtering: %d products (%d had price, %d without)",
                len(validated), len(budget_filtered), len(no_price[:5]))

    # Step 3: If we have enough products, do a quick LLM appropriateness check
    if validated and len(validated) > 2:
        try:
            validated = await _check_appropriateness(validated, contact)
        except Exception as e:
            logger.warning("Appropriateness check failed: %s — keeping all products", str(e))

    # Track validation result for retry logic
    retry_count = state.get("_retry_count", 0)

    if len(validated) < 2 and retry_count < 2:
        # Not enough products — signal for retry
        logger.warning("Only %d valid products — will retry search", len(validated))
        return {
            "validated_products": validated,
            "_validation_failed": True,
            "_retry_count": retry_count + 1,
            "current_step": "validate_products",
        }

    return {
        "validated_products": validated,
        "_validation_failed": False,
        "current_step": "validate_products",
    }


async def _check_appropriateness(products: list, contact: dict) -> list:
    """Quick LLM check to filter out inappropriate products."""
    rel = contact.get("relationship_context", {})
    product_list = "\n".join(
        f"- [{i}] {p.get('title', 'Unknown')} ({p.get('store', 'Unknown store')}): {p.get('snippet', '')[:100]}"
        for i, p in enumerate(products)
    )

    prompt = f"""Review these products for professional gift appropriateness.
Relationship type: {rel.get('relationship_type', 'professional')}

Products:
{product_list}

Return JSON with indices of APPROPRIATE products only:
{{"appropriate_indices": [0, 1, 2, ...]}}

Remove products that are:
- Clearly not gifts (tools, services, software subscriptions)
- Inappropriate for professional relationships
- Too personal or intimate
- Joke/gag gifts

Return ONLY valid JSON."""

    result = await llm_service.call_llm(
        prompt=prompt,
        system_prompt="You are a professional gift appropriateness reviewer. Be conservative.",
        json_mode=True,
    )

    appropriate_idx = result.get("appropriate_indices", list(range(len(products))))
    filtered = [products[i] for i in appropriate_idx if i < len(products)]

    logger.info("Appropriateness check: %d/%d products passed", len(filtered), len(products))
    return filtered if filtered else products  # Don't filter everything out
