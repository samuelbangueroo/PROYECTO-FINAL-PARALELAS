from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Protocol

from app.schemas.telemetria import LecturaTelemetria, TipoActivo


class RepositorioNoDisponible(Exception):
    """El almacenamiento no pudo completar la operación."""


@dataclass(frozen=True)
class FiltrosLecturas:
    planta_id: str
    desde: datetime | None
    hasta: datetime | None
    activo_id: str | None
    tipo_activo: TipoActivo | None
    metrica: str | None


class RepositorioTelemetria(Protocol):
    def guardar(self, lecturas: list[LecturaTelemetria]) -> None:
        """Guarda el lote completo o lanza RepositorioNoDisponible."""
        ...

    def consultar(
        self, filtros: FiltrosLecturas, *, offset: int, limite: int
    ) -> list[LecturaTelemetria]:
        """Filtra y ordena por fechaHora e identificador interno antes de paginar."""
        ...

    def disponible(self) -> bool:
        """Comprueba rápidamente si el almacenamiento responde."""
        ...


class RepositorioEnMemoria:
    """Datos de ejemplo para ejecutar el esqueleto del Avance 1."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._tipos: dict[tuple[str, str], TipoActivo] = {
            ("PL-001", "PL-001-PS-07"): "panel_solar",
            ("PL-041", "PL-041-TB-03"): "turbina",
        }
        self._lecturas = [
            LecturaTelemetria(
                plantaId="PL-001",
                activoId="PL-001-PS-07",
                fechaHora="2026-11-18T15:30:00Z",
                metrica="potencia",
                valor=0,
                unidad="W",
                estadoReportado="fuera_de_servicio",
            ),
            LecturaTelemetria(
                plantaId="PL-041",
                activoId="PL-041-TB-03",
                fechaHora="2026-11-24T05:10:00Z",
                metrica="potencia",
                valor=850,
                unidad="W",
            ),
        ]

    def guardar(self, lecturas: list[LecturaTelemetria]) -> None:
        with self._lock:
            self._lecturas.extend(lecturas)

    def consultar(
        self, filtros: FiltrosLecturas, *, offset: int, limite: int
    ) -> list[LecturaTelemetria]:
        with self._lock:
            coincidencias = [
                lectura
                for lectura in self._lecturas
                if lectura.plantaId == filtros.planta_id
                and (filtros.desde is None or lectura.fechaHora >= filtros.desde)
                and (filtros.hasta is None or lectura.fechaHora < filtros.hasta)
                and (filtros.activo_id is None or lectura.activoId == filtros.activo_id)
                and (filtros.metrica is None or lectura.metrica == filtros.metrica)
                and (
                    filtros.tipo_activo is None
                    or self._tipos.get((lectura.plantaId, lectura.activoId)) == filtros.tipo_activo
                )
            ]
        # El orden de inserción equivale al identificador interno de la demo.
        coincidencias.sort(key=lambda lectura: lectura.fechaHora)
        return coincidencias[offset : offset + limite]

    def disponible(self) -> bool:
        return True
