"""
LangGraph Workflow Definition
Wires all nodes into a directed graph with conditional edges for:
- Retry loop: validation failure → broaden queries → search again
- Regenerate loop: human rejects → back to ranking
- Normal flow: ingest → extract → filter → queries → search → validate → rank → messages → finalize
"""

import logging
from langgraph.graph import StateGraph, START, END

from app.models.state import WorkflowState
from app.workflow.nodes.ingest import ingest_contact
from app.workflow.nodes.extract_signals import extract_signals
from app.workflow.nodes.filter_signals import filter_signals
from app.workflow.nodes.generate_queries import generate_search_queries
from app.workflow.nodes.search_products import search_products
from app.workflow.nodes.validate_products import validate_products
from app.workflow.nodes.rank_gifts import rank_gifts
from app.workflow.nodes.generate_message import generate_messages
from app.workflow.nodes.finalize import finalize_output

logger = logging.getLogger(__name__)


def should_retry_search(state: WorkflowState) -> str:
    """
    Conditional edge after validation:
    - If validation failed (< 2 products) and retries remain → go back to search
    - Otherwise → proceed to ranking
    """
    if state.get("_validation_failed", False):
        retry_count = state.get("_retry_count", 0)
        if retry_count <= 2:
            logger.info("Validation failed — retrying search (attempt %d)", retry_count)
            return "retry_search"
    return "proceed_to_ranking"


def check_ingest_status(state: WorkflowState) -> str:
    """
    Conditional edge after ingestion:
    - If ingestion failed → go to finalize (output error)
    - Otherwise → proceed to signal extraction
    """
    if state.get("workflow_status") == "failed":
        return "failed"
    return "continue"


def build_workflow() -> StateGraph:
    """
    Build and compile the gift recommendation LangGraph workflow.
    
    Graph structure:
    
    START → ingest → extract_signals → filter_signals → generate_queries
           ↓ (fail)
           finalize
    
    generate_queries → search_products → validate_products
                                              ↓
                                    [retry?] → search_products (loop)
                                    [ok]    → rank_gifts
    
    rank_gifts → generate_messages → finalize → END
    """
    workflow = StateGraph(WorkflowState)

    # Add all nodes
    workflow.add_node("ingest", ingest_contact)
    workflow.add_node("extract_signals", extract_signals)
    workflow.add_node("filter_signals", filter_signals)
    workflow.add_node("generate_queries", generate_search_queries)
    workflow.add_node("search_products", search_products)
    workflow.add_node("validate_products", validate_products)
    workflow.add_node("rank_gifts", rank_gifts)
    workflow.add_node("generate_messages", generate_messages)
    workflow.add_node("finalize", finalize_output)

    # Entry edge
    workflow.add_edge(START, "ingest")

    # Conditional: ingest success/failure
    workflow.add_conditional_edges(
        "ingest",
        check_ingest_status,
        {
            "continue": "extract_signals",
            "failed": "finalize",
        },
    )

    # Linear flow: extract → filter → generate queries → search
    workflow.add_edge("extract_signals", "filter_signals")
    workflow.add_edge("filter_signals", "generate_queries")
    workflow.add_edge("generate_queries", "search_products")
    workflow.add_edge("search_products", "validate_products")

    # Conditional: retry search or proceed to ranking
    workflow.add_conditional_edges(
        "validate_products",
        should_retry_search,
        {
            "retry_search": "search_products",
            "proceed_to_ranking": "rank_gifts",
        },
    )

    # Linear flow: rank → messages → finalize → END
    workflow.add_edge("rank_gifts", "generate_messages")
    workflow.add_edge("generate_messages", "finalize")
    workflow.add_edge("finalize", END)

    return workflow


def compile_workflow():
    """Compile the workflow into a runnable graph."""
    workflow = build_workflow()
    graph = workflow.compile()
    logger.info("Gift recommendation workflow compiled successfully")
    return graph


# Compile the graph at module level for reuse

recommendation_graph = compile_workflow()
