"""
Application configuration loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the recomm_agent directory, backend directory, or parent directories
_env_path = Path(__file__).resolve().parents[2] / ".env"  # recomm_agent/.env
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parents[1] / ".env"  # recomm_agent/backend/.env
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parents[3] / ".env"  # learning/.env
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parents[4] / ".env"

load_dotenv(_env_path)


class Settings:
    """Application settings loaded from environment."""

    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # LLM Config
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096

    # Search Config
    MAX_SEARCH_RESULTS_PER_QUERY: int = 5
    MAX_SEARCH_QUERIES: int = 4

    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
