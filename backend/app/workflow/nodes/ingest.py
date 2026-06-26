"""
Node 1: Contact Ingestion
Validates and normalises the contact data into the workflow state.
"""

import logging
from app.models.state import WorkflowState

logger = logging.getLogger(__name__)


async def ingest_contact(state: WorkflowState) -> dict:
    """
    Parse and validate the raw contact data.
    Extracts key fields into the workflow state for downstream nodes.
    """
    contact = state.get("contact", {})

    if not contact:
        return {
            "errors": ["No contact data provided"],
            "workflow_status": "failed",
            "current_step": "ingest",
        }

    name = contact.get("name", "")
    if not name:
        return {
            "errors": ["Contact name is required"],
            "workflow_status": "failed",
            "current_step": "ingest",
        }

    logger.info("Ingesting contact: %s", name)

    return {
        "current_step": "ingest",
        "workflow_status": "processing",
        "errors": [],
    }
