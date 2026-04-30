from fastapi import APIRouter,HTTPException, UploadFile, File
from config.conexion import db
from schemas.user import userEntity,listUser
from models.users import usuario, Cultivos, PerfilUpdate
from passlib.context import CryptContext
import os
import uuid


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
            "profesion": "",
            "ubicacion": "",
            "descripcion": "",
            "foto": "",
            "cultivos": []

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
            raise HTTPException(status_code=404, detail="Usuario no encontrado, por favor registrese")
        

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
    
#Obtener perfil de usuario
@user.get("/perfil/{correo}")
def obtener_perfil(correo: str):
    try:
        coleccion = db["usuarios"]

        usuario_encontrado = coleccion.find_one({"correo": correo})

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "nombre": usuario_encontrado.get("nombre", ""),
            "apellido": usuario_encontrado.get("apellido", ""),
            "telefono": usuario_encontrado.get("telefono", ""),
            "correo": usuario_encontrado.get("correo", ""),
            "profesion": usuario_encontrado.get("profesion", ""),
            "ubicacion": usuario_encontrado.get("ubicacion", ""),
            "descripcion": usuario_encontrado.get("descripcion", ""),
            "foto": usuario_encontrado.get("foto", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {e}")

#actualizar perfil de usuario
@user.put("/perfil/{correo}")
def actualizar_perfil(correo: str, datos: PerfilUpdate):
    try:
        coleccion = db["usuarios"]

        campos_actualizar = {
            k: v for k, v in datos.dict().items() if v is not None
        }

        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se enviaron datos")

        resultado = coleccion.update_one(
            {"correo": correo},
            {"$set": campos_actualizar}
        )

        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"mensaje": "Perfil actualizado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar perfil: {e}")

#Subir foto de perfil    
@user.post("/perfil/foto/{correo}")
async def subir_foto(correo: str, foto: UploadFile = File(...)):
    try:
        coleccion = db["usuarios"]

        usuario_encontrado = coleccion.find_one({"correo": correo})

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Extensión
        extension = foto.filename.split(".")[-1]

        # Nombre único
        nombre_archivo = f"{correo.replace('@','_')}.{extension}"

        ruta_guardado = f"uploads/{nombre_archivo}"

        # Guardar archivo
        with open(ruta_guardado, "wb") as buffer:
            buffer.write(await foto.read())

        # Ruta para frontend
        ruta_foto = f"http://127.0.0.1:8000/uploads/{nombre_archivo}"

        # Guardar en MongoDB
        coleccion.update_one(
            {"correo": correo},
            {"$set": {"foto": ruta_foto}}
        )

        return {
            "mensaje": "Foto actualizada correctamente",
            "foto": ruta_foto
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir foto: {e}")
    
#Obtener cultivos de un usuario
@user.get("/cultivos/{correo}")
def obtener_cultivos(correo: str):
    try:
        coleccion = db["usuarios"]

        usuario_encontrado = coleccion.find_one({"correo": correo})

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "nombre": usuario_encontrado["nombre"],
            "cultivos": usuario_encontrado.get("cultivos", [])
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al encontrar usuario: {e}"
        )

   

@user.post("/cultivos")
def registrar_cultivo(user_data: Cultivos):

    try:
        coleccion = db["usuarios"]

        cultivo = {
            "id": str(uuid.uuid4()),
            "nombre": user_data.nombre,
            "fechaSiembra": user_data.fechaSiembra,
            "fechaCosecha": user_data.fechaCosecha,
            "estado": user_data.estado,
            "ubicacion": user_data.ubicacion
        }

        resultado = coleccion.update_one(
            {"correo": user_data.correo},
            {"$push": {"cultivos": cultivo}}
        )

        if resultado.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return {"mensaje": "Cultivo registrado exitosamente"}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar cultivo: {e}"

        )



@user.delete("/cultivos/{correo}/{cultivo_id}")

def eliminar_cultivo(correo: str, cultivo_id: str):

    try:
        coleccion = db["usuarios"]

        resultado = coleccion.update_one(
            {"correo": correo},
            {"$pull": {"cultivos": {"id": cultivo_id}}}

        )

        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="Cultivo no encontrado")

        return {"mensaje": "Cultivo eliminado"}


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")