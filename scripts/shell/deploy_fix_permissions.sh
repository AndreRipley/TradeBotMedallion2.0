#!/bin/bash
# Fix Google Cloud Permissions and Deploy
# This script fixes permission issues and completes deployment

set -e

GCLOUD="/Users/andreripley/google-cloud-sdk/bin/gcloud"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Please set a project first."
    exit 1
fi

echo "=========================================="
echo "FIXING PERMISSIONS AND DEPLOYING"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo ""

echo "Step 1: Getting project number..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"

echo ""
echo "Step 2: Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
echo "✅ APIs enabled"

echo ""
echo "Step 3: Granting Cloud Build permissions..."
# Grant Cloud Build service account necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/storage.admin" \
    --condition=None

echo "✅ Permissions granted"

echo ""
echo "Step 4: Creating .gcloudignore to exclude unnecessary files..."
cat > .gcloudignore << 'EOF'
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

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
*.log.*

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Environment
.env
.env.local

# CSV files (large)
*.csv

# Documentation
*.md
!README.md

# Scripts
*.sh
!deploy*.sh
EOF
echo "✅ .gcloudignore created"

echo ""
echo "Step 5: Building container image..."
echo "This may take 2-5 minutes..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/trading-bot --project=$PROJECT_ID

echo ""
echo "Step 6: Deploying to Cloud Run..."
gcloud run deploy trading-bot \
  --image gcr.io/$PROJECT_ID/trading-bot \
  --platform managed \
  --region us-central1 \
  --min-instances=1 \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --memory=512Mi \
  --cpu=1 \
  --timeout=3600 \
  --port=8080

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service URL: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "=========================================="
echo "NEXT STEP: Set Environment Variables"
echo "=========================================="
echo ""
echo "1. Go to: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "2. Click on 'trading-bot' service"
echo "3. Click 'Edit & Deploy New Revision'"
echo "4. Go to 'Variables & Secrets' tab"
echo "5. Add environment variables (see ENABLE_BILLING.md)"
echo "6. Click 'Deploy'"
echo ""
echo "View logs:"
echo "gcloud run services logs read trading-bot --region=us-central1 --project=$PROJECT_ID --follow"
echo ""

