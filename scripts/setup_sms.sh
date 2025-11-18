#!/bin/bash
# Setup SMS notifications for trading bot in Google Cloud Run

set -e

SERVICE_NAME="trading-bot"
REGION="us-central1"
PHONE_NUMBER="+13402446406"  # Your phone number in E.164 format

echo "📱 Setting up SMS notifications for $SERVICE_NAME"
echo ""

# Check if Twilio credentials are provided
if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ] || [ -z "$TWILIO_FROM_NUMBER" ]; then
    echo "❌ Error: Twilio credentials not set!"
    echo ""
    echo "Please set these environment variables:"
    echo "  export TWILIO_ACCOUNT_SID=your_account_sid"
    echo "  export TWILIO_AUTH_TOKEN=your_auth_token"
    echo "  export TWILIO_FROM_NUMBER=+1your_twilio_number"
    echo ""
    echo "Or pass them as arguments:"
    echo "  ./scripts/setup_sms.sh ACCOUNT_SID AUTH_TOKEN FROM_NUMBER"
    echo ""
    exit 1
fi

# Allow passing credentials as arguments
if [ $# -eq 3 ]; then
    TWILIO_ACCOUNT_SID=$1
    TWILIO_AUTH_TOKEN=$2
    TWILIO_FROM_NUMBER=$3
fi

echo "📞 Phone Number: $PHONE_NUMBER"
echo "🔑 Twilio Account SID: ${TWILIO_ACCOUNT_SID:0:10}..."
echo "📱 Twilio From Number: $TWILIO_FROM_NUMBER"
echo ""

read -p "Continue with SMS setup? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "🚀 Updating Cloud Run service..."

gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --update-env-vars \
    SMS_ENABLED=true,\
    SMS_PHONE_NUMBER=$PHONE_NUMBER,\
    TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID,\
    TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN,\
    TWILIO_FROM_NUMBER=$TWILIO_FROM_NUMBER

echo ""
echo "✅ SMS notifications configured!"
echo ""
echo "The bot will now send SMS alerts to $PHONE_NUMBER when:"
echo "  - RSI crosses below 28 (oversold condition)"
echo "  - A buy alert is generated"
echo ""
echo "Check logs to verify:"
echo "  gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=50 | grep SMS"

