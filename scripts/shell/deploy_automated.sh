#!/bin/bash
# Automated Google Cloud Deployment Script
# This script will deploy your trading bot to Google Cloud Run

set -e  # Exit on error

echo "=========================================="
echo "GOOGLE CLOUD DEPLOYMENT - AUTOMATED"
echo "=========================================="
echo ""

# Use gcloud from the detected path
GCLOUD="/Users/andreripley/google-cloud-sdk/bin/gcloud"

# Check if gcloud exists
if [ ! -f "$GCLOUD" ]; then
    echo "❌ gcloud not found at $GCLOUD"
    echo "Please ensure Google Cloud SDK is installed"
    exit 1
fi

echo "Step 1: Checking current project..."
CURRENT_PROJECT=$($GCLOUD config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo "⚠️  No project set. Creating new project..."
    
    # Generate unique project ID
    PROJECT_ID="trading-bot-$(date +%s | tail -c 7)"
    echo "Creating project: $PROJECT_ID"
    
    $GCLOUD projects create $PROJECT_ID --name="Trading Bot" || {
        echo "⚠️  Project creation failed. Trying to use existing project..."
        echo "Available projects:"
        $GCLOUD projects list --format="table(projectId,name)"
        echo ""
        read -p "Enter project ID to use: " PROJECT_ID
    }
    
    $GCLOUD config set project $PROJECT_ID
    echo "✅ Project set to: $PROJECT_ID"
else
    PROJECT_ID=$CURRENT_PROJECT
    echo "✅ Using existing project: $PROJECT_ID"
fi

echo ""
echo "Step 2: Enabling required APIs..."
$GCLOUD services enable run.googleapis.com --project=$PROJECT_ID
$GCLOUD services enable cloudbuild.googleapis.com --project=$PROJECT_ID
echo "✅ APIs enabled"

echo ""
echo "Step 3: Checking Dockerfile..."
if [ ! -f "Dockerfile" ]; then
    echo "⚠️  Dockerfile not found. Creating..."
    cat > Dockerfile << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
DOCKERFILE_EOF
    echo "✅ Dockerfile created"
else
    echo "✅ Dockerfile exists"
fi

echo ""
echo "Step 4: Building container image..."
echo "This may take a few minutes..."
$GCLOUD builds submit --tag gcr.io/$PROJECT_ID/trading-bot --project=$PROJECT_ID

echo ""
echo "Step 5: Deploying to Cloud Run..."
echo "Setting min-instances=1 to keep bot running 24/7..."
$GCLOUD run deploy trading-bot \
  --image gcr.io/$PROJECT_ID/trading-bot \
  --platform managed \
  --region us-central1 \
  --min-instances=1 \
  --allow-unauthenticated \
  --project=$PROJECT_ID \
  --memory=512Mi \
  --cpu=1

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service: trading-bot"
echo "Region: us-central1"
echo ""
echo "=========================================="
echo "NEXT STEP: Set Environment Variables"
echo "=========================================="
echo ""
echo "1. Go to Cloud Run console:"
echo "   https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "2. Click on 'trading-bot' service"
echo ""
echo "3. Click 'Edit & Deploy New Revision'"
echo ""
echo "4. Go to 'Variables & Secrets' tab"
echo ""
echo "5. Add these environment variables:"
echo "   - ALPACA_API_KEY"
echo "   - ALPACA_SECRET_KEY"
echo "   - ALPACA_BASE_URL=https://paper-api.alpaca.markets"
echo "   - STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA"
echo "   - POSITION_SIZE=1000.0"
echo "   - TIMEZONE=America/New_York"
echo "   - LOG_LEVEL=INFO"
echo ""
echo "6. Click 'Deploy'"
echo ""
echo "=========================================="
echo "View Logs:"
echo "=========================================="
echo "$GCLOUD run services logs read trading-bot --region=us-central1 --project=$PROJECT_ID --follow"
echo ""
echo "Or in console:"
echo "https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""

