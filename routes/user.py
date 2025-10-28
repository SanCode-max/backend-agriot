from fastapi import APIRouter,HTTPException
from config.conexion import db
from schemas.user import userEntity,listUser
from models.users import usuario
from passlib.context import CryptContext

user = APIRouter()

#Hasheo de contraseña
hasheo = CryptContext(schemes=["argon2"], deprecated="auto")


def get_contraseña_hash(password: str) -> str:
    password_bytes = password.strip().encode("utf-8")[:72]
    return hasheo.hash(password_bytes)

@user.post("/registro")
def registrar_usuario(user_data : usuario):   
    try:
        coleccion = db["usuarios"]

        #Verificación de correo existente
        if coleccion.find_one({"correo": user_data.correo}):
            raise HTTPException(status_code=400, detail="El correo ya esta registrado")
        if not user_data.password:
            raise HTTPException(status_code=400, detail="No se detecto la contraseña")

        
        
        contra_Hasheada= get_contraseña_hash(user_data.password)

        #documento a insertar
        documento = {
            "nombre":user_data.nombre,
            "apellido":user_data.apellido,
            "telefono":user_data.telefono,
            "correo":user_data.correo,
            "password":contra_Hasheada,
        }
        
        resultado = coleccion.insert_one(documento)
        return {
            "mensaje": f"Usuario {user_data.nombre} registrado exitosamente", 
            "id": str(resultado.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar: {e}")

#verificacion de la contraseña hashada
def verificar_Contraseña(password_plano: str, password_hasheado: str) -> bool:
    return hasheo.verify(password_plano,password_hasheado)
    
@user.post("/login")
def login_user(user_data: dict):
    try:
        coleccion = db["usuarios"]

        #Buscar el correo en la base de datos
        usuario_encontrado = coleccion.find_one({"correo": user_data.get("correo")})

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        #Obtener contraseña guardada
        password_guardada = usuario_encontrado.get("password")

        #verificar contraseña
        if not verificar_Contraseña(user_data.get("password"), password_guardada):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        return {
            "mensaje": f"Bienvenido {usuario_encontrado.get('nombre')}",
            "usuario": {
                "nombre": usuario_encontrado.get("nombre"),
                "correo": usuario_encontrado.get("correo")
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ingresar: {e}")
    

@user.get("/usuario/{correo}")
def obtener_usuarios(correo: str):
    try:
        coleccion = db["usuarios"]
        usuario_encontrado= coleccion.find_one({"correo": correo})
        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {
            "nombre":usuario_encontrado["nombre"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al encontrar usuario: {e}")