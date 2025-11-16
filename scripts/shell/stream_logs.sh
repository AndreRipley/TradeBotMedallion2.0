#!/bin/bash
# Stream Trading Bot Logs from Cloud Run (Polling Method)

echo "=========================================="
echo "STREAMING TRADING BOT LOGS"
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
echo "Streaming logs (Polling every 3 seconds, Press Ctrl+C to stop)..."
echo "=========================================="
echo ""

# Get initial timestamp
LAST_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Show recent logs first
echo "📋 Recent logs:"
gcloud run services logs read $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)" 2>/dev/null

echo ""
echo "🔄 Now streaming new logs (checking every 3 seconds)..."
echo "=========================================="
echo ""

# Poll for new logs
while true; do
    # Get logs since last check
    NEW_LOGS=$(gcloud run services logs read $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --limit=50 \
        --format="table(timestamp,severity,textPayload)" 2>/dev/null)
    
    # Filter to show only new logs (simple approach - show all recent)
    if [ -n "$NEW_LOGS" ]; then
        echo "$NEW_LOGS" | tail -n +2  # Skip header if repeated
    fi
    
    # Update timestamp
    LAST_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Wait before next poll
    sleep 3
done

