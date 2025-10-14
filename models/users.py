from pydantic import BaseModel

class usuario(BaseModel):
    id: int
    nombre: str
    apellido: str
    telefono: str
    correo: str
    contraseña: str