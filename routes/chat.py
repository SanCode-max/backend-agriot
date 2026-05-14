"""
chat.py (routes/chat.py)
Handles POST /api/chat — receives a message + history from the frontend,
calls the Groq API, and returns the AI reply.
API key is read from GROQ_API_KEY environment variable.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from groq import (
    APIStatusError,
    AuthenticationError,
    Groq,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a helpful, ethical, and autonomous AI assistant integrated into a Knowledge Management platform.
You support human development, autonomy, and responsible thinking.
You align with Persona Transhumana values: human dignity, conscious evolution, ethical autonomy, solidarity, and the responsible use of knowledge for individual and collective flourishing.
Always respond in the same language the user writes in — Spanish or English.
If the user writes in Spanish, respond fully in Spanish.
If the user writes in English, respond fully in English.
Be concise, clear, and supportive. Encourage critical thinking and personal growth."""

MODEL_NAME = "llama-3.1-8b-instant"

logger = logging.getLogger(__name__)

_QUOTA_EXCEEDED_BODY = {
    "error": "quota_exceeded",
    "reply": "El servicio de IA está temporalmente no disponible. Por favor intenta más tarde.",
}
_INVALID_KEY_BODY = {
    "error": "invalid_key",
    "reply": "El asistente no está configurado correctamente.",
}

chat_router = APIRouter(prefix="/api", tags=["chat"])


class ChatHistoryItem(BaseModel):
    role: Literal["user", "model"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatHistoryItem] = Field(default_factory=list)


def _history_to_messages(history: list[ChatHistoryItem]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in history:
        role = "assistant" if item.role == "model" else "user"
        out.append({"role": role, "content": item.content})
    return out


def _call_groq(message: str, history: list[ChatHistoryItem]) -> str:
    api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Chat service is not configured.")

    client = Groq(api_key=api_key)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *_history_to_messages(history),
        {"role": "user", "content": message},
    ]

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )

    choice = completion.choices[0]
    content = (choice.message.content or "").strip()
    if not content:
        raise RuntimeError("The model did not return any text.")
    return content


@chat_router.post("/chat")
async def chat_endpoint(body: ChatRequest):
    if not (os.environ.get("GROQ_API_KEY") or "").strip():
        logger.warning("Chat request rejected: GROQ_API_KEY is missing or empty")
        return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)

    try:
        reply = await asyncio.to_thread(_call_groq, body.message, body.history)
        if not reply or not str(reply).strip():
            raise RuntimeError("Empty model reply")
        return {"reply": reply}
    except RateLimitError as e:
        logger.warning("Groq rate limit / quota: %s", type(e).__name__)
        return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
    except (AuthenticationError, PermissionDeniedError) as e:
        logger.warning("Groq API key or auth error: %s", type(e).__name__)
        return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
    except APIStatusError as e:
        if e.status_code == 429:
            logger.warning("Groq HTTP 429")
            return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
        if e.status_code in (401, 403):
            logger.warning("Groq HTTP %s", e.status_code)
            return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
        logger.exception("Groq APIStatusError: %s", e.status_code)
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to complete the chat request."},
        )
    except RuntimeError as e:
        if "not configured" in str(e).lower() or "chat service" in str(e).lower():
            return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
        logger.exception("Chat RuntimeError")
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to complete the chat request."},
        )
    except Exception:
        logger.exception("Chat request failed")
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to complete the chat request."},
        )
