from dotenv import load_dotenv
import os
from fastapi_mail import FastMail,MessageSchema,ConnectionConfig
from pydantic import EmailStr
import jwt
from datetime import datetime, timedelta


load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = 587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)


async def enviar_email(correo: EmailStr, link: str):
    mensaje = MessageSchema(
        subject= "Restablecimiento de contraseña",
        recipients=[correo],
        body=f"""
        <h2>Solucitud de restablecimiento de contraseña</h2>
        <p>Desde la asocioción AGRIOT le brindamos la bienvenida.</p>
        <p>Haz click en el siguiente enlace para restablecer tu contraseña:</p>
        <a href="{link}">{link}</a>
        <p>Este link expirará en 1 hora.</p>
        """,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(mensaje)
