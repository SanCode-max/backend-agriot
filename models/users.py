from pydantic import BaseModel,EmailStr
from typing import Optional

class usuario(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    correo: str
    password: str

class Requisito_reestablecer_password(BaseModel):
    correo: str

class password_reseteada(BaseModel):
    token: str
    nueva_password: str