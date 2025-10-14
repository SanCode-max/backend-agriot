from fastapi import APIRouter,HTTPException
from config.conexion import DB_NAME
from schemas.user import userEntity,listUser
from models.users import usuario

user = APIRouter()

@user.get("/")
def conection():
    return{"mensaje": "Conexion exitosa con MongoDB"}

@user.post("/registro")
def registrar_usuario(usuario: dict):   
    try:
        coleccion = DB_NAME("usuarios")
        resultado = coleccion.insert_one(user)
        return {"mensaje": "Usuario registrado exitosamente", "id": str(resultado.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar: {e}")
    
