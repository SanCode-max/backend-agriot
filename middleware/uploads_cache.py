"""Cabeceras de caché para archivos estáticos bajo /uploads."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class UploadsCacheControlMiddleware(BaseHTTPMiddleware):
    """Evita que el navegador repita descargas innecesarias si la URL de la imagen no cambia."""

    def __init__(self, app, max_age_seconds: int = 3600):
        super().__init__(app)
        self._directive = f"public, max-age={max_age_seconds}"

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/uploads"):
            response.headers["Cache-Control"] = self._directive
        return response
