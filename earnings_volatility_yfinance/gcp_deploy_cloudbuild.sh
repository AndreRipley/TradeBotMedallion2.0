#!/bin/bash
# Alternative deployment script using Google Cloud Build (no local Docker required)
# This uses gcloud builds submit instead of local docker build/push

set -e  # Exit on error

# Configuration
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}GCP_PROJECT_ID not set.${NC}"
    read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
    export GCP_PROJECT_ID
fi

if [ -z "$GCP_REGION" ]; then
    echo -e "${YELLOW}GCP_REGION not set.${NC}"
    read -p "Enter your GCP Region (default: us-central1): " GCP_REGION
    GCP_REGION="${GCP_REGION:-us-central1}"
    export GCP_REGION
fi

PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${GCP_REGION}"
JOB_NAME="earnings-bot"
IMAGE_NAME="earnings-bot"
ARTIFACT_REGISTRY_REPO="trading-bot-repo"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-earnings-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Earnings Bot - GCP Deployment (Cloud Build)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Step 1: Setting GCP project...${NC}"
gcloud config set project "${PROJECT_ID}"
echo -e "${GREEN}✓ Project set to ${PROJECT_ID}${NC}"
echo ""

# Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}"

# Try to enable Cloud Scheduler (may fail due to org restrictions)
echo "Attempting to enable Cloud Scheduler API..."
if gcloud services enable cloudscheduler.googleapis.com --project="${PROJECT_ID}" 2>&1 | grep -q "ERROR\|not available"; then
    echo -e "${YELLOW}⚠ Cloud Scheduler API could not be enabled (may require Console or have org restrictions)${NC}"
    echo -e "${YELLOW}  You can enable it manually at: https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com?project=${PROJECT_ID}${NC}"
    echo -e "${YELLOW}  Or we'll skip scheduler setup and you can create jobs manually${NC}"
    SKIP_SCHEDULER=true
else
    echo -e "${GREEN}✓ Cloud Scheduler API enabled${NC}"
    SKIP_SCHEDULER=false
fi

echo -e "${GREEN}✓ Core APIs enabled${NC}"
echo ""

# Create Artifact Registry repository (if it doesn't exist)
echo -e "${YELLOW}Step 3: Setting up Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe "${ARTIFACT_REGISTRY_REPO}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create "${ARTIFACT_REGISTRY_REPO}" \
        --repository-format=docker \
        --location="${REGION}" \
        --project="${PROJECT_ID}"
    echo -e "${GREEN}✓ Artifact Registry repository created${NC}"
else
    echo -e "${GREEN}✓ Artifact Registry repository already exists${NC}"
fi
echo ""

# Build and push using Cloud Build
echo -e "${YELLOW}Step 4: Building Docker image with Cloud Build...${NC}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${IMAGE_NAME}:latest"

# Use cloudbuild.yaml if it exists, otherwise use --tag (simpler)
if [ -f "earnings_volatility_yfinance/cloudbuild.yaml" ]; then
    # Update image URI in cloudbuild.yaml temporarily
    sed "s|_IMAGE_URI:.*|_IMAGE_URI: '${IMAGE_URI}'|" earnings_volatility_yfinance/cloudbuild.yaml > /tmp/cloudbuild.yaml
    echo "Using cloudbuild.yaml..."
    gcloud builds submit \
        --config="/tmp/cloudbuild.yaml" \
        --project="${PROJECT_ID}" \
        --substitutions="_IMAGE_URI=${IMAGE_URI}"
else
    # Simple build using --tag (requires Dockerfile in current directory)
    echo "Using --tag flag (Dockerfile must be in current directory)..."
    # Copy Dockerfile to root temporarily for build context
    cp earnings_volatility_yfinance/Dockerfile ./Dockerfile.tmp
    gcloud builds submit \
        --tag "${IMAGE_URI}" \
        --project="${PROJECT_ID}" \
        --dockerfile=./Dockerfile.tmp
    rm -f ./Dockerfile.tmp
fi

echo -e "${GREEN}✓ Docker image built and pushed${NC}"
echo ""

# Create service account (if it doesn't exist)
echo -e "${YELLOW}Step 5: Setting up service account...${NC}"
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create earnings-bot-sa \
        --display-name="Earnings Bot Service Account" \
        --project="${PROJECT_ID}"
    
    # Grant necessary permissions
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor"
    
    # Grant permission to invoke Cloud Run Jobs
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/run.invoker"
    
    echo -e "${GREEN}✓ Service account created and permissions granted${NC}"
else
    echo -e "${GREEN}✓ Service account already exists${NC}"
fi
echo ""

# Create or update Cloud Run Job
echo -e "${YELLOW}Step 6: Creating/Updating Cloud Run Job...${NC}"
if gcloud run jobs describe "${JOB_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "Updating existing Cloud Run Job..."
    gcloud run jobs update "${JOB_NAME}" \
        --image="${IMAGE_URI}" \
        --region="${REGION}" \
        --service-account="${SERVICE_ACCOUNT}" \
        --max-retries=1 \
        --task-timeout=30m \
        --memory=2Gi \
        --cpu=2 \
        --project="${PROJECT_ID}" \
        --set-secrets="ALPACA_KEY=alpaca-key:latest,ALPACA_SECRET=alpaca-secret:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,API_NINJAS_KEY=api-ninjas-key:latest" \
        --set-env-vars="ALPACA_PAPER=true"
    echo -e "${GREEN}✓ Cloud Run Job updated${NC}"
else
    echo "Creating new Cloud Run Job..."
    gcloud run jobs create "${JOB_NAME}" \
        --image="${IMAGE_URI}" \
        --region="${REGION}" \
        --service-account="${SERVICE_ACCOUNT}" \
        --max-retries=1 \
        --task-timeout=30m \
        --memory=2Gi \
        --cpu=2 \
        --project="${PROJECT_ID}" \
        --set-secrets="ALPACA_KEY=alpaca-key:latest,ALPACA_SECRET=alpaca-secret:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,API_NINJAS_KEY=api-ninjas-key:latest" \
        --set-env-vars="ALPACA_PAPER=true"
    echo -e "${GREEN}✓ Cloud Run Job created${NC}"
fi
echo ""

# Create Cloud Scheduler jobs (same as original script)
if [ "$SKIP_SCHEDULER" = true ]; then
    echo -e "${YELLOW}Step 7: Skipping Cloud Scheduler (API not available)${NC}"
    echo -e "${YELLOW}  You can create scheduler jobs manually via Console or enable the API first${NC}"
    echo ""
else
    echo -e "${YELLOW}Step 7: Creating Cloud Scheduler jobs...${NC}"

ENTRY_JOB_NAME="earnings-entry"
ENTRY_SCHEDULE="15 15 * * 1-5"
ENTRY_TIMEZONE="America/New_York"

if gcloud scheduler jobs describe "${ENTRY_JOB_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "Updating entry scheduler job..."
    gcloud scheduler jobs update http "${ENTRY_JOB_NAME}" \
        --location="${REGION}" \
        --schedule="${ENTRY_SCHEDULE}" \
        --time-zone="${ENTRY_TIMEZONE}" \
        --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --project="${PROJECT_ID}" \
        --message-body='{"overrides":{"containerOverrides":[{"args":["--mode","entry"]}]}}' \
        --headers="Content-Type=application/json" \
        --oidc-token-audience="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"
    echo -e "${GREEN}✓ Entry scheduler job updated${NC}"
else
    echo "Creating entry scheduler job..."
    gcloud scheduler jobs create http "${ENTRY_JOB_NAME}" \
        --location="${REGION}" \
        --schedule="${ENTRY_SCHEDULE}" \
        --time-zone="${ENTRY_TIMEZONE}" \
        --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --project="${PROJECT_ID}" \
        --message-body='{"overrides":{"containerOverrides":[{"args":["--mode","entry"]}]}}' \
        --headers="Content-Type=application/json" \
        --oidc-token-audience="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"
    echo -e "${GREEN}✓ Entry scheduler job created${NC}"
fi

EXIT_JOB_NAME="earnings-exit"
EXIT_SCHEDULE="45 9 * * 1-5"

if gcloud scheduler jobs describe "${EXIT_JOB_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" &> /dev/null; then
    echo "Updating exit scheduler job..."
    gcloud scheduler jobs update http "${EXIT_JOB_NAME}" \
        --location="${REGION}" \
        --schedule="${EXIT_SCHEDULE}" \
        --time-zone="${ENTRY_TIMEZONE}" \
        --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --project="${PROJECT_ID}" \
        --message-body='{"overrides":{"containerOverrides":[{"args":["--mode","exit"]}]}}' \
        --headers="Content-Type=application/json" \
        --oidc-token-audience="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"
    echo -e "${GREEN}✓ Exit scheduler job updated${NC}"
else
    echo "Creating exit scheduler job..."
    gcloud scheduler jobs create http "${EXIT_JOB_NAME}" \
        --location="${REGION}" \
        --schedule="${EXIT_SCHEDULE}" \
        --time-zone="${ENTRY_TIMEZONE}" \
        --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
        --http-method=POST \
        --oidc-service-account-email="${SERVICE_ACCOUNT}" \
        --project="${PROJECT_ID}" \
        --message-body='{"overrides":{"containerOverrides":[{"args":["--mode","exit"]}]}}' \
        --headers="Content-Type=application/json" \
        --oidc-token-audience="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"
    echo -e "${GREEN}✓ Exit scheduler job created${NC}"
fi
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run setup_secrets.py to configure secrets in Secret Manager"
echo "2. Test the job manually:"
echo "   gcloud run jobs execute ${JOB_NAME} --region=${REGION} --args='--mode,entry'"
echo "3. View logs:"
echo "   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}\" --limit=50"
echo ""

