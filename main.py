import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.conexion import ensure_indexes, close_db
from middleware.uploads_cache import UploadsCacheControlMiddleware
from routes.user import user
from routes import token


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads", exist_ok=True)
    await ensure_indexes()
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)

app.add_middleware(UploadsCacheControlMiddleware, max_age_seconds=3600)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(user)
app.include_router(token.restablecer)
