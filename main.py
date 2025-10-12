from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import HTTPException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class usuario(BaseModel):
    nombre: str
    apellido: str
    correo: str
    telefono: str
    contraseña: str

@app.post("/registro")
def registrar_usuario(user: usuario):
    print(user.dict())
    if not user.nombre or not user.apellido or not user.correo or not user.telefono or not user.contraseña:
        raise HTTPException(status_code=400, detail="Todos los campos son obligatorios.")
    return {"mensaje": f"Usuario {user.nombre} registrado exitosamente."}
