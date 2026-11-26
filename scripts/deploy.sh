#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Falta .env con la configuración del servidor."
    exit 1
fi

: "${API_IMAGE:?Debes indicar la imagen publicada por GitHub}"
export API_IMAGE

compose() {
    sudo --preserve-env=API_IMAGE docker compose \
        -f docker-compose.yml -f compose.ec2.yml "$@"
}

compose config --quiet
compose pull
compose up -d --no-build

echo "Esperando respuesta de la API..."
for intento in $(seq 1 30); do
    if curl --fail --silent --max-time 3 \
        http://localhost:8080/health > /dev/null; then
        echo "Despliegue verificado."
        compose ps
        exit 0
    fi
    sleep 2
done

echo "Falló la comprobación de salud."
compose ps
compose logs --tail=80 api
exit 1
