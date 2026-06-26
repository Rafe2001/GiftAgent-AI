"""
API Routes — All FastAPI endpoints for the gift recommendation system.
Handles contact upload, recommendation generation, status tracking, and human review.
"""

import uuid
import logging
import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.contact import ContactUploadRequest
from app.models.recommendation import (
    ContactRecommendation,
    RecommendationListResponse,
    ReviewAction,
    ReviewStatus,
)
from app.workflow.graph import recommendation_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory store for recommendations (keyed by contact_id)
recommendations_store: Dict[str, dict] = {}
# In-memory store for uploaded contacts
contacts_store: Dict[str, dict] = {}


# ─── Contact Upload ──────────────────────────────────────────────

@router.post("/contacts/upload")
async def upload_contacts(request: ContactUploadRequest):
    """Upload one or more contacts for recommendation generation."""
    uploaded = []
    for contact in request.contacts:
        contact_id = str(uuid.uuid4())[:8]
        contacts_store[contact_id] = contact.model_dump()
        uploaded.append({
            "contact_id": contact_id,
            "name": contact.name,
            "status": "uploaded",
        })
        logger.info("Uploaded contact: %s (id: %s)", contact.name, contact_id)

    return {
        "message": f"Uploaded {len(uploaded)} contacts",
        "contacts": uploaded,
    }


# ─── Recommendation Generation ───────────────────────────────────

async def _run_workflow(contact_id: str, contact_data: dict):
    """Run the LangGraph workflow for a single contact (background task)."""
    try:
        # Set initial status
        recommendations_store[contact_id] = {
            "contact_id": contact_id,
            "contact_name": contact_data.get("name", ""),
            "workflow_status": "processing",
            "current_step": "starting",
            "profile_signals": {},
            "search_trace": {},
            "recommended_gifts": [],
            "human_review": {"status": "pending_review", "available_actions": []},
            "errors": [],
        }

        # Prepare initial state for the graph
        initial_state = {
            "contact": contact_data,
            "contact_id": contact_id,
            "errors": [],
        }

        logger.info("Starting workflow for contact: %s (id: %s)",
                     contact_data.get("name", ""), contact_id)

        # Run the graph
        result = await recommendation_graph.ainvoke(initial_state)

        # Store the final result
        recommendations_store[contact_id] = {
            "contact_id": result.get("contact_id", contact_id),
            "contact_name": result.get("contact_name", contact_data.get("name", "")),
            "profile_signals": result.get("profile_signals", {}),
            "search_trace": result.get("search_trace", {}),
            "recommended_gifts": result.get("recommended_gifts", []),
            "human_review": result.get("human_review", {
                "status": "pending_review",
                "available_actions": ["approve", "reject", "edit", "regenerate"],
            }),
            "workflow_status": result.get("workflow_status", "completed"),
            "current_step": result.get("current_step", "finalized"),
            "errors": result.get("errors", []),
        }

        logger.info("Workflow completed for: %s", contact_data.get("name", ""))

    except Exception as e:
        logger.error("Workflow failed for contact %s: %s", contact_id, str(e))
        recommendations_store[contact_id] = {
            "contact_id": contact_id,
            "contact_name": contact_data.get("name", ""),
            "workflow_status": "failed",
            "current_step": "error",
            "error": str(e),
            "errors": [str(e)],
            "profile_signals": {},
            "search_trace": {},
            "recommended_gifts": [],
            "human_review": {
                "status": "pending_review",
                "available_actions": ["regenerate"],
            },
        }


@router.post("/recommendations/generate")
async def generate_recommendations(background_tasks: BackgroundTasks):
    """
    Trigger recommendation generation for all uploaded contacts.
    Runs workflows in background and returns job tracking info.
    """
    if not contacts_store:
        raise HTTPException(status_code=400, detail="No contacts uploaded. Upload contacts first.")

    jobs = []
    for contact_id, contact_data in contacts_store.items():
        # Skip if already processed
        if contact_id in recommendations_store and \
           recommendations_store[contact_id].get("workflow_status") in ("completed", "processing"):
            jobs.append({
                "contact_id": contact_id,
                "name": contact_data.get("name", ""),
                "status": recommendations_store[contact_id].get("workflow_status"),
            })
            continue

        background_tasks.add_task(_run_workflow, contact_id, contact_data)
        jobs.append({
            "contact_id": contact_id,
            "name": contact_data.get("name", ""),
            "status": "processing",
        })

    return {
        "message": f"Processing {len(jobs)} contacts",
        "jobs": jobs,
    }


@router.post("/recommendations/generate/{contact_id}")
async def generate_single_recommendation(contact_id: str, background_tasks: BackgroundTasks):
    """Trigger recommendation generation for a single contact."""
    if contact_id not in contacts_store:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_data = contacts_store[contact_id]
    background_tasks.add_task(_run_workflow, contact_id, contact_data)

    return {
        "message": f"Processing contact: {contact_data.get('name', '')}",
        "contact_id": contact_id,
        "status": "processing",
    }


# ─── Recommendation Retrieval ────────────────────────────────────

@router.get("/recommendations")
async def list_recommendations():
    """List all recommendations with their current status."""
    recs = list(recommendations_store.values())
    return RecommendationListResponse(
        recommendations=[ContactRecommendation(**r) for r in recs],
        total=len(recs),
    )


@router.get("/recommendations/{contact_id}")
async def get_recommendation(contact_id: str):
    """Get the full recommendation for a specific contact."""
    if contact_id not in recommendations_store:
        # Check if it's in contacts but not yet processed
        if contact_id in contacts_store:
            return {
                "contact_id": contact_id,
                "contact_name": contacts_store[contact_id].get("name", ""),
                "workflow_status": "pending",
                "message": "Recommendations not yet generated. Call POST /api/recommendations/generate first.",
            }
        raise HTTPException(status_code=404, detail="Contact not found")

    return recommendations_store[contact_id]


# ─── Human Review ────────────────────────────────────────────────

@router.post("/recommendations/{contact_id}/review")
async def review_recommendation(
    contact_id: str,
    review: ReviewAction,
    background_tasks: BackgroundTasks,
):
    """
    Human review action on a contact's recommendations.
    Actions: approve, reject, edit, regenerate
    """
    if contact_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec = recommendations_store[contact_id]

    if review.action == "approve":
        rec["human_review"] = {
            "status": ReviewStatus.APPROVED.value,
            "available_actions": ["reject", "regenerate"],
            "reviewer_notes": review.notes or "",
        }
        rec["workflow_status"] = "approved"
        logger.info("Recommendation approved for: %s", rec.get("contact_name", ""))

    elif review.action == "reject":
        rec["human_review"] = {
            "status": ReviewStatus.REJECTED.value,
            "available_actions": ["regenerate"],
            "reviewer_notes": review.notes or "",
        }
        rec["workflow_status"] = "rejected"
        logger.info("Recommendation rejected for: %s", rec.get("contact_name", ""))

    elif review.action == "edit":
        if review.edited_gifts:
            rec["recommended_gifts"] = [g.model_dump() for g in review.edited_gifts]
        rec["human_review"] = {
            "status": ReviewStatus.EDITED.value,
            "available_actions": ["approve", "reject", "regenerate"],
            "reviewer_notes": review.notes or "",
        }
        rec["workflow_status"] = "edited"
        logger.info("Recommendation edited for: %s", rec.get("contact_name", ""))

    elif review.action == "regenerate":
        rec["human_review"] = {
            "status": ReviewStatus.REGENERATING.value,
            "available_actions": [],
        }
        rec["workflow_status"] = "processing"
        # Re-run the workflow
        if contact_id in contacts_store:
            background_tasks.add_task(_run_workflow, contact_id, contacts_store[contact_id])
        logger.info("Regenerating recommendations for: %s", rec.get("contact_name", ""))

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {review.action}")

    recommendations_store[contact_id] = rec
    return rec


# ─── Contacts Management ─────────────────────────────────────────

@router.get("/contacts")
async def list_contacts():
    """List all uploaded contacts."""
    result = []
    for cid, data in contacts_store.items():
        status = "uploaded"
        if cid in recommendations_store:
            status = recommendations_store[cid].get("workflow_status", "unknown")
        result.append({
            "contact_id": cid,
            "name": data.get("name", ""),
            "role": data.get("role", ""),
            "company": data.get("company", ""),
            "location": data.get("location", ""),
            "status": status,
        })
    return {"contacts": result, "total": len(result)}
