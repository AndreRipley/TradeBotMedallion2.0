#!/bin/bash
# Google Cloud Run Deployment Script
# Deploys trading bot to Google Cloud Run

# Try to get project ID from gcloud config, or use environment variable, or prompt
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
SERVICE_NAME="trading-bot"

echo "=========================================="
echo "Google Cloud Run Deployment"
echo "=========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""

# Check if project ID is still placeholder
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
fi
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "⚠️  Dockerfile not found. Creating..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
EOF
    echo "✅ Dockerfile created"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found!"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "Step 1: Authenticating..."
gcloud auth login

echo ""
echo "Step 2: Setting project..."
gcloud config set project $PROJECT_ID

echo ""
echo "Step 3: Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo ""
echo "Step 4: Deploying to Cloud Run..."
echo "⚠️  Make sure to set environment variables in Cloud Run console!"
echo ""
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --min-instances=1 \
  --allow-unauthenticated

echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Go to Cloud Run console:"
echo "   https://console.cloud.google.com/run"
echo ""
echo "2. Click on '$SERVICE_NAME' service"
echo ""
echo "3. Go to 'Edit & Deploy New Revision'"
echo ""
echo "4. Add Environment Variables:"
echo "   - ALPACA_API_KEY"
echo "   - ALPACA_SECRET_KEY"
echo "   - ALPACA_BASE_URL=https://paper-api.alpaca.markets"
echo "   - STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA"
echo "   - POSITION_SIZE=1000.0"
echo "   - TIMEZONE=America/New_York"
echo "   - LOG_LEVEL=INFO"
echo ""
echo "5. Deploy!"
echo ""
echo "6. View logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo ""
echo "✅ Deployment complete!"

