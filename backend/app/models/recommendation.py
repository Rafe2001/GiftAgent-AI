"""
Pydantic models for recommendation output data.
Matches the assignment's expected output schema exactly.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ProfileSignals(BaseModel):
    """Extracted and filtered signals from the contact's profile."""
    strong_signals: List[str] = Field(default_factory=list)
    weak_signals: List[str] = Field(default_factory=list)
    signals_to_avoid: List[str] = Field(
        default_factory=lambda: [
            "Do not infer religion, politics, health, family status, or other sensitive personal attributes"
        ]
    )


class SearchTrace(BaseModel):
    """Trace of product search queries and results for transparency."""
    queries_used: List[str] = Field(default_factory=list)
    products_considered_count: int = 0


class RecommendedGift(BaseModel):
    """A single gift recommendation with full reasoning and metadata."""
    rank: int
    gift_name: str
    product_url: str = ""
    store: str = ""
    estimated_price: str = ""
    why_this_gift: str = ""
    personalisation_reasoning: str = ""
    personalised_message: str = ""
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_level: str = "medium"  # low, medium, high
    assumptions: List[str] = Field(default_factory=list)


class ReviewStatus(str, Enum):
    """Status of human review for a recommendation set."""
    PENDING = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    REGENERATING = "regenerating"


class HumanReview(BaseModel):
    """Human review state for a contact's recommendations."""
    status: str = ReviewStatus.PENDING.value
    available_actions: List[str] = Field(
        default_factory=lambda: ["approve", "reject", "edit", "regenerate"]
    )
    reviewer_notes: str = ""


class ContactRecommendation(BaseModel):
    """
    Full recommendation output for a single contact.
    This is the primary output of the recommendation workflow.
    """
    contact_id: str = ""
    contact_name: str = ""
    profile_signals: ProfileSignals = Field(default_factory=ProfileSignals)
    search_trace: SearchTrace = Field(default_factory=SearchTrace)
    recommended_gifts: List[RecommendedGift] = Field(default_factory=list)
    human_review: HumanReview = Field(default_factory=HumanReview)
    workflow_status: str = "pending"  # pending, processing, completed, failed
    current_step: str = ""
    error: Optional[str] = None


class RecommendationListResponse(BaseModel):
    """Response for listing all recommendations."""
    recommendations: List[ContactRecommendation]
    total: int


class ReviewAction(BaseModel):
    """Request body for a human review action."""
    action: str  # approve, reject, edit, regenerate
    notes: Optional[str] = ""
    edited_gifts: Optional[List[RecommendedGift]] = None
