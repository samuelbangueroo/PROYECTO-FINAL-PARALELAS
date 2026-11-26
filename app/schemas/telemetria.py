import re
from datetime import datetime
from typing import Annotated, Literal, Self
from app.core.tipos import EstadoReportado, Modo, TipoActivo

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    FiniteFloat,
    StringConstraints,
    model_validator,
)

Identificador = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]



def validar_formato_fecha(valor: object) -> object:
    if isinstance(valor, datetime):
        return valor
    if not isinstance(valor, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})",
        valor,
    ):
        raise ValueError("debe ser una fecha RFC 3339 con zona horaria")
    return valor


def validar_numero(valor: object) -> object:
    if type(valor) not in (int, float):
        raise ValueError("debe ser un número JSON")
    return valor


def validar_id(valor: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
        raise ValueError("debe contener únicamente letras ASCII, números, guiones o guiones bajos")
    return valor


Identificador = Annotated[Identificador, AfterValidator(validar_id)]
FechaRFC3339 = Annotated[AwareDatetime, BeforeValidator(validar_formato_fecha)]
NumeroJSON = Annotated[FiniteFloat, BeforeValidator(validar_numero)]


class LecturaTelemetria(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plantaId: Identificador
    activoId: Identificador
    fechaHora: FechaRFC3339
    metrica: str
    valor: NumeroJSON
    unidad: str
    estadoReportado: EstadoReportado | None = None

    @model_validator(mode="after")
    def validar_estado_opcional(self) -> Self:
        if "estadoReportado" in self.model_fields_set and self.estadoReportado is None:
            raise ValueError("estadoReportado debe ser un estado válido cuando se incluye")
        if self.valor is None and self.estadoReportado != "fuera_de_servicio":
            raise ValueError("valor solo puede faltar si estadoReportado es 'fuera_de_servicio'")
        return self


class LoteTelemetria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lecturas: list[LecturaTelemetria] = Field(min_length=1)


class MetricasProcesamiento(BaseModel):
    modo: Modo
    workers: int = Field(ge=1)
    elementos: int = Field(ge=0)
    duracionMs: int = Field(ge=0)


class ResultadoLote(BaseModel):
    recibidas: int = Field(ge=0)
    procesadas: int = Field(ge=0)
    descartadas: int = Field(ge=0)
    metricas: MetricasProcesamiento


class Salud(BaseModel):
    estado: Literal["disponible", "no_disponible"]
    baseDatos: Literal["ok", "error"]
    tiempoActivoSeg: int = Field(ge=0)
