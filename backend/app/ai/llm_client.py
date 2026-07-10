import asyncio
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings


class LLMClientError(Exception):
    """Raised when the LLM request cannot produce a usable diagnosis."""


class OpenRouterClient:
    def __init__(self) -> None:
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout = httpx.Timeout(30.0)
        self.max_retries = 2

    async def complete(self, messages: list[dict[str, str]]) -> str:
        if not settings.openrouter_api_key:
            raise LLMClientError("OPENROUTER_API_KEY is not configured")

        if not settings.openrouter_model:
            raise LLMClientError("OPENROUTER_MODEL is not configured")

        payload = {
            "model": settings.openrouter_model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 900,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": "AI Kubernetes Agent",
        }

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    if not content:
                        raise LLMClientError("OpenRouter returned an empty response")
                    return content
                except (httpx.HTTPError, KeyError, IndexError, ValueError, LLMClientError) as error:
                    last_error = error
                    logger.warning(
                        "OpenRouter request failed on attempt {}: {}",
                        attempt + 1,
                        self._safe_error_message(error),
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(2**attempt)

        raise LLMClientError(f"OpenRouter request failed: {self._safe_error_message(last_error)}")

    def _safe_error_message(self, error: Exception | None) -> str:
        if error is None:
            return "unknown error"
        return str(error).replace(settings.openrouter_api_key, "[redacted]")
