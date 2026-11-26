# Clúster EKS local con Floci

Esta guía reproduce el punto 5 del proyecto Voltrix Energy. Floci crea un clúster EKS emulado en el equipo local y usa K3s para ejecutar Kubernetes. La prueba queda completa cuando Floci reporta el clúster `ACTIVE` y `kubectl` muestra un nodo `Ready`. [Floci EKS](https://github.com/floci-io/floci/blob/2.5.0/docs/services/eks.md#modes)

## 1. Preparar el entorno

Abre Docker Desktop con el motor de contenedores Linux activo. En el equipo de la demostración se usó Windows con WSL 2. Ejecuta los siguientes comandos en la misma sesión de PowerShell, desde la raíz del repositorio, donde está la carpeta `floci`.

```powershell
Set-Location 'C:\Users\HP\Desktop\proyectofinalinfra\PROYECTO-FINAL-PARALELAS'
docker info --format '{{.OSType}}'
docker compose version
```

Usa la ruta de tu clon si es diferente. El primer comando de Docker debe imprimir `linux`.

## 2. Iniciar Floci

```powershell
docker compose -f .\floci\compose.yml up -d
$floci = 'http://127.0.0.1:4566'
$cluster = 'voltrix-eks'
Invoke-RestMethod "$floci/_floci/health"
```

Si Floci todavía está arrancando, repite la última consulta. `compose.yml` fija la imagen de Floci en `2.5.0`, publica su API en el puerto local `4566` y le da acceso al motor de Docker para iniciar K3s. La variable `FLOCI_SERVICES_EKS_MOCK` está en `false` para levantar Kubernetes y poder consultarlo. [Configuración de Floci EKS](https://github.com/floci-io/floci/blob/2.5.0/docs/services/eks.md#modes)

## 3. Crear el clúster

Consulta primero qué clústeres tiene el emulador.

```powershell
(Invoke-RestMethod "$floci/clusters").clusters
```

Si `voltrix-eks` ya aparece, pasa a la verificación. Si la lista está vacía o el nombre no aparece, ejecuta este bloque una vez.

```powershell
$solicitud = @{
    name = $cluster
    roleArn = 'arn:aws:iam::000000000000:role/eks-role'
    resourcesVpcConfig = @{ subnetIds = @(); securityGroupIds = @() }
} | ConvertTo-Json

Invoke-RestMethod "$floci/clusters" -Method Post -ContentType 'application/json' -Body $solicitud
```

PowerShell envía la solicitud HTTP a Floci en `127.0.0.1`. El `roleArn` del ejemplo identifica un rol simulado. La solicitud se hace con PowerShell y el paso siguiente usa el `kubectl` incluido en el contenedor de K3s. [API de EKS en Floci](https://github.com/floci-io/floci/blob/2.5.0/docs/services/eks.md#examples)

## 4. Verificar y guardar la evidencia

Consulta el estado de Floci. Si todavía aparece `CREATING`, repite la consulta hasta ver `ACTIVE`. La primera creación puede tardar mientras Docker descarga la imagen de K3s.

```powershell
$estado = (Invoke-RestMethod "$floci/clusters/$cluster").cluster
$estado | Select-Object name, status, endpoint
```

Después consulta los nodos. `docker exec` ejecuta `kubectl` dentro del contenedor del clúster, de modo que la consulta llega al Kubernetes de esta demo. Busca `Ready` en la columna `STATUS`.

```powershell
docker exec floci-aws-eks-voltrix-eks kubectl get nodes -o wide
```

La evidencia incluida en `floci/evidencia.txt` muestra `voltrix-eks ACTIVE` en `https://localhost:6500` y un nodo `Ready` con rol `control-plane`. El puerto de Kubernetes se asigna al crear el clúster y puede variar si el `6500` está ocupado.

Una vez que veas ambos resultados, puedes actualizar `floci/evidencia.txt` con este bloque. Las dos salidas se guardan juntas en UTF-8.

```powershell
$estado = (Invoke-RestMethod "$floci/clusters/$cluster").cluster
if ($estado.status -ne 'ACTIVE') { throw "Estado del clúster: $($estado.status)" }

$nodos = docker exec floci-aws-eks-voltrix-eks kubectl get nodes -o wide
if ($LASTEXITCODE -ne 0 -or -not ($nodos | Select-String '\sReady\s')) {
    throw 'kubectl todavía no muestra un nodo Ready.'
}

$resumen = ($estado | Select-Object name, status, endpoint | Format-Table | Out-String).Trim()
@($resumen; ''; $nodos) | Set-Content -LiteralPath .\floci\evidencia.txt -Encoding utf8
Get-Content -LiteralPath .\floci\evidencia.txt
```

Si Floci no responde o el clúster aparece en `FAILED`, revisa los registros.

```powershell
docker compose -f .\floci\compose.yml logs --tail 80 floci
docker ps -a --filter 'name=floci-aws-eks-voltrix-eks'
```

## 5. Repetir la prueba desde cero

Cuando quieras repetir la prueba, hazlo desde la misma carpeta con Floci todavía en ejecución. Conserva `compose.yml`, este README y la evidencia. Puedes respaldar `evidencia.txt` en la carpeta superior antes de regenerarla. El `DELETE` elimina el clúster local y las cargas que hayas desplegado dentro de él. [Operación DeleteCluster](https://github.com/floci-io/floci/blob/2.5.0/docs/services/eks.md#supported-operations)

*OJO VIVO! si usted sigue en la misma TERMINAL los dos primeros comandos ($floci, $cluster) SOBRAN*
*Si les ejecuta tampoco se daña nada, pero puede ahorrar tiempo!!!*

```powershell
$floci = 'http://127.0.0.1:4566'
$cluster = 'voltrix-eks'
Invoke-RestMethod "$floci/clusters/$cluster" -Method Delete
(Invoke-RestMethod "$floci/clusters").clusters
```

Cuando `voltrix-eks` ya no aparezca en la lista, baja el proyecto Compose de Floci.

```powershell
docker compose -f .\floci\compose.yml down
```

Vuelve al paso 2 y sigue hasta obtener `ACTIVE` y `Ready` otra vez. Puedes reutilizar las imágenes descargadas para acelerar el ensayo. El despliegue de Telemetría en EC2 se administra aparte.
