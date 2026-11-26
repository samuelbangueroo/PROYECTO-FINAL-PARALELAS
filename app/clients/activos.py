"""Validación preliminar mientras se desarrolla API de Inventario de Activos"""
class ClienteActivosFalso:
    _tipos = {
        ("PL-001", "PL-001-PS-07"): "panel_solar",
        ("PL-041", "PL-041-TB-03"): "turbina",
    }

    def ids_por_tipo(self, planta_id: str, tipo: TipoActivo) -> list[str]:
        return [a for (p, a), t in self._tipos.items() if p == planta_id and t == tipo]