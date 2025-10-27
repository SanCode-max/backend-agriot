from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

load_dotenv()

SECRET_KEY= os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def crear_token(correo: str, expiracion:int = 1):
    expira = datetime.utcnow() + timedelta(hours=expiracion)
    data = {"sub": correo, "exp": expira}
    return jwt.encode(data, SECRET_KEY,  algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms= [ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El enlace ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")