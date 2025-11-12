#!/bin/bash
# Check Trading Bot Status - Cloud Run Deployment

echo "=========================================="
echo "TRADING BOT STATUS CHECK"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="trading-bot"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Check service status
echo "📊 Checking service status..."
echo "----------------------------------------"
gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="table(
        status.conditions[0].type,
        status.conditions[0].status,
        status.url,
        spec.template.spec.containers[0].image,
        status.latestReadyRevisionName,
        status.latestCreatedRevisionName
    )" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Service not found or error accessing it."
    echo "Make sure the service is deployed: bash deploy_fix_permissions.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "HEALTH CHECK"
echo "=========================================="

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)" 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo "Service URL: $SERVICE_URL"
    echo ""
    echo "Testing health endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Health check: OK (HTTP $HTTP_CODE)"
    else
        echo "⚠️  Health check: Failed (HTTP $HTTP_CODE)"
        echo "   The service may still be starting up..."
    fi
else
    echo "⚠️  Could not retrieve service URL"
fi

echo ""
echo "=========================================="
echo "RECENT LOGS (Last 20 lines)"
echo "=========================================="
echo ""

gcloud run services logs read $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Could not retrieve logs"
fi

echo ""
echo "=========================================="
echo "QUICK COMMANDS"
echo "=========================================="
echo ""
echo "View live logs:"
echo "  gcloud run services logs read $SERVICE_NAME --region=$REGION --follow"
echo ""
echo "View service details:"
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION"
echo ""
echo "Open in browser:"
echo "  https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo ""

