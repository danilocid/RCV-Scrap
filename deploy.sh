#!/bin/bash

# Script de despliegue manual a Cloud Run
# Uso: bash deploy.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando despliegue a Cloud Run${NC}"

# Verificar que gcloud esté instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI no está instalado${NC}"
    echo "Instala desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Variables (modificar según tu proyecto)
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="rcv-scraper"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${YELLOW}📋 Configuración:${NC}"
echo "  Project ID: ${PROJECT_ID}"
echo "  Service: ${SERVICE_NAME}"
echo "  Region: ${REGION}"
echo ""

# Confirmar
read -p "¿Continuar con el despliegue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️  Despliegue cancelado${NC}"
    exit 0
fi

# Paso 1: Habilitar APIs necesarias
echo -e "${YELLOW}🔧 Habilitando APIs necesarias...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Paso 2: Build de la imagen Docker
echo -e "${YELLOW}🐳 Construyendo imagen Docker...${NC}"
docker build -t ${IMAGE_NAME}:latest .

# Paso 3: Push a Container Registry
echo -e "${YELLOW}📤 Subiendo imagen a GCR...${NC}"
docker push ${IMAGE_NAME}:latest

# Paso 4: Deploy a Cloud Run
echo -e "${YELLOW}☁️  Desplegando a Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 5 \
    --allow-unauthenticated \
    --set-env-vars AMBIENTE=PROD

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Despliegue completado exitosamente!${NC}"
echo ""
echo -e "${GREEN}📡 URL del servicio:${NC}"
echo "   ${SERVICE_URL}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Configura las variables de entorno en Cloud Run:${NC}"
echo "   - SII_RUT"
echo "   - SII_CLAVE"
echo ""
echo "Configúralas con:"
echo "gcloud run services update ${SERVICE_NAME} --region ${REGION} \\"
echo "  --set-env-vars SII_RUT=tu-rut,SII_CLAVE=tu-clave"
echo ""
echo -e "${GREEN}🔍 Prueba el servicio:${NC}"
echo "curl ${SERVICE_URL}/health"
