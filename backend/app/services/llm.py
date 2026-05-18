"""Unified LLM client: OpenRouter primary, Ollama local fallback.

Per REVISED-PRD.md §4: OpenRouter + Kimi cloud, Ollama on Apple Silicon as fallback.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    pass


@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str


def _msgs_to_dicts(messages: Iterable[ChatMessage | dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        if isinstance(m, ChatMessage):
            out.append(m.to_dict())
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


def _extract_message_text(message: dict) -> str:
    """Pull the user-facing text from an OpenAI/OpenRouter chat message.

    Reasoning/thinking models (e.g. Kimi K2 Thinking) sometimes return the final
    answer in `content` and sometimes in `reasoning` / `reasoning_content`.
    Fall back through the known fields.
    """
    for key in ("content", "reasoning_content", "reasoning"):
        value = message.get(key)
        if value:
            return value if isinstance(value, str) else str(value)
    return ""


async def _try_openrouter(messages: list[dict[str, str]], temperature: float, max_tokens: int) -> LLMResponse | None:
    if not settings.openrouter_api_key:
        return None
    url = f"{settings.openrouter_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://dclaw-crisis.local",
        "X-Title": "DClaw Crisis",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            message = data["choices"][0]["message"]
            text = _extract_message_text(message)
            if not text:
                logger.warning("openrouter returned empty content: %s", data)
                return None
            return LLMResponse(text=text, provider="openrouter", model=settings.openrouter_model)
    except Exception as exc:
        logger.warning("openrouter failed: %s", exc)
        return None


async def _try_ollama(messages: list[dict[str, str]], temperature: float, max_tokens: int) -> LLMResponse | None:
    url = f"{settings.ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            return LLMResponse(text=text, provider="ollama", model=settings.ollama_model)
    except Exception as exc:
        logger.warning("ollama failed: %s", exc)
        return None


async def chat(
    messages: Iterable[ChatMessage | dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> LLMResponse:
    """Send a chat completion request. Tries OpenRouter, falls back to Ollama."""
    msgs = _msgs_to_dicts(messages)
    result = await _try_openrouter(msgs, temperature, max_tokens)
    if result is not None:
        return result
    result = await _try_ollama(msgs, temperature, max_tokens)
    if result is not None:
        return result
    raise LLMUnavailableError(
        "No LLM provider reachable. Set OPENROUTER_API_KEY or run Ollama at OLLAMA_URL."
    )


async def complete(
    system: str,
    user: str,
    *,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> LLMResponse:
    """Single-turn helper."""
    return await chat(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def complete_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Single-turn helper that parses the response as JSON.

    Strips markdown fences and extracts the first JSON object from any surrounding text,
    which thinking models often emit.
    """
    res = await complete(system, user, temperature=temperature, max_tokens=max_tokens)
    text = res.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        if text.startswith("json"):
            text = text[4:].lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
