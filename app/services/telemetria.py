from time import perf_counter

from app.repositories.telemetria import FiltrosLecturas, RepositorioTelemetria
from app.schemas.telemetria import (
    LecturaTelemetria,
    LoteTelemetria,
    MetricasProcesamiento,
    ResultadoLote,
)


class ServicioTelemetria:
    def __init__(self, repositorio: RepositorioTelemetria) -> None:
        self.repositorio = repositorio

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
        self, filtros: FiltrosLecturas, *, offset: int, limite: int
    ) -> tuple[list[LecturaTelemetria], int | None]:
        # Pedir una fila adicional evita una consulta de conteo.
        lecturas = self.repositorio.consultar(filtros, offset=offset, limite=limite + 1)
        siguiente = offset + limite if len(lecturas) > limite else None
        return lecturas[:limite], siguiente
