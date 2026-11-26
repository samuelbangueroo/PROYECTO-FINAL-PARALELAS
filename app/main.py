import json
import logging
from contextlib import asynccontextmanager
from threading import BoundedSemaphore
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html

from app.clients.activos import ClienteActivosFalso
from app.repositories.telemetria import (
    RepositorioPostgres,
    RepositorioNoDisponible,
    RepositorioTelemetria,
)
from app.routers.errores import SolicitudInvalida, respuesta_error
from app.routers.telemetria import router
from app.services.telemetria import ServicioTelemetria

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.inicio = monotonic()
    yield


def crear_app(
    repositorio: RepositorioTelemetria | None = None, *, max_solicitudes: int = 8
) -> FastAPI:
    app = FastAPI(
        title="Voltrix Energy · Telemetría de Plantas",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    if repositorio is None:
        repositorio = RepositorioPostgres()
    app.state.servicio = ServicioTelemetria(
    repositorio=RepositorioPostgres(),
    activos=ClienteActivosFalso(),
)   
    admision = BoundedSemaphore(max_solicitudes)
    app.include_router(router)

    @app.get("/docs", include_in_schema=False)
    def documentacion(request: Request):
        url = request.url_for("obtener_contrato").path
        return get_swagger_ui_html(openapi_url=url, title=app.title)

    @app.middleware("http")
    async def identificar_peticion(request: Request, call_next):
        inicio = monotonic()
        request.state.request_id = str(uuid4())
        ruta = request.url.path.rstrip("/")
        if ruta == "/telemetria" or ruta.startswith("/telemetria/"):
            if admision.acquire(blocking=False):
                try:
                    response = await call_next(request)
                finally:
                    admision.release()
            else:
                response = respuesta_error(
                    request, 429, "SOBRECARGA", "El servicio alcanzó su capacidad de atención.",
                    headers={"Retry-After": "1"},
                )
        else:
            response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        logger.info(
            "%s",
            json.dumps({
                "requestId": request.state.request_id,
                "metodo": request.method,
                "ruta": request.url.path,
                "equipoConsumidor": request.headers.get("X-Equipo-Consumidor"),
                "estadoHttp": response.status_code,
                "duracionMs": round((monotonic() - inicio) * 1000, 2),
            }),
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def error_validacion(request: Request, error: RequestValidationError):
        detalles = [
            {
                "campo": ".".join(map(str, item["loc"][1:])) or str(item["loc"][0]),
                "problema": item["msg"],
            }
            for item in error.errors()
        ]
        return respuesta_error(
            request, 400, "SOLICITUD_INVALIDA", "La solicitud no cumple el contrato.",
            detalles=detalles,
        )

    @app.exception_handler(SolicitudInvalida)
    async def error_solicitud(request: Request, error: SolicitudInvalida):
        return respuesta_error(
            request, 400, "SOLICITUD_INVALIDA", "La solicitud no cumple el contrato.",
            detalles=[error.detalle],
        )

    @app.exception_handler(RepositorioNoDisponible)
    async def error_repositorio(request: Request, error: RepositorioNoDisponible):
        return respuesta_error(
            request, 503, "NO_DISPONIBLE", "No hay conexión con el almacenamiento.",
        )

    return app


app = crear_app()
