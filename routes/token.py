import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks

from config.conexion import db
from models.users import Requisito_reestablecer_password
from utils.token import crear_token, verificar_token
from utils.token_reset import enviar_email
from routes.user import get_contraseña_hash

restablecer = APIRouter()


@restablecer.post("/request_password")
async def solicitar_reset_password(
    request: Requisito_reestablecer_password,
    background_tasks: BackgroundTasks,
):
    try:
        correo = request.correo
        coleccion = db["usuarios"]
        usuario_encontrado = await coleccion.find_one(
            {"correo": correo},
            projection={"_id": 1},
        )

        if not usuario_encontrado:
            raise HTTPException(
                status_code=404,
                detail="El correo no se encuentra registrado en nuestra base de datos",
            )

        token = crear_token(correo)
        link = f"http://localhost:3000/Nueva_contraseña?token={token}"
        background_tasks.add_task(enviar_email, correo, link)
        return {"detail": "A tu correo se ha enviado un enlace para restablecer la contraseña"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error:{e}")


@restablecer.post("/reset_password")
async def resetear_password(data: dict):
    try:
        token = data.get("token")
        nueva_password = data.get("nueva_password")

        if not nueva_password or not isinstance(nueva_password, str):
            raise HTTPException(status_code=400, detail="Se requiere nueva_password")

        correo = verificar_token(token)
        if not correo:
            raise HTTPException(status_code=402, detail="Token inválido o expirado")

        coleccion = db["usuarios"]
        usuario = await coleccion.find_one(
            {"correo": correo},
            projection={"_id": 1},
        )
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        nueva_contra = await asyncio.to_thread(
            get_contraseña_hash, nueva_password[:72]
        )
        await coleccion.update_one(
            {"correo": correo},
            {"$set": {"password": nueva_contra}},
        )

        return {"detail": "Contraseña actualizada exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al restablecer la contraseña: {e}",
        )
