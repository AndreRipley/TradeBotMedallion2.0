#!/bin/bash
# Simple Log Viewer - Shows Recent Logs

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="trading-bot"

echo "=========================================="
echo "TRADING BOT LOGS"
echo "=========================================="
echo ""

# Show last 50 lines
gcloud run services logs read $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --limit=50 \
    --format="table(timestamp,severity,textPayload)"

echo ""
echo "=========================================="
echo "To refresh, run this script again"
echo "Or use: gcloud run services logs read trading-bot --region=us-central1 --limit=50"
echo "=========================================="

