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
    nueva_password: str
    token: str
    confirmacion_password: str

class Cultivos(BaseModel):
    correo: str
    nombre: str
    fechaSiembra: str
    fechaCosecha: str
    estado: Optional[str]
    ubicacion: Optional[str]