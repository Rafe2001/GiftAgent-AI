"""
Pydantic models for contact input data.
Matches the assignment's sample input schema exactly.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Experience(BaseModel):
    """A single work experience entry from LinkedIn profile."""
    title: str
    company: str
    description: Optional[str] = ""


class LinkedInProfile(BaseModel):
    """LinkedIn-style profile data scraped/enriched for a contact."""
    headline: str = ""
    about: str = ""
    experience: List[Experience] = Field(default_factory=list)
    recent_posts: List[str] = Field(default_factory=list)
    recent_comments: List[str] = Field(default_factory=list)
    engaged_topics: List[str] = Field(default_factory=list)


class RelationshipContext(BaseModel):
    """Context about the business relationship with this contact."""
    relationship_type: str = ""
    last_interaction: str = ""
    business_goal: str = ""


class GiftContext(BaseModel):
    """Constraints and context for the gift recommendation."""
    occasion: str = ""
    budget_min: float = 0
    budget_max: float = 5000
    currency: str = "INR"
    country: str = "India"


class Contact(BaseModel):
    """
    Full enriched contact data — the primary input to the recommendation workflow.
    Contains LinkedIn profile data, relationship context, and gift constraints.
    """
    name: str
    role: str = ""
    company: str = ""
    location: str = ""
    linkedin_profile: LinkedInProfile = Field(default_factory=LinkedInProfile)
    relationship_context: RelationshipContext = Field(default_factory=RelationshipContext)
    gift_context: GiftContext = Field(default_factory=GiftContext)


class ContactUploadRequest(BaseModel):
    """Request body for uploading one or more contacts."""
    contacts: List[Contact]
