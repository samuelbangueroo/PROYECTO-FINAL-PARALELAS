from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import SessionLocal
from app.models.lectura import LecturaTelemetria as LecturaModel
from app.schemas import LecturaTelemetria


class RepositorioNoDisponible(Exception):
    """El almacenamiento no pudo completar la operación."""


@dataclass(frozen=True)
class FiltrosLecturas:
    planta_id: str
    desde: datetime | None
    hasta: datetime | None
    activos_ids: list[str] | None  # ya resuelto por el servicio (activo_id y/o tipo_activo)
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


def _a_schema(fila: LecturaModel) -> LecturaTelemetria:
    """Convierte una fila a schema.

    estadoReportado solo se pasa si existe: el validador del schema rechaza
    un None explícito, y una columna NULL significa "no reportado".
    """
    datos = dict(
        plantaId=fila.plantaId,
        activoId=fila.activoId,
        fechaHora=fila.fechaHora,
        metrica=fila.metrica,
        valor=fila.valor,
        unidad=fila.unidad,
    )
    if fila.estadoReportado is not None:
        datos["estadoReportado"] = fila.estadoReportado
    return LecturaTelemetria(**datos)


class RepositorioPostgres:
    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def guardar(self, lecturas: list[LecturaTelemetria]) -> None:
        if not lecturas:
            return
        try:
            # begin() abre una transacción: o se guarda todo el lote o nada.
            with self._session_factory.begin() as db:
                db.execute(
                    insert(LecturaModel),
                    [lectura.model_dump() for lectura in lecturas],
                )
        except SQLAlchemyError as exc:
            raise RepositorioNoDisponible("No se pudo guardar el lote") from exc

    def consultar(
        self, filtros: FiltrosLecturas, *, offset: int, limite: int
    ) -> list[LecturaTelemetria]:
        if filtros.activos_ids is not None and not filtros.activos_ids:
            return []  # el tipo pedido no tiene activos: nada que consultar

        stmt = select(LecturaModel).where(LecturaModel.plantaId == filtros.planta_id)
        if filtros.desde is not None:
            stmt = stmt.where(LecturaModel.fechaHora >= filtros.desde)
        if filtros.hasta is not None:
            stmt = stmt.where(LecturaModel.fechaHora < filtros.hasta)
        if filtros.metrica is not None:
            stmt = stmt.where(LecturaModel.metrica == filtros.metrica)
        if filtros.activos_ids is not None:
            stmt = stmt.where(LecturaModel.activoId.in_(filtros.activos_ids))

        stmt = (
            stmt.order_by(LecturaModel.fechaHora, LecturaModel.id)
            .offset(offset)
            .limit(limite)
        )

        try:
            with self._session_factory() as db:
                return [_a_schema(fila) for fila in db.scalars(stmt)]
        except SQLAlchemyError as exc:
            raise RepositorioNoDisponible("No se pudo consultar") from exc

    def disponible(self) -> bool:
        try:
            with self._session_factory() as db:
                db.execute(select(1))
            return True
        except SQLAlchemyError:
            return False