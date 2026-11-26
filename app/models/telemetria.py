from sqlalchemy import String, Float, DateTime, Enum 
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime
from uuid import UUID
from ..schemas import EstadoReportado

class LecturaTelemetria(Base):
    __tablename__ = "lecturas"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    plantaId: Mapped[str] = mapped_column(String(100), nullable=False)
    fechaHora: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    activoId: Mapped[str] = mapped_column(String(100), nullable=False)
    metrica: Mapped[str] = mapped_column(String(250), nullable=False)
    valor: Mapped[float] = mapped_column(Float)
    unidad: Mapped[str] = mapped_column(String(50))
    estadoReportado: Mapped[str] = mapped_column(Enum(EstadoReportado))