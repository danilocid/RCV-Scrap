# 🚀 Guía de Despliegue a Google Cloud Run

Esta guía describe cómo desplegar el RCV Scraper en Google Cloud Run.

## 📋 Pre-requisitos

### 1. Cuenta de Google Cloud

- Proyecto de GCP activo
- Facturación habilitada
- gcloud CLI instalado: https://cloud.google.com/sdk/docs/install

### 2. Configuración Inicial

```bash
# Instalar gcloud CLI (Windows)
# Descarga desde: https://cloud.google.com/sdk/docs/install

# Inicializar gcloud
gcloud init

# Configurar proyecto
gcloud config set project TU_PROJECT_ID

# Autenticarse
gcloud auth login
gcloud auth configure-docker
```

### 3. Habilitar APIs Necesarias

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 🎯 Métodos de Despliegue

### Opción 1: Trigger Automático (Recomendado - Repositorio Conectado)

Si Cloud Run está conectado a tu repositorio Git, el despliegue es automático:

```bash
# Simplemente haz push al repositorio
git add .
git commit -m "Update scraper"
git push origin main
```

**El trigger automático:**

- ✅ Detecta cambios en el repositorio
- ✅ Ejecuta `cloudbuild.yaml` automáticamente
- ✅ Build, push y deploy sin intervención manual
- ✅ Notificaciones de éxito/error

**Configuración del Trigger:**

1. Cloud Console → Cloud Build → Triggers
2. Verificar que el trigger esté conectado a tu repo
3. Rama: `main` o `master`
4. Config: `cloudbuild.yaml`

**Tiempo estimado:** 10-15 minutos desde el push

---

### Opción 2: Cloud Build Manual

Despliegue manual sin usar el trigger:

```bash
# Desde el directorio del proyecto
gcloud builds submit --config cloudbuild.yaml
```

**Ventajas:**

- ✅ Control total del momento de despliegue
- ✅ Útil para testing antes de merge
- ✅ No requiere Docker local

**Tiempo estimado:** 10-15 minutos

---

### Opción 3: Script Manual

Usando el script `deploy.sh`:

```bash
# Dar permisos de ejecución (Linux/Mac)
chmod +x deploy.sh

# Ejecutar
bash deploy.sh
```

**Ventajas:**

- ✅ Control paso a paso
- ✅ Ideal para desarrollo
- ✅ Fácil de customizar

---

### Opción 4: Comandos Manuales

Control total del proceso:

```bash
# 1. Build de la imagen
docker build -t gcr.io/TU_PROJECT_ID/rcv-scraper:latest .

# 2. Push a Container Registry
docker push gcr.io/TU_PROJECT_ID/rcv-scraper:latest

# 3. Deploy a Cloud Run
gcloud run deploy rcv-scraper \
  --image gcr.io/TU_PROJECT_ID/rcv-scraper:latest \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 5 \
  --allow-unauthenticated
```

---

## 🔐 Configuración de Variables de Entorno

**CRÍTICO:** Las credenciales del SII deben configurarse en Cloud Run (NO en el repositorio).

### Configurar desde Cloud Console (Más Seguro)

1. Ir a: https://console.cloud.google.com/run
2. Seleccionar servicio `rcv-scraper`
3. Click en **"EDIT & DEPLOY NEW REVISION"**
4. **Variables y Secretos** → **Add Variable**
5. Agregar:
   - `SII_RUT`: `12345678-9`
   - `SII_CLAVE`: `tu_clave_sii`
   - `AMBIENTE`: `PROD`
6. Click **DEPLOY**

### Configurar desde gcloud CLI

Las credenciales del SII deben configurarse en Cloud Run:

```bash
gcloud run services update rcv-scraper \
  --region us-central1 \
  --set-env-vars SII_RUT=12345678-9,SII_CLAVE=tu_clave,AMBIENTE=PROD
```

O desde la consola web:

1. Ir a Cloud Run → rcv-scraper
2. Click en "EDIT & DEPLOY NEW REVISION"
3. Variables y Secretos → Agregar variable
   - `SII_RUT`: Tu RUT con guion
   - `SII_CLAVE`: Tu contraseña SII
   - `AMBIENTE`: PROD

---

## ⚙️ Configuración de Recursos

### Recursos Recomendados

| Recurso       | Valor      | Razón                                 |
| ------------- | ---------- | ------------------------------------- |
| **Memoria**   | 2 GiB      | Playwright necesita ~1.5GB + overhead |
| **CPU**       | 2 vCPU     | Mejora velocidad de navegación        |
| **Timeout**   | 3600s (1h) | Extracciones grandes pueden tardar    |
| **Instances** | 1-5        | Evita sobrecargar portal SII          |

### Modificar Recursos

```bash
gcloud run services update rcv-scraper \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4 \
  --timeout 3600 \
  --min-instances 0 \
  --max-instances 5
```

---

## 🧪 Verificar Despliegue

### 1. Health Check

```bash
# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe rcv-scraper --region us-central1 --format 'value(status.url)')

# Verificar salud
curl $SERVICE_URL/health
```

Respuesta esperada:

```json
{ "status": "ok", "timestamp": "2025-12-26T10:30:00" }
```

### 2. Probar Extracción

```bash
# Iniciar extracción del período actual
curl -X POST $SERVICE_URL/extraer

# Consultar estado
curl $SERVICE_URL/estado
```

### 3. Ver Logs

```bash
# Logs en tiempo real
gcloud run services logs tail rcv-scraper --region us-central1

# Logs recientes
gcloud run services logs read rcv-scraper --region us-central1 --limit 50
```

---

## 💰 Costos Estimados

### Calculadora de Costos

**Configuración:** 2 vCPU, 2 GiB RAM, 1 hora timeout

| Concepto        | Costo Unitario           | Costo por Ejecución |
| --------------- | ------------------------ | ------------------- |
| CPU (2 vCPU)    | $0.00002400/vCPU-segundo | ~$0.17              |
| Memoria (2 GiB) | $0.00000250/GiB-segundo  | ~$0.018             |
| Requests        | $0.40/millón             | ~$0.0004            |
| **Total**       | -                        | **~$0.19**          |

**Estimación mensual (30 extracciones):** $5.70

**Notas:**

- Free tier: 2 millones de requests, 360,000 vCPU-segundos, 180,000 GiB-segundos/mes
- Costos reales dependen del tiempo de ejecución
- Storage de Container Registry adicional: ~$0.026/GB/mes

---

## 🔒 Seguridad y Mejores Prácticas

### 1. Gestión de Secretos

**Opción recomendada:** Secret Manager

```bash
# Crear secretos
echo -n "12345678-9" | gcloud secrets create sii-rut --data-file=-
echo -n "tu_clave" | gcloud secrets create sii-clave --data-file=-

# Asignar permisos
gcloud secrets add-iam-policy-binding sii-rut \
  --member serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor

# Configurar en Cloud Run
gcloud run services update rcv-scraper \
  --region us-central1 \
  --set-secrets SII_RUT=sii-rut:latest,SII_CLAVE=sii-clave:latest
```

### 2. Autenticación

Para producción, habilita autenticación:

```bash
# Requiere autenticación
gcloud run services update rcv-scraper \
  --region us-central1 \
  --no-allow-unauthenticated

# Invocar con identidad
gcloud run services proxy rcv-scraper --region us-central1
```

### 3. Límites y Throttling

```bash
# Configurar concurrencia
gcloud run services update rcv-scraper \
  --region us-central1 \
  --concurrency 1 \
  --max-instances 3
```

---

## 🐛 Troubleshooting

### Error: "Memory limit exceeded"

**Solución:** Aumentar memoria

```bash
gcloud run services update rcv-scraper --memory 4Gi
```

### Error: "Timeout"

**Solución:** Aumentar timeout

```bash
gcloud run services update rcv-scraper --timeout 3600
```

### Error: "Container failed to start"

**Diagnóstico:**

1. Revisar logs: `gcloud run services logs read rcv-scraper`
2. Verificar que Playwright esté instalado en el Dockerfile
3. Confirmar que el puerto 8080 esté expuesto

### Error: "Credenciales incorrectas"

**Solución:**

1. Verificar variables de entorno en Cloud Run console
2. Confirmar que `SII_RUT` incluya el guion: `12345678-9`
3. Revisar que `AMBIENTE=PROD`

---

## 🔄 Actualizar Servicio

### Con Repositorio Conectado (Automático)

```bash
# Hacer cambios en el código
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# Cloud Build se ejecuta automáticamente
# Verifica el progreso en: https://console.cloud.google.com/cloud-build/builds
```

### Sin Repositorio (Manual)

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Update Directo

```bash
# Rebuild imagen
docker build -t gcr.io/TU_PROJECT_ID/rcv-scraper:latest .
docker push gcr.io/TU_PROJECT_ID/rcv-scraper:latest

# Actualizar servicio
gcloud run services update rcv-scraper \
  --image gcr.io/TU_PROJECT_ID/rcv-scraper:latest
```

---

## 📊 Monitoreo

### 1. Cloud Console

- **Cloud Run Dashboard:** https://console.cloud.google.com/run
- Métricas: Requests, latencia, errores, uso de CPU/memoria

### 2. Logs Explorer

```bash
# Filtrar errores
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 50

# Logs específicos
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rcv-scraper"
```

### 3. Alertas (Opcional)

Configura alertas para:

- Errores 5xx > 1%
- Latencia > 60s
- Uso de memoria > 90%

---

## 🧹 Limpieza

Para eliminar el servicio:

```bash
# Borrar servicio Cloud Run
gcloud run services delete rcv-scraper --region us-central1

# Borrar imágenes
gcloud container images delete gcr.io/TU_PROJECT_ID/rcv-scraper:latest

# Borrar secretos
gcloud secrets delete sii-rut
gcloud secrets delete sii-clave
```

---

## 📚 Recursos Adicionales

- **Documentación Cloud Run:** https://cloud.google.com/run/docs
- **Cloud Build Triggers:** https://cloud.google.com/build/docs/automating-builds/create-manage-triggers
- **Playwright en Docker:** https://playwright.dev/docs/docker
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Best Practices:** https://cloud.google.com/run/docs/tips
- **Secret Manager:** https://cloud.google.com/secret-manager/docs

---

## 🆘 Soporte

Si encuentras problemas:

1. Revisa logs: `gcloud run services logs tail rcv-scraper`
2. Verifica configuración: `gcloud run services describe rcv-scraper`
3. Consulta troubleshooting section arriba
4. Verifica estado del portal SII (puede estar en mantenimiento)
