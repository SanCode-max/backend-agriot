from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
connection = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(connection, tls=True)
db = client[DB_NAME]

print(db.list_collection_names())
