"""
Node 8: Personalised Message Generation
Generates a short, warm, professional gift note for each recommended gift.
"""

import logging
from app.models.state import WorkflowState
from app.services.llm import llm_service
from app.workflow.prompts import MESSAGE_GENERATION_SYSTEM, MESSAGE_GENERATION_PROMPT

logger = logging.getLogger(__name__)


async def generate_messages(state: WorkflowState) -> dict:
    """
    For each ranked gift, generate a personalised message to send with it.
    Messages are specific (not generic) — they reference the recipient and occasion.
    """
    contact = state.get("contact", {})
    gift_ctx = contact.get("gift_context", {})
    rel = contact.get("relationship_context", {})
    ranked = state.get("ranked_gifts", [])

    if not ranked:
        logger.warning("No ranked gifts — skipping message generation")
        return {
            "gifts_with_messages": [],
            "current_step": "generate_messages",
        }

    # Format gifts for the prompt
    gifts_text = ""
    for g in ranked:
        gifts_text += (
            f"Gift #{g.get('rank', '?')}: {g.get('gift_name', 'Unknown')}\n"
            f"  Why: {g.get('why_this_gift', '')}\n"
            f"  Personalisation: {g.get('personalisation_reasoning', '')}\n\n"
        )

    signals = state.get("strong_signals", []) + state.get("weak_signals", [])

    prompt = MESSAGE_GENERATION_PROMPT.format(
        name=contact.get("name", ""),
        role=contact.get("role", ""),
        company=contact.get("company", ""),
        occasion=gift_ctx.get("occasion", ""),
        relationship_type=rel.get("relationship_type", ""),
        last_interaction=rel.get("last_interaction", ""),
        business_goal=rel.get("business_goal", ""),
        gifts=gifts_text,
        signals=", ".join(signals),
    )

    logger.info("Generating personalised messages for %d gifts", len(ranked))

    try:
        result = await llm_service.call_llm(
            prompt=prompt,
            system_prompt=MESSAGE_GENERATION_SYSTEM,
            json_mode=True,
        )

        messages = result.get("messages", [])

        # Merge messages into the ranked gifts
        gifts_with_messages = []
        for gift in ranked:
            gift_copy = dict(gift)
            # Find matching message by rank
            matching = [m for m in messages if m.get("rank") == gift.get("rank")]
            if matching:
                gift_copy["personalised_message"] = matching[0].get("personalised_message", "")
            elif not gift_copy.get("personalised_message"):
                gift_copy["personalised_message"] = (
                    f"Hi {contact.get('name', '').split()[0] if contact.get('name') else 'there'}, "
                    f"thank you for your time. Wishing you all the best!"
                )
            gifts_with_messages.append(gift_copy)

        logger.info("Generated messages for %d gifts", len(gifts_with_messages))

        return {
            "gifts_with_messages": gifts_with_messages,
            "current_step": "generate_messages",
        }

    except Exception as e:
        logger.error("Message generation failed: %s", str(e))
        # Fallback: use a generic message
        name_first = contact.get("name", "").split()[0] if contact.get("name") else "there"
        gifts_with_messages = []
        for gift in ranked:
            gift_copy = dict(gift)
            if not gift_copy.get("personalised_message"):
                gift_copy["personalised_message"] = (
                    f"Hi {name_first}, it was great connecting with you. "
                    f"I thought you might enjoy this — hope it brings a smile!"
                )
            gifts_with_messages.append(gift_copy)

        return {
            "gifts_with_messages": gifts_with_messages,
            "errors": state.get("errors", []) + [f"Message generation error: {str(e)}"],
            "current_step": "generate_messages",
        }
