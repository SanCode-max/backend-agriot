from pydantic import BaseModel,EmailStr
from typing import Optional

class usuario(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    correo: EmailStr
    password: str


class Requisito_reestablecer_password(BaseModel):
    correo: EmailStr

class password_reseteada(BaseModel):
    nueva_password: str
    token: str
    confirmacion_password: str

class Cultivos(BaseModel):
    correo: EmailStr
    nombre: str
    fechaSiembra: str
    fechaCosecha: Optional[str] = None
    estado: Optional[str] = None
    ubicacion: Optional[str] = None
    observaciones: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    profesion: Optional[str] = None
    ubicacion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    descripcion: Optional[str] = None
    foto: Optional[str] = None