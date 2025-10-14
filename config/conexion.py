from pymongo import mongo_client
from dotenv import load_dotenv
import os

#Carga las variables de .env
load_dotenv()

#conexion
connection = os.getenv("connection")
DB_NAME = os.getenv("DB_NAME")