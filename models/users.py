from pydantic import BaseModel,Field
from typing import Optional

class usuario(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    correo: str
    password: str