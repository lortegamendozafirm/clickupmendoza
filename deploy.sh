#!/bin/bash
# ============================================================================
# Script de deployment para Google Cloud Run
# ============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables (configurar según tu proyecto)
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="nexus-legal-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Verificar que gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI no está instalado${NC}"
    echo "Instalar desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${GREEN}=== Nexus Legal Integration - Deployment ===${NC}"
echo -e "${YELLOW}Proyecto:${NC} ${PROJECT_ID}"
echo -e "${YELLOW}Región:${NC} ${REGION}"
echo -e "${YELLOW}Servicio:${NC} ${SERVICE_NAME}"
echo ""

# Confirmar proyecto activo
read -p "¿Continuar con el deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelado"
    exit 0
fi

# 1. Configurar proyecto
echo -e "${YELLOW}[1/4] Configurando proyecto GCP...${NC}"
gcloud config set project ${PROJECT_ID}

# 2. Build imagen Docker
echo -e "${YELLOW}[2/4] Construyendo imagen Docker...${NC}"
gcloud builds submit --tag ${IMAGE_NAME}:latest

# 3. Deploy a Cloud Run
echo -e "${YELLOW}[3/4] Desplegando a Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars APP_ENV=production \
    --set-secrets "CLICKUP_API_TOKEN=CLICKUP_API_TOKEN:latest,CLICKUP_WEBHOOK_SECRET=CLICKUP_WEBHOOK_SECRET:latest,DATABASE_URL=DATABASE_URL:latest" \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300

# 4. Obtener URL del servicio
echo -e "${YELLOW}[4/4] Obteniendo URL del servicio...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment completado exitosamente!${NC}"
echo -e "${GREEN}URL del servicio:${NC} ${SERVICE_URL}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Configurar webhook en ClickUp apuntando a: ${SERVICE_URL}/webhooks/clickup"
echo "2. Configurar Cloud Scheduler para job nocturno (safety net)"
echo "3. Verificar logs: gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
