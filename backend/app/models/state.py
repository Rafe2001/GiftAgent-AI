"""
LangGraph workflow state definition.
This TypedDict holds all intermediate data flowing through the graph nodes.
"""

from typing import TypedDict, List, Optional, Any


class ProductCandidate(TypedDict, total=False):
    """A product found during search, before validation."""
    title: str
    url: str
    price: str
    price_numeric: float
    snippet: str
    store: str
    source_query: str


class WorkflowState(TypedDict, total=False):
    """
    The state object passed through all LangGraph nodes.
    Each node reads from and writes to specific fields.
    """
    # Input
    contact: dict  # Raw contact data
    contact_id: str

    # Signal extraction (node: extract_signals)
    strong_signals: List[str]
    weak_signals: List[str]
    signals_to_avoid: List[str]

    # Search (node: search_products)
    search_queries: List[str]
    raw_search_results: List[ProductCandidate]

    # Validation (node: validate_products)
    validated_products: List[ProductCandidate]

    # Ranking (node: rank_gifts)
    ranked_gifts: List[dict]  # Top 3 ranked gift dicts

    # Message generation (node: generate_messages)
    gifts_with_messages: List[dict]  # Ranked gifts + personalised messages

    # Workflow metadata
    current_step: str
    errors: List[str]
    workflow_status: str  # pending, processing, completed, failed

    # Finalized output fields (node: finalize)
    contact_name: str
    profile_signals: dict
    search_trace: dict
    recommended_gifts: List[dict]
    human_review: dict
