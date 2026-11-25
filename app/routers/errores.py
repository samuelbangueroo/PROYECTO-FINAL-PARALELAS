from fastapi import Request
from fastapi.responses import JSONResponse


class SolicitudInvalida(Exception):
    def __init__(self, campo: str, problema: str) -> None:
        self.detalle = {"campo": campo, "problema": problema}


def respuesta_error(
    request: Request,
    estado: int,
    codigo: str,
    mensaje: str,
    *,
    detalles: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    contenido = {"codigo": codigo, "mensaje": mensaje, "requestId": request.state.request_id}
    if detalles:
        contenido["detalles"] = detalles
    return JSONResponse(contenido, status_code=estado, headers=headers)
