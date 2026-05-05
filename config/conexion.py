from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

connection = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# URL pública del API (sin barra final); usada en enlaces guardados p.ej. fotos de perfil.
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE", "http://127.0.0.1:8000").rstrip("/")

client = AsyncIOMotorClient(connection)
db = client[DB_NAME]


async def ensure_indexes() -> None:
    """Índice único en correo para búsquedas O(log n) y registro/login más rápidos."""
    await db["usuarios"].create_index("correo", unique=True)


async def close_db() -> None:
    client.close()
