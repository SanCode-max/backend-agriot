from fastapi import APIRouter,HTTPException
from config.conexion import db
from schemas.user import userEntity,listUser
from models.users import usuario

user = APIRouter()

@user.get("/")
def conection():
    return{"mensaje": "Conexion exitosa con MongoDB"}

@user.post("/registro")
def registrar_usuario(user_data : usuario):   
    try:
        coleccion = db["usuarios"]
        resultado = coleccion.insert_one(user_data.dict())
        return {"mensaje": f"Usuario {user_data.nombre} registrado exitosamente", "id": str(resultado.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar: {e}")