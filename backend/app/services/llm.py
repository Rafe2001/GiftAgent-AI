"""
LLM Service — uses LangChain's ChatGroq for Groq/Llama access.
Falls back to Google Gemini via langchain-google-genai if Groq fails.
"""

import json
import logging
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM interface using LangChain's ChatGroq (primary).
    Supports JSON mode for structured output parsing.
    """

    def __init__(self):
        self._groq_llm = None
        self._gemini_llm = None
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM clients via LangChain."""
        if settings.GROQ_API_KEY:
            self._groq_llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            logger.info("Groq LLM initialized via LangChain (model: %s)", settings.GROQ_MODEL)

        if settings.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._gemini_llm = ChatGoogleGenerativeAI(
                    google_api_key=settings.GOOGLE_API_KEY,
                    model=settings.GEMINI_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.LLM_MAX_TOKENS,
                )
                logger.info("Gemini LLM initialized via LangChain (model: %s)", settings.GEMINI_MODEL)
            except ImportError:
                logger.warning("langchain-google-genai not installed — Gemini fallback unavailable")

    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        json_mode: bool = True,
        temperature: Optional[float] = None,
    ) -> dict | str:
        """
        Call the LLM with automatic fallback.

        Args:
            prompt: The user prompt to send
            system_prompt: System-level instructions
            json_mode: If True, request JSON output and parse it
            temperature: Override default temperature

        Returns:
            Parsed dict if json_mode, otherwise raw string
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]

        # Try Groq first
        if self._groq_llm:
            try:
                llm = self._groq_llm
                if temperature is not None:
                    llm = llm.bind(temperature=temperature)

                if json_mode:
                    llm = llm.bind(response_format={"type": "json_object"})

                response = await llm.ainvoke(messages)
                content = response.content

                if json_mode:
                    return self._parse_json(content)
                return content

            except Exception as e:
                logger.warning("Groq call failed: %s. Falling back to Gemini.", str(e))

        # Fallback to Gemini
        if self._gemini_llm:
            try:
                llm = self._gemini_llm
                if json_mode:
                    # Append JSON instruction for Gemini
                    messages[-1] = HumanMessage(
                        content=prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks."
                    )

                response = await llm.ainvoke(messages)
                content = response.content

                if json_mode:
                    return self._parse_json(content)
                return content

            except Exception as e:
                logger.error("Gemini call also failed: %s", str(e))
                raise

        raise RuntimeError("No LLM client available. Check API keys in .env")

    def _parse_json(self, content: str) -> dict:
        """Parse JSON from LLM response, handling common formatting issues."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object within the text
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

            # Try array
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

            logger.error("Failed to parse JSON from LLM response: %s", content[:200])
            raise ValueError(f"Could not parse JSON from LLM response: {content[:200]}")


# Singleton instance
llm_service = LLMService()
