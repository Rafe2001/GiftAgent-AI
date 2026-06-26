"""
Node 4: Generate Search Queries
Uses LLM to convert filtered signals into optimised product search queries.
This is a dedicated step (not just template-based) so the LLM can craft
context-aware queries that produce better e-commerce results.
"""

import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service
from app.workflow.prompts import QUERY_GENERATION_SYSTEM, QUERY_GENERATION_PROMPT

logger = logging.getLogger(__name__)


async def generate_search_queries(state: WorkflowState) -> dict:
    """
    LLM generates 3-4 specific product search queries based on filtered signals.
    Each query targets a different angle/signal to maximise product diversity.
    """
    contact = state.get("contact", {})
    gift = contact.get("gift_context", {})
    rel = contact.get("relationship_context", {})

    strong = state.get("strong_signals", [])
    weak = state.get("weak_signals", [])

    # If no signals at all, generate generic queries
    if not strong and not weak:
        logger.warning("No signals available — generating generic queries")
        country = gift.get("country", "India")
        currency = gift.get("currency", "INR")
        budget_max = gift.get("budget_max", 5000)
        occasion = gift.get("occasion", "business gift")

        generic_queries = [
            f"premium corporate gift {country} under {currency} {int(budget_max)}",
            f"{occasion} professional gift buy online {country}",
            f"elegant business gift for executive {country} under {currency} {int(budget_max)}",
        ]
        return {
            "search_queries": generic_queries,
            "current_step": "generate_queries",
        }

    prompt = QUERY_GENERATION_PROMPT.format(
        name=contact.get("name", ""),
        role=contact.get("role", ""),
        location=contact.get("location", ""),
        strong_signals=", ".join(strong),
        weak_signals=", ".join(weak),
        occasion=gift.get("occasion", ""),
        relationship_type=rel.get("relationship_type", ""),
        budget_min=gift.get("budget_min", 0),
        budget_max=gift.get("budget_max", 5000),
        currency=gift.get("currency", "INR"),
        country=gift.get("country", "India"),
    )

    logger.info("Generating search queries for: %s", contact.get("name", ""))

    try:
        result = await llm_service.call_llm(
            prompt=prompt,
            system_prompt=QUERY_GENERATION_SYSTEM,
            json_mode=True,
        )

        queries = result.get("queries", [])
        reasoning = result.get("query_reasoning", [])

        if not queries:
            raise ValueError("LLM returned empty queries list")

        logger.info("Generated %d search queries: %s", len(queries), queries)
        for i, (q, r) in enumerate(zip(queries, reasoning)):
            logger.debug("  Query %d: %s (reason: %s)", i + 1, q, r)

        return {
            "search_queries": queries[:4],  # Cap at 4
            "current_step": "generate_queries",
        }

    except Exception as e:
        logger.error("Query generation failed: %s — using fallback queries", str(e))
        # Fallback to template-based queries
        country = gift.get("country", "India")
        currency = gift.get("currency", "INR")
        budget_max = gift.get("budget_max", 5000)
        budget_str = f"under {currency} {int(budget_max)}"

        fallback_queries = []
        if strong:
            fallback_queries.append(f"{strong[0]} gift {country} {budget_str} buy online")
        if len(strong) > 1:
            fallback_queries.append(f"premium {strong[1]} gift {country} {budget_str}")
        fallback_queries.append(
            f"corporate gift for professional {country} {budget_str}"
        )

        return {
            "search_queries": fallback_queries,
            "errors": state.get("errors", []) + [f"Query generation error: {str(e)}"],
            "current_step": "generate_queries",
        }
