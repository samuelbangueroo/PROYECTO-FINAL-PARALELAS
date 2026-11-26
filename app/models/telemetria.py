from sqlalchemy import String, Float, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime
from uuid import UUID, uuid4
from app.models.lectura import ESTADOS

class LecturaTelemetria(Base):
    __tablename__ = "lecturas"
    __table_args__ = (
        Index("ix_lecturas_planta_activo_fecha", "plantaId", "activoId", "fechaHora"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plantaId: Mapped[str] = mapped_column(String(100), nullable=False)
    fechaHora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activoId: Mapped[str] = mapped_column(String(100), nullable=False)
    metrica: Mapped[str] = mapped_column(String(250), nullable=False)
    valor: Mapped[float | None] = mapped_column(Float, nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estadoReportado: Mapped[str | None] = mapped_column(
    Enum(*ESTADOS, name="estado_reportado"), nullable=True)