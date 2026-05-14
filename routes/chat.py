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
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SYSTEM_PROMPT = """You are a helpful, ethical, and autonomous AI assistant integrated into a Knowledge Management platform.
You support human development, autonomy, and responsible thinking.
Always respond in the same language the user writes in — Spanish or English.
If the user writes in Spanish, respond fully in Spanish.
If the user writes in English, respond fully in English.
Be concise, clear, and supportive. Encourage critical thinking and personal growth."""

MODEL_NAME = "gemini-1.5-flash"

chat_router = APIRouter(prefix="/api", tags=["chat"])


class ChatHistoryItem(BaseModel):
    role: Literal["user", "model"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatHistoryItem] = Field(default_factory=list)


def _call_gemini(message: str, history: list[ChatHistoryItem]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
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
        parts = response.candidates[0].content.parts
        texts = [p.text for p in parts if getattr(p, "text", None)]
        if texts:
            return "".join(texts)

    text = getattr(response, "text", None)
    if text:
        return text

    raise RuntimeError("The model did not return any text.")


@chat_router.post("/chat")
async def chat_endpoint(body: ChatRequest):
    try:
        reply = await asyncio.to_thread(_call_gemini, body.message, body.history)
        return {"reply": reply}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to complete the chat request."},
        )
