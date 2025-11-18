#!/bin/bash
# Deploy Trading Alert System to Google Cloud Run

set -e  # Exit on error

echo "=========================================="
echo "TRADING ALERT SYSTEM - GCP DEPLOYMENT"
echo "=========================================="
echo ""

# Get project ID
if command -v gcloud &> /dev/null; then
    DETECTED_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$DETECTED_PROJECT" ]; then
        PROJECT_ID="${GCP_PROJECT_ID:-$DETECTED_PROJECT}"
    else
        PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
    fi
else
    PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
fi

REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="trading-bot"  # Replace existing trading-bot service
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""

# Check if project ID is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "⚠️  WARNING: Project ID not set!"
    echo ""
    echo "Please either:"
    echo "  1. Set GCP_PROJECT_ID environment variable:"
    echo "     export GCP_PROJECT_ID=your-actual-project-id"
    echo ""
    echo "  2. Or set project in gcloud:"
    echo "     gcloud config set project YOUR_PROJECT_ID"
    echo ""
    read -p "Enter your project ID now (or press Ctrl+C to cancel): " PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        echo "❌ Project ID required. Exiting."
        exit 1
    fi
    IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found!"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "Step 1: Enabling required APIs..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID 2>/dev/null || true
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID 2>/dev/null || true
echo "✅ APIs enabled"
echo ""

echo "Step 2: Creating .gcloudignore..."
cat > .gcloudignore << 'EOF'
# Git
.git/
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Data files
data/*.db
data/*.csv
*.csv

# Logs
logs/
*.log

# Models
models/
*.pkl
*.json

# SQL files
sql/

# Documentation
docs/
*.md
!README.md

# Scripts
scripts/

# Old bot files
stat_arb/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Test files
tests/
.pytest_cache/
EOF
echo "✅ .gcloudignore created"
echo ""

echo "Step 3: Building container image..."
echo "This may take 2-5 minutes..."
# Ensure Dockerfile exists (copy from Dockerfile.alert if needed)
if [ -f "Dockerfile.alert" ] && [ ! -f "Dockerfile" ]; then
    cp Dockerfile.alert Dockerfile
    echo "✅ Created Dockerfile from Dockerfile.alert"
fi
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID

echo ""
echo "Step 4: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --min-instances=1 \
  --max-instances=1 \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --memory=1Gi \
  --cpu=1 \
  --timeout=3600 \
  --set-env-vars="LOG_LEVEL=INFO"

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo ""
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format="value(status.url)" 2>/dev/null || echo "Check Cloud Run console"
echo ""
echo "=========================================="
echo "NEXT STEP: Set Environment Variables"
echo "=========================================="
echo ""
echo "1. Go to: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "2. Click on '$SERVICE_NAME' service"
echo "3. Click 'Edit & Deploy New Revision'"
echo "4. Go to 'Variables & Secrets' tab"
echo "5. Add environment variables:"
echo ""
echo "   Required:"
echo "   - ALPHA_VANTAGE_API_KEY=your_api_key"
echo ""
echo "   Optional (with defaults):"
echo "   - DATABASE_URL=sqlite:///./data/trading_alerts.db"
echo "   - RSI_THRESHOLD=28.0"
echo "   - MIN_MARKET_CAP=5000000000"
echo "   - UPDATE_INTERVAL_MINUTES=5"
echo "   - LOG_LEVEL=INFO"
echo ""
echo "6. Click 'Deploy'"
echo ""
echo "View logs:"
echo "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --follow"
echo ""

