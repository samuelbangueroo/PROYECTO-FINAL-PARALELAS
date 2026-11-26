from typing import Literal

EstadoReportado = Literal["operativo", "en_mantenimiento", "fuera_de_servicio"]
Modo = Literal["secuencial", "paralelo"]
TipoActivo = Literal["panel_solar", "turbina", "banco_baterias"]