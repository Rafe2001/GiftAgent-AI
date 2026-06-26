"""
Node 3: Signal Filtering (Guardrails)
Second LLM pass to remove any sensitive, inappropriate, or unsupported signals.
"""

import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service
from app.workflow.prompts import SIGNAL_FILTER_SYSTEM, SIGNAL_FILTER_PROMPT

logger = logging.getLogger(__name__)


async def filter_signals(state: WorkflowState) -> dict:
    """
    Safety review pass — ensures signals don't contain sensitive attributes.
    Removes signals based on religion, politics, health, ethnicity, gender, family.
    """
    contact = state.get("contact", {})
    rel = contact.get("relationship_context", {})

    strong = state.get("strong_signals", [])
    weak = state.get("weak_signals", [])
    avoid = state.get("signals_to_avoid", [])

    # If no signals were extracted, pass through
    if not strong and not weak:
        logger.warning("No signals to filter for: %s", contact.get("name", ""))
        return {
            "current_step": "filter_signals",
        }

    prompt = SIGNAL_FILTER_PROMPT.format(
        strong_signals="\n".join(f"- {s}" for s in strong),
        weak_signals="\n".join(f"- {s}" for s in weak),
        signals_to_avoid="\n".join(f"- {s}" for s in avoid),
        relationship_type=rel.get("relationship_type", "professional contact"),
    )

    logger.info("Filtering signals for: %s", contact.get("name", ""))

    try:
        result = await llm_service.call_llm(
            prompt=prompt,
            system_prompt=SIGNAL_FILTER_SYSTEM,
            json_mode=True,
        )

        filtered_strong = result.get("strong_signals", strong)
        filtered_weak = result.get("weak_signals", weak)
        filtered_avoid = result.get("signals_to_avoid", avoid)
        removed = result.get("removed_signals", [])

        if removed:
            logger.info("Removed %d signals during filtering: %s", len(removed), removed)

        return {
            "strong_signals": filtered_strong,
            "weak_signals": filtered_weak,
            "signals_to_avoid": filtered_avoid,
            "current_step": "filter_signals",
        }

    except Exception as e:
        logger.error("Signal filtering failed: %s — keeping original signals", str(e))
        # On filter failure, keep original signals but log the error
        return {
            "errors": state.get("errors", []) + [f"Signal filter error: {str(e)}"],
            "current_step": "filter_signals",
        }
