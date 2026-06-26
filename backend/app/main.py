"""
FastAPI Application Entry Point
Gift Recommendation Agent — Hyper-Personalised Gift Recommendation System
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

# Create FastAPI app
app = FastAPI(
    title="Gift Recommendation Agent",
    description=(
        "Hyper-Personalised Gift Recommendation System — "
        "AI-powered multi-step workflow that analyses LinkedIn-style profile data "
        "and recommends real, purchasable gifts with personalised messages."
    ),
    version="1.0.0",
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Gift Recommendation Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
