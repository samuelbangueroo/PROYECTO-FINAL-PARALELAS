# PROYECTO-FINAL-PARALELAS

## API de Telemetría · Avance 1

Desde la raíz del repositorio, con Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

El contrato se sirve en `/openapi.yaml` y Swagger UI está en `/docs`.

```bash
curl -i http://localhost:8080/health
curl -i -X POST http://localhost:8080/telemetria \
  -H 'Content-Type: application/json' \
  -d '{"lecturas":[{"plantaId":"PL-001","activoId":"PL-001-PS-07","fechaHora":"2026-11-19T15:30:00Z","metrica":"potencia","valor":250,"unidad":"W"}]}'
curl -i 'http://localhost:8080/telemetria/PL-001?desde=2026-11-19T00:00:00Z&metrica=potencia&limit=10'
```

La aplicación arranca con un repositorio de demostración en memoria.
Las lecturas añadidas se pierden al reiniciar. El filtro por tipo conoce
los dos activos de ejemplo del contrato. La ingesta de demostración acepta
lecturas válidas según el esquema y reporta el modo ejecutado como
`secuencial` con un worker. Inventario y el procesamiento paralelo
corresponden al Avance 2.

### Integración con PostgreSQL

La presentación está en `app/routers` y `app/schemas`, y el servicio que
coordina la ingesta y la consulta está en `app/services`.

La persona a cargo de PostgreSQL puede implementar `RepositorioTelemetria`
en `app/repositories/telemetria.py` y pasar su implementación a
`crear_app(repositorio)` en el punto de arranque. La interfaz acuerda tres
operaciones:

- `guardar(lecturas)` persiste el lote completo en una transacción.
- `consultar(filtros, offset=..., limite=...)` aplica los filtros y ordena
  por fecha e ID interno antes de paginar. La API pide hasta 201 filas
  para detectar si hay otra página y devuelve como máximo 200.
- `disponible()` comprueba rápidamente la conexión que usa el repositorio.
  Los fallos de almacenamiento se traducen a `RepositorioNoDisponible`
  para que la API devuelva el `503` del contrato.
