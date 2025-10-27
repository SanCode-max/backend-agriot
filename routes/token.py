from fastapi import APIRouter,HTTPException, BackgroundTasks
from config.conexion import db
from models.users import usuario, Requisito_reestablecer_password
from utils.token import crear_token,verificar_token
from utils.token_reset import enviar_email
from routes.user import get_contraseña_hash

restablecer = APIRouter()

#Enviar link de restablecimiento de contraseña
@restablecer.post("/request_password")
async def solicitar_reset_password(request: Requisito_reestablecer_password, background_tasks: BackgroundTasks):
    try:
        correo = request.correo
        coleccion = db["usuarios"]
        usuario_encontrado = coleccion.find_one({"correo": correo})
        
        if not usuario_encontrado:
            return {"detail": "El enlace se ha enviado al correo suministrado"}
        
        token = crear_token(correo)
        link = f"http://localhost:3000/Nueva_contraseña?token={token}"
        background_tasks.add_task(enviar_email, correo, link)

        return {"detail": "A tu correo se ha enviado un enlace para restablecer la contraseña"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error:{e}")

#Cambiar la contraseña
@restablecer.post("/reset_password")
def resetear_password(data : dict):
    try:
        token = data.get("token")
        nueva_password = data.get("nueva_password")

        correo = verificar_token(token)
        if not correo:
            raise HTTPException(status_code=402, detail="Token inválido o expirado")
        
        coleccion = db["usuarios"]
        usuario = coleccion.find_one({"correo": correo})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        nueva_contra = get_contraseña_hash(nueva_password[:72])
        coleccion.update_one({"correo": correo}, {"$set": {"password": nueva_contra}})
        
        return {"detail": "Contraseña actualizada exitosamente"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al restablecer la contraseña: {e}")