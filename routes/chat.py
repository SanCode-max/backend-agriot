"""
chat.py (routes/chat.py)
Handles POST /api/chat — receives a message + history from the frontend,
calls the Google Gemini API, and returns the AI reply.
API key is read from GEMINI_API_KEY environment variable.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Literal

import google.generativeai as genai
import grpc
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from google.api_core.exceptions import (
    Forbidden,
    GoogleAPICallError,
    PermissionDenied,
    ResourceExhausted,
    Unauthenticated,
)
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a helpful, ethical, and autonomous AI assistant integrated into a Knowledge Management platform.
You support human development, autonomy, and responsible thinking.
Always respond in the same language the user writes in — Spanish or English.
If the user writes in Spanish, respond fully in Spanish.
If the user writes in English, respond fully in English.
Be concise, clear, and supportive. Encourage critical thinking and personal growth."""

# `gemini-1.5-flash` is often retired on the consumer API; 2.0 Flash works with AI Studio keys.
MODEL_NAME = "gemini-2.0-flash"

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


def _call_gemini(message: str, history: list[ChatHistoryItem]) -> str:
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Chat service is not configured.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
    )

    gemini_history = [
        {"role": item.role, "parts": [item.content]} for item in history
    ]
    chat_session = model.start_chat(history=gemini_history)
    response = chat_session.send_message(message)

    if response.candidates:
        cand = response.candidates[0]
        parts = cand.content.parts
        texts = [p.text for p in parts if getattr(p, "text", None)]
        if texts:
            out = "".join(texts).strip()
            if out:
                return out

    text = getattr(response, "text", None)
    if text and str(text).strip():
        return str(text).strip()

    raise RuntimeError("The model did not return any text.")


def _is_quota_exceeded(exc: Exception) -> bool:
    if isinstance(exc, ResourceExhausted):
        return True
    if isinstance(exc, GoogleAPICallError) and getattr(exc, "grpc_status_code", None) == grpc.StatusCode.RESOURCE_EXHAUSTED:
        return True
    if isinstance(exc, grpc.RpcError) and exc.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
        return True
    msg = str(exc).lower()
    return "429" in msg and "quota" in msg


def _is_auth_key_error(exc: Exception) -> bool:
    if isinstance(exc, (Unauthenticated, PermissionDenied, Forbidden)):
        return True
    if isinstance(exc, grpc.RpcError) and exc.code() in (
        grpc.StatusCode.UNAUTHENTICATED,
        grpc.StatusCode.PERMISSION_DENIED,
    ):
        return True
    return False


@chat_router.post("/chat")
async def chat_endpoint(body: ChatRequest):
    if not (os.environ.get("GEMINI_API_KEY") or "").strip():
        logger.warning("Chat request rejected: GEMINI_API_KEY is missing or empty")
        return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)

    try:
        reply = await asyncio.to_thread(_call_gemini, body.message, body.history)
        if not reply or not str(reply).strip():
            raise RuntimeError("Empty model reply")
        return {"reply": reply}
    except ResourceExhausted as e:
        logger.warning("Gemini quota exceeded: %s", type(e).__name__)
        return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
    except (Unauthenticated, PermissionDenied, Forbidden) as e:
        logger.warning("Gemini API key or auth error: %s", type(e).__name__)
        return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
    except GoogleAPICallError as e:
        if _is_quota_exceeded(e):
            logger.warning("Gemini quota exceeded (GoogleAPICallError)")
            return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
        if _is_auth_key_error(e):
            logger.warning("Gemini auth error (GoogleAPICallError): %s", type(e).__name__)
            return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
        code = getattr(e, "code", None)
        if code in (401, 403):
            logger.warning("Gemini HTTP status on API call: %s", code)
            return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
        if code == 429:
            logger.warning("Gemini HTTP 429 (GoogleAPICallError)")
            return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
        logger.exception("Gemini GoogleAPICallError")
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to complete the chat request."},
        )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
            logger.warning("Gemini quota exceeded (gRPC)")
            return JSONResponse(status_code=429, content=_QUOTA_EXCEEDED_BODY)
        if e.code() in (
            grpc.StatusCode.UNAUTHENTICATED,
            grpc.StatusCode.PERMISSION_DENIED,
        ):
            logger.warning("Gemini auth error (gRPC): %s", e.code())
            return JSONResponse(status_code=503, content=_INVALID_KEY_BODY)
        logger.exception("Gemini gRPC error: %s", e.code())
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
