"""
Node 7: Gift Ranking
Uses LLM to rank validated products and select the top 3 gifts
with full reasoning, confidence scores, and assumptions.
"""

import json
import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service
from app.workflow.prompts import GIFT_RANKING_SYSTEM, GIFT_RANKING_PROMPT

logger = logging.getLogger(__name__)


async def rank_gifts(state: WorkflowState) -> dict:
    """
    Send validated products + profile signals to LLM for ranking.
    Returns top 3 gifts with detailed reasoning.
    """
    contact = state.get("contact", {})
    gift = contact.get("gift_context", {})
    rel = contact.get("relationship_context", {})
    validated = state.get("validated_products", [])

    if not validated:
        logger.error("No validated products to rank")
        return {
            "ranked_gifts": [],
            "errors": state.get("errors", []) + ["No products available for ranking"],
            "current_step": "rank_gifts",
        }

    # Format products for the prompt
    product_lines = []
    for i, p in enumerate(validated):
        price_str = p.get("price", "Price unknown")
        product_lines.append(
            f"[{i + 1}] {p.get('title', 'Unknown Product')}\n"
            f"    Store: {p.get('store', 'Unknown')}\n"
            f"    Price: {price_str}\n"
            f"    URL: {p.get('url', 'N/A')}\n"
            f"    Description: {p.get('snippet', 'No description')[:200]}"
        )

    prompt = GIFT_RANKING_PROMPT.format(
        name=contact.get("name", ""),
        role=contact.get("role", ""),
        company=contact.get("company", ""),
        location=contact.get("location", ""),
        strong_signals=", ".join(state.get("strong_signals", [])),
        weak_signals=", ".join(state.get("weak_signals", [])),
        occasion=gift.get("occasion", ""),
        relationship_type=rel.get("relationship_type", ""),
        business_goal=rel.get("business_goal", ""),
        budget_min=gift.get("budget_min", 0),
        budget_max=gift.get("budget_max", 5000),
        currency=gift.get("currency", "INR"),
        products="\n\n".join(product_lines),
    )

    logger.info("Ranking %d products for: %s", len(validated), contact.get("name", ""))

    try:
        result = await llm_service.call_llm(
            prompt=prompt,
            system_prompt=GIFT_RANKING_SYSTEM,
            json_mode=True,
        )

        ranked = result.get("ranked_gifts", [])

        if not ranked:
            raise ValueError("LLM returned empty ranked_gifts")

        # Ensure ranks are sequential
        for i, g in enumerate(ranked):
            g["rank"] = i + 1

        # Ensure we have at most 3
        ranked = ranked[:3]

        logger.info("Ranked top %d gifts:", len(ranked))
        for g in ranked:
            logger.info("  #%d: %s (confidence: %.2f, risk: %s)",
                        g.get("rank"), g.get("gift_name"), 
                        g.get("confidence_score", 0), g.get("risk_level", "unknown"))

        return {
            "ranked_gifts": ranked,
            "current_step": "rank_gifts",
        }

    except Exception as e:
        logger.error("Gift ranking failed: %s", str(e))

        # Fallback: return first 3 products unranked
        fallback = []
        for i, p in enumerate(validated[:3]):
            fallback.append({
                "rank": i + 1,
                "gift_name": p.get("title", "Unknown Product"),
                "product_url": p.get("url", ""),
                "store": p.get("store", ""),
                "estimated_price": p.get("price", "Unknown"),
                "why_this_gift": "Automatic selection — ranking LLM failed",
                "personalisation_reasoning": "Based on search results matching profile signals",
                "confidence_score": 0.3,
                "risk_level": "medium",
                "assumptions": ["LLM ranking failed — products selected by search relevance only"],
            })

        return {
            "ranked_gifts": fallback,
            "errors": state.get("errors", []) + [f"Ranking error: {str(e)}"],
            "current_step": "rank_gifts",
        }
