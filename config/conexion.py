from pymongo import MongoClient
from dotenv import load_dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Carga las variables del archivo .env
load_dotenv()

# Obtener datos del entorno
connection = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# Crear la conexión
try:
    client = AsyncIOMotorClient(connection)
    db = client[DB_NAME]
    print("✅ Conexión exitosa a MongoDB Atlas")
except Exception as e:
    print("❌ Error en la conexión:", e)
