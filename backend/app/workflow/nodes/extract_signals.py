"""
Node 2: Signal Extraction
Uses LLM to extract gifting signals from the contact's profile data.
"""

import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service
from app.workflow.prompts import SIGNAL_EXTRACTION_SYSTEM, SIGNAL_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


async def extract_signals(state: WorkflowState) -> dict:
    """
    Send the contact's full profile to the LLM and extract:
    - strong_signals: well-supported interests/traits
    - weak_signals: possible but less certain interests
    - signals_to_avoid: sensitive areas to exclude
    """
    contact = state.get("contact", {})
    profile = contact.get("linkedin_profile", {})
    rel = contact.get("relationship_context", {})
    gift = contact.get("gift_context", {})

    # Format experience for the prompt
    experience_lines = []
    for exp in profile.get("experience", []):
        experience_lines.append(
            f"- {exp.get('title', '')} at {exp.get('company', '')}: {exp.get('description', '')}"
        )

    # Build the prompt with all available data
    prompt = SIGNAL_EXTRACTION_PROMPT.format(
        name=contact.get("name", ""),
        role=contact.get("role", ""),
        company=contact.get("company", ""),
        location=contact.get("location", ""),
        headline=profile.get("headline", ""),
        about=profile.get("about", ""),
        experience="\n".join(experience_lines) if experience_lines else "None provided",
        recent_posts="\n".join(f"- {p}" for p in profile.get("recent_posts", [])) or "None",
        recent_comments="\n".join(f"- {c}" for c in profile.get("recent_comments", [])) or "None",
        engaged_topics=", ".join(profile.get("engaged_topics", [])) or "None",
        relationship_type=rel.get("relationship_type", ""),
        last_interaction=rel.get("last_interaction", ""),
        business_goal=rel.get("business_goal", ""),
        occasion=gift.get("occasion", ""),
        budget_min=gift.get("budget_min", 0),
        budget_max=gift.get("budget_max", 5000),
        currency=gift.get("currency", "INR"),
        country=gift.get("country", "India"),
    )

    logger.info("Extracting signals for: %s", contact.get("name", ""))

    try:
        result = await llm_service.call_llm(
            prompt=prompt,
            system_prompt=SIGNAL_EXTRACTION_SYSTEM,
            json_mode=True,
        )

        strong = result.get("strong_signals", [])
        weak = result.get("weak_signals", [])
        avoid = result.get("signals_to_avoid", [])

        logger.info(
            "Extracted signals — strong: %d, weak: %d, avoid: %d",
            len(strong), len(weak), len(avoid),
        )

        return {
            "strong_signals": strong,
            "weak_signals": weak,
            "signals_to_avoid": avoid,
            "current_step": "extract_signals",
        }

    except Exception as e:
        logger.error("Signal extraction failed: %s", str(e))
        return {
            "strong_signals": [],
            "weak_signals": [],
            "signals_to_avoid": ["Extraction failed — using fallback"],
            "errors": state.get("errors", []) + [f"Signal extraction error: {str(e)}"],
            "current_step": "extract_signals",
        }
