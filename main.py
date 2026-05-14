import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.conexion import ensure_indexes, close_db
from middleware.uploads_cache import UploadsCacheControlMiddleware
from routes.user import user
from routes import token
from routes.chat import chat_router

logger = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "https://frontend-agriot.vercel.app",
    "https://*.vercel.app",
    "https://frontend-agriot-santiago-torres-projects-ec92f9fd.vercel.app",
]


def _cors_allow_origins() -> list[str]:
    extra = os.getenv("CORS_ALLOW_ORIGINS", "")
    if not extra.strip():
        return list(_DEFAULT_CORS_ORIGINS)
    merged = list(_DEFAULT_CORS_ORIGINS)
    for part in extra.split(","):
        o = part.strip()
        if o and o not in merged:
            merged.append(o)
    return merged


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("GROQ_API_KEY"):
        logger.warning(
            "WARNING: GROQ_API_KEY is not set. Chat endpoint will not work."
        )
    os.makedirs("uploads", exist_ok=True)
    await ensure_indexes()
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(UploadsCacheControlMiddleware, max_age_seconds=3600)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/api/health")
async def api_health():
    """Comprueba que el proceso del API responde (útil para front / despliegues)."""
    return {"ok": True}


app.include_router(user)
app.include_router(token.restablecer)
app.include_router(chat_router)
