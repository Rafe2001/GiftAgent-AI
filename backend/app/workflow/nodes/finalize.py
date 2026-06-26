"""
Node 9: Finalize Output
Assembles the final structured JSON response matching the assignment's expected output.
This is the terminal node that produces the clean API response.
"""

import logging
import uuid
from app.models.state import WorkflowState

logger = logging.getLogger(__name__)


async def finalize_output(state: WorkflowState) -> dict:
    """
    Assemble the final ContactRecommendation output from all intermediate state.
    Produces the structured response matching the assignment spec.
    """
    contact = state.get("contact", {})
    contact_id = state.get("contact_id", str(uuid.uuid4())[:8])

    # Build profile signals
    profile_signals = {
        "strong_signals": state.get("strong_signals", []),
        "weak_signals": state.get("weak_signals", []),
        "signals_to_avoid": state.get("signals_to_avoid", []),
    }

    # Build search trace
    search_trace = {
        "queries_used": state.get("search_queries", []),
        "products_considered_count": len(state.get("raw_search_results", [])),
    }

    # Build recommended gifts from gifts_with_messages
    recommended_gifts = []
    for g in state.get("gifts_with_messages", []):
        recommended_gifts.append({
            "rank": g.get("rank", 0),
            "gift_name": g.get("gift_name", ""),
            "product_url": g.get("product_url", ""),
            "store": g.get("store", ""),
            "estimated_price": g.get("estimated_price", ""),
            "why_this_gift": g.get("why_this_gift", ""),
            "personalisation_reasoning": g.get("personalisation_reasoning", ""),
            "personalised_message": g.get("personalised_message", ""),
            "confidence_score": g.get("confidence_score", 0.5),
            "risk_level": g.get("risk_level", "medium"),
            "assumptions": g.get("assumptions", []),
        })

    # Human review state
    human_review = {
        "status": "pending_review",
        "available_actions": ["approve", "reject", "edit", "regenerate"],
    }

    # Final assembled output
    final_output = {
        "contact_id": contact_id,
        "contact_name": contact.get("name", ""),
        "profile_signals": profile_signals,
        "search_trace": search_trace,
        "recommended_gifts": recommended_gifts,
        "human_review": human_review,
        "workflow_status": "completed" if recommended_gifts else "completed_with_issues",
        "current_step": "finalized",
        "errors": state.get("errors", []),
    }

    logger.info(
        "Finalized output for %s: %d gifts, status=%s",
        contact.get("name", ""),
        len(recommended_gifts),
        final_output["workflow_status"],
    )

    return final_output
