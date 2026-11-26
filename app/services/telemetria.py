from dataclasses import dataclass
from datetime import datetime
from time import perf_counter

from app.clients.activos import ClienteActivosFalso
from app.core.tipos import TipoActivo
from app.repositories.telemetria import FiltrosLecturas, RepositorioTelemetria
from app.schemas.telemetria import (
    LecturaTelemetria,
    LoteTelemetria,
    MetricasProcesamiento,
    ResultadoLote,
)


@dataclass(frozen=True)
class ConsultaLecturas:
    """Lo que pide el cliente de la API; el servicio lo traduce a FiltrosLecturas."""

    planta_id: str
    desde: datetime | None
    hasta: datetime | None
    activo_id: str | None
    tipo_activo: TipoActivo | None
    metrica: str | None


class ServicioTelemetria:
    def __init__(self, repositorio: RepositorioTelemetria, activos: ClienteActivosFalso) -> None:
        self.repositorio = repositorio
        self.activos = activos

    def registrar(self, lote: LoteTelemetria) -> ResultadoLote:
        inicio = perf_counter()
        self.repositorio.guardar(lote.lecturas)
        cantidad = len(lote.lecturas)
        return ResultadoLote(
            recibidas=cantidad,
            procesadas=cantidad,
            descartadas=0,
            metricas=MetricasProcesamiento(
                modo="secuencial",
                workers=1,
                elementos=cantidad,
                duracionMs=int((perf_counter() - inicio) * 1000),
            ),
        )

    def consultar(
        self, consulta: ConsultaLecturas, *, offset: int, limite: int
    ) -> tuple[list[LecturaTelemetria], int | None]:
        filtros = FiltrosLecturas(
            planta_id=consulta.planta_id,
            desde=consulta.desde,
            hasta=consulta.hasta,
            activos_ids=self._resolver_activos(consulta),
            metrica=consulta.metrica,
        )
        # Pedir una fila adicional evita una consulta de conteo.
        lecturas = self.repositorio.consultar(filtros, offset=offset, limite=limite + 1)
        siguiente = offset + limite if len(lecturas) > limite else None
        return lecturas[:limite], siguiente

    def _resolver_activos(self, consulta: ConsultaLecturas) -> list[str] | None:
        """None = sin filtro por activo; lista vacía = nada puede coincidir."""
        ids = None
        if consulta.tipo_activo is not None:
            ids = self.activos.ids_por_tipo(consulta.planta_id, consulta.tipo_activo)
        if consulta.activo_id is not None:
            ids = [consulta.activo_id] if ids is None or consulta.activo_id in ids else []
        return ids