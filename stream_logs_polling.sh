#!/bin/bash
# Stream Trading Bot Logs - Alternative Method (Polling)

echo "=========================================="
echo "STREAMING TRADING BOT LOGS (Polling)"
echo "=========================================="
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="trading-bot"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set."
    exit 1
fi

echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""
echo "Streaming logs (Polling every 5 seconds, Press Ctrl+C to stop)..."
echo "=========================================="
echo ""

LAST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

while true; do
    # Get new logs since last check
    gcloud run services logs read $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --limit=50 \
        --format="table(timestamp,severity,textPayload)" \
        2>/dev/null | grep -A 1000 "$LAST_TIMESTAMP" || true
    
    # Update timestamp
    LAST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Wait before next poll
    sleep 5
done

