import cloudinary
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(secure=True)