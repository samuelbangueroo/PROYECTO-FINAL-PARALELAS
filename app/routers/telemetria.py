from pathlib import Path
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path as PathParam, Query, Request, Response
from fastapi.responses import FileResponse
from app.routers.errores import SolicitudInvalida

from app.repositories.telemetria import RepositorioNoDisponible   
from app.services.telemetria import ConsultaLecturas, ServicioTelemetria

from app.schemas.telemetria import (
    FechaRFC3339,
    Identificador,
    LecturaTelemetria,
    LoteTelemetria,
    Modo,
    ResultadoLote,
    Salud,
    TipoActivo,
)
from app.services.telemetria import ServicioTelemetria

router = APIRouter()
contrato = Path(__file__).resolve().parents[2] / "openapi.yaml"


def obtener_servicio(request: Request) -> ServicioTelemetria:
    return request.app.state.servicio


def validar_consumidor(
    consumidor: Annotated[str | None, Header(alias="X-Equipo-Consumidor", pattern=r"^equipo-[1-7]$")] = None,
) -> None:
    pass


Servicio = Annotated[ServicioTelemetria, Depends(obtener_servicio)]


@router.post(
    "/telemetria",
    operation_id="registrarTelemetria",
    dependencies=[Depends(validar_consumidor)],
)
def registrar_telemetria(
    lote: LoteTelemetria,
    servicio: Servicio,
    modo: Modo = "paralelo",
    workers: Annotated[int | None, Query(ge=1, le=64)] = None,
) -> ResultadoLote:
    # Se validan las opciones del contrato. La demo registra el modo realmente ejecutado.
    return servicio.registrar(lote)


@router.get(
    "/telemetria/{plantaId}",
    operation_id="consultarTelemetriaPorPlanta",
    response_model_exclude_none=True,
    dependencies=[Depends(validar_consumidor)],
)
def consultar_telemetria(
    plantaId: Annotated[Identificador, PathParam()],
    servicio: Servicio,
    response: Response,
    desde: Annotated[FechaRFC3339 | None, Query()] = None,
    hasta: Annotated[FechaRFC3339 | None, Query()] = None,
    activoId: Annotated[Identificador | None, Query()] = None,
    tipoActivo: TipoActivo | None = None,
    metrica: Annotated[str | None, Query(min_length=1)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LecturaTelemetria]:
    if desde is not None and hasta is not None and desde >= hasta:
        raise SolicitudInvalida("desde", "debe ser anterior a hasta")
    consulta = ConsultaLecturas(plantaId, desde, hasta, activoId, tipoActivo, metrica)
    lecturas, siguiente = servicio.consultar(consulta, offset=offset, limite=limit)
    if siguiente is not None:
        response.headers["X-Next-Offset"] = str(siguiente)
    return lecturas


@router.get("/health", operation_id="consultarSalud")
def consultar_salud(request: Request, response: Response, servicio: Servicio) -> Salud:
    try:
        disponible = servicio.repositorio.disponible()
    except RepositorioNoDisponible:
        disponible = False
    if not disponible:
        response.status_code = 503
    return Salud(
        estado="disponible" if disponible else "no_disponible",
        baseDatos="ok" if disponible else "error",
        tiempoActivoSeg=int(monotonic() - request.app.state.inicio),
    )


@router.get("/openapi.yaml", operation_id="obtenerContrato")
def obtener_contrato() -> FileResponse:
    return FileResponse(contrato, media_type="application/yaml")
