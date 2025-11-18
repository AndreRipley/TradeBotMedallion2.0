# SMS Notification Setup

This guide explains how to set up SMS notifications for trading alerts using Twilio.

## Prerequisites

1. **Twilio Account**: Sign up at https://www.twilio.com (free trial available)
2. **Twilio Phone Number**: Get a phone number from Twilio to send SMS from
3. **Twilio Credentials**: Account SID and Auth Token from Twilio dashboard

## Setup Steps

### 1. Get Twilio Credentials

1. Log in to your Twilio Console: https://console.twilio.com
2. Find your **Account SID** and **Auth Token** on the dashboard
3. Get a **Phone Number** from Twilio (Phone Numbers → Buy a Number)

### 2. Format Phone Number

Your phone number must be in **E.164 format**:
- US numbers: `+1XXXXXXXXXX` (country code +1, then 10 digits)
- Example: `+13402446406` (for 340-244-6406)

### 3. Set Environment Variables in Cloud Run

Run these commands to configure SMS notifications:

```bash
# Enable SMS notifications
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars SMS_ENABLED=true

# Set your phone number (E.164 format)
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars SMS_PHONE_NUMBER=+13402446406

# Set Twilio Account SID
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars TWILIO_ACCOUNT_SID=your_account_sid_here

# Set Twilio Auth Token
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars TWILIO_AUTH_TOKEN=your_auth_token_here

# Set Twilio From Number (your Twilio phone number)
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

### 4. Or Set All at Once

```bash
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars \
    SMS_ENABLED=true,\
    SMS_PHONE_NUMBER=+13402446406,\
    TWILIO_ACCOUNT_SID=your_account_sid,\
    TWILIO_AUTH_TOKEN=your_auth_token,\
    TWILIO_FROM_NUMBER=+1your_twilio_number
```

## SMS Message Format

When a buy alert is triggered, you'll receive an SMS like:

```
🚨 BUY ALERT: AAPL
RSI: 23.40 (below 28)
Price: $99.67
Entry: Next 5-min candle
Take Profit: +3.0%
Max Hold: 20 days
```

## Testing

After setting up, the bot will automatically send SMS notifications when:
- RSI crosses below 28 (oversold condition)
- A buy alert is generated

Check Cloud Run logs to verify SMS is being sent:
```bash
gcloud run services logs read trading-bot --region=us-central1 --limit=50 | grep SMS
```

## Troubleshooting

### SMS Not Sending

1. **Check Twilio credentials**: Verify Account SID and Auth Token are correct
2. **Check phone number format**: Must be E.164 format (+1XXXXXXXXXX)
3. **Check Twilio balance**: Ensure you have credits in your Twilio account
4. **Check logs**: Look for SMS-related errors in Cloud Run logs

### Common Errors

- `"Twilio credentials not configured"`: Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
- `"SMS phone number not configured"`: Set SMS_PHONE_NUMBER
- `"Twilio from number not configured"`: Set TWILIO_FROM_NUMBER
- `"twilio package not installed"**: The package is in requirements.txt, redeploy if needed

## Cost

- Twilio free trial: $15.50 credit (enough for ~1,000 SMS)
- After trial: ~$0.0075 per SMS (very affordable)
- Typical usage: 1-10 SMS per day = $0.02-0.20/month

## Security Notes

- Never commit Twilio credentials to git
- Use environment variables only
- Twilio credentials are stored securely in Cloud Run
- Phone numbers are stored in environment variables (not in code)

