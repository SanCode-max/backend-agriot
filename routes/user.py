import asyncio
import uuid

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File
from passlib.context import CryptContext

from config.conexion import PUBLIC_API_BASE, db
from models.users import usuario, Cultivos, PerfilUpdate, LoginRequest

user = APIRouter()

hasheo = CryptContext(schemes=["argon2"], deprecated="auto")


def get_contraseña_hash(password: str) -> str:
    password_bytes = password.strip().encode("utf-8")[:72]
    return hasheo.hash(password_bytes)


def _perfil_campos(datos: PerfilUpdate) -> dict:
    if hasattr(datos, "model_dump"):
        return datos.model_dump(exclude_unset=True, exclude_none=True)
    return {k: v for k, v in datos.dict(exclude_unset=True).items() if v is not None}


def _cultivo_coincide_id(item: dict, cultivo_id: str) -> bool:
    """Coincide con `id` (uuid guardado al crear) o con `_id` si el cliente envía el de MongoDB."""
    req = cultivo_id.strip()
    if not req:
        return False
    if item.get("id") is not None and str(item["id"]) == req:
        return True
    if item.get("_id") is not None and str(item["_id"]) == req:
        return True
    return False


@user.post("/registro")
async def registrar_usuario(user_data: usuario):
    try:
        coleccion = db["usuarios"]
        existe = await coleccion.find_one(
            {"correo": user_data.correo},
            projection={"_id": 1},
        )
        if existe:
            raise HTTPException(status_code=400, detail="El correo ya esta registrado")
        if not user_data.password:
            raise HTTPException(status_code=400, detail="No se detecto la contraseña")

        contra_Hasheada = await asyncio.to_thread(
            get_contraseña_hash, user_data.password
        )

        documento = {
            "nombre": user_data.nombre,
            "apellido": user_data.apellido,
            "telefono": user_data.telefono,
            "correo": user_data.correo,
            "password": contra_Hasheada,
            "profesion": "",
            "ubicacion": "",
            "descripcion": "",
            "foto": "",
            "cultivos": [],
        }

        resultado = await coleccion.insert_one(documento)
        return {
            "mensaje": f"Usuario {user_data.nombre} registrado exitosamente",
            "id": str(resultado.inserted_id),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar: {e}")


def verificar_Contraseña(password_plano: str, password_hasheado: str) -> bool:
    return hasheo.verify(password_plano, password_hasheado)


@user.post("/login")
async def login_user(user_data: LoginRequest):
    try:
        coleccion = db["usuarios"]
        usuario_encontrado = await coleccion.find_one(
            {"correo": user_data.correo},
            projection={"password": 1, "nombre": 1, "correo": 1},
        )

        if not usuario_encontrado:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado, por favor registrese",
            )

        password_guardada = usuario_encontrado.get("password")
        ok = await asyncio.to_thread(
            verificar_Contraseña, user_data.password, password_guardada
        )
        if not ok:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        return {
            "mensaje": f"Bienvenido {usuario_encontrado.get('nombre')}",
            "usuario": {
                "nombre": usuario_encontrado.get("nombre"),
                "correo": usuario_encontrado.get("correo"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ingresar: {e}")


@user.get("/perfil/{correo}")
async def obtener_perfil(correo: str):
    try:
        coleccion = db["usuarios"]
        usuario_encontrado = await coleccion.find_one(
            {"correo": correo},
            projection={
                "nombre": 1,
                "apellido": 1,
                "telefono": 1,
                "correo": 1,
                "profesion": 1,
                "ubicacion": 1,
                "descripcion": 1,
                "foto": 1,
            },
        )

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
            "foto": usuario_encontrado.get("foto", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {e}")


@user.put("/perfil/{correo}")
async def actualizar_perfil(correo: str, datos: PerfilUpdate):
    try:
        coleccion = db["usuarios"]
        campos_actualizar = _perfil_campos(datos)

        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se enviaron datos")

        resultado = await coleccion.update_one(
            {"correo": correo},
            {"$set": campos_actualizar},
        )

        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"mensaje": "Perfil actualizado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar perfil: {e}")


@user.post("/perfil/foto/{correo}")
async def subir_foto(correo: str, foto: UploadFile = File(...)):
    try:
        coleccion = db["usuarios"]

        usuario_encontrado = await coleccion.find_one(
            {"correo": correo},
            projection={"_id": 1},
        )

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        extension = foto.filename.split(".")[-1]
        nombre_archivo = f"{correo.replace('@', '_')}.{extension}"
        ruta_guardado = f"uploads/{nombre_archivo}"

        contenido = await foto.read()
        async with aiofiles.open(ruta_guardado, "wb") as buffer:
            await buffer.write(contenido)

        ruta_foto = f"{PUBLIC_API_BASE}/uploads/{nombre_archivo}"

        await coleccion.update_one(
            {"correo": correo},
            {"$set": {"foto": ruta_foto}},
        )

        return {
            "mensaje": "Foto actualizada correctamente",
            "foto": ruta_foto,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir foto: {e}")


@user.get("/cultivos/{correo}")
async def obtener_cultivos(correo: str):
    try:
        coleccion = db["usuarios"]

        usuario_encontrado = await coleccion.find_one(
            {"correo": correo},
            projection={"nombre": 1, "cultivos": 1},
        )

        if not usuario_encontrado:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "nombre": usuario_encontrado["nombre"],
            "cultivos": usuario_encontrado.get("cultivos", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al encontrar usuario: {e}",
        )


@user.post("/cultivos")
async def registrar_cultivo(user_data: Cultivos):
    try:
        coleccion = db["usuarios"]

        cultivo = {
            "id": str(uuid.uuid4()),
            "nombre": user_data.nombre,
            "fechaSiembra": user_data.fechaSiembra,
            "fechaCosecha": user_data.fechaCosecha,
            "estado": user_data.estado,
            "ubicacion": user_data.ubicacion,
            "observaciones": user_data.observaciones,
            "latitud": user_data.latitud,
            "longitud": user_data.longitud,
        }

        resultado = await coleccion.update_one(
            {"correo": user_data.correo},
            {"$push": {"cultivos": cultivo}},
        )

        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "mensaje": "Cultivo registrado exitosamente",
            "cultivo": cultivo,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar cultivo: {e}",
        )


@user.delete("/cultivos/{correo}/{cultivo_id}")
async def eliminar_cultivo(correo: str, cultivo_id: str):
    try:
        cid = cultivo_id.strip()
        if not cid or cid.lower() in ("undefined", "null", "none"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Falta el id del cultivo en la URL. En el frontend usá el campo "
                    "`id` del objeto cultivo (p. ej. cultivo.id), no una variable vacía."
                ),
            )

        coleccion = db["usuarios"]
        doc = await coleccion.find_one(
            {"correo": correo.strip()},
            projection={"cultivos": 1},
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cultivos = doc.get("cultivos") or []
        hay_coincidencia = any(
            isinstance(c, dict) and _cultivo_coincide_id(c, cid)
            for c in cultivos
        )
        if not hay_coincidencia:
            raise HTTPException(
                status_code=404,
                detail="Cultivo no encontrado (verifica que envías el campo id del cultivo)",
            )

        restantes = [
            c
            for c in cultivos
            if not (isinstance(c, dict) and _cultivo_coincide_id(c, cid))
        ]

        await coleccion.update_one(
            {"correo": correo.strip()},
            {"$set": {"cultivos": restantes}},
        )

        return {"mensaje": "Cultivo eliminado"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
