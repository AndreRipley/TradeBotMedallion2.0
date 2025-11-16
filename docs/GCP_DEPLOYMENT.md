# Google Cloud Platform Deployment Guide

## Recommended: Google Cloud Run ⭐

**Best Option for Trading Bot**

### Why Cloud Run?
- ✅ Serverless - no server management
- ✅ Pay-per-use pricing (very cheap)
- ✅ Can run continuously
- ✅ Easy deployment with Docker
- ✅ Free tier: 2 million requests/month
- ✅ Automatic scaling

### Cost Estimate
- **Free Tier:** 2 million requests/month
- **After Free Tier:** ~$0.10-0.50/month for continuous running
- **Very affordable!**

---

## Setup Steps for Cloud Run

### Step 1: Create Dockerfile

Create `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the bot
CMD ["python3", "main.py"]
```

### Step 2: Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Or download from:
# https://cloud.google.com/sdk/docs/install
```

### Step 3: Authenticate

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 4: Build and Deploy

```bash
# Build container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/trading-bot

# Deploy to Cloud Run
gcloud run deploy trading-bot \
  --image gcr.io/YOUR_PROJECT_ID/trading-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ALPACA_API_KEY=your_key,ALPACA_SECRET_KEY=your_secret,STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA"
```

### Step 5: Set Environment Variables

In Cloud Run console:
1. Go to Cloud Run → trading-bot → Edit & Deploy New Revision
2. Variables & Secrets tab
3. Add:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `ALPACA_BASE_URL=https://paper-api.alpaca.markets`
   - `STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA`
   - `POSITION_SIZE=1000.0`
   - `TIMEZONE=America/New_York`
   - `LOG_LEVEL=INFO`

### Step 6: Configure for Continuous Running

Cloud Run by default scales to zero. To keep it running:

```bash
# Set minimum instances to 1 (keeps it always running)
gcloud run services update trading-bot \
  --min-instances=1 \
  --region=us-central1
```

**Note:** This will cost more (~$5-10/month) but ensures 24/7 operation.

---

## Alternative: Compute Engine (VM)

### Why Compute Engine?
- Full control over server
- Fixed monthly cost
- More predictable
- Free tier: e2-micro (1 year)

### Setup Steps

1. **Create VM Instance:**
```bash
gcloud compute instances create trading-bot-vm \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

2. **SSH into VM:**
```bash
gcloud compute ssh trading-bot-vm --zone=us-central1-a
```

3. **Install Dependencies:**
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

4. **Clone and Setup:**
```bash
git clone YOUR_REPO_URL
cd TradeBot
pip3 install -r requirements.txt
```

5. **Set Environment Variables:**
```bash
nano .env
# Add your API keys
```

6. **Create Systemd Service:**
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add:
```ini
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/TradeBot
ExecStart=/usr/bin/python3 /home/YOUR_USER/TradeBot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

7. **Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

---

## Cost Comparison

| Service | Free Tier | Cost After | Best For |
|---------|-----------|------------|----------|
| **Cloud Run** | 2M requests/month | $0.10-0.50/mo | ⭐ Recommended |
| **Compute Engine** | e2-micro (1 year) | $5-10/mo | Full control |
| **Cloud Functions** | 2M invocations | Pay-per-use | Scheduled tasks |
| **App Engine** | 28 hours/day | Pay-per-use | Web apps |

---

## Quick Start: Cloud Run (Recommended)

### Prerequisites
1. Google Cloud account (free $300 credit)
2. Google Cloud SDK installed
3. Docker (optional, Cloud Build handles it)

### One-Command Deploy Script

Create `deploy_gcp.sh`:

```bash
#!/bin/bash
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="trading-bot"

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --min-instances=1 \
  --set-env-vars="ALPACA_API_KEY=$ALPACA_API_KEY,ALPACA_SECRET_KEY=$ALPACA_SECRET_KEY"
```

---

## Monitoring

### View Logs
```bash
gcloud run services logs read trading-bot --region=us-central1
```

### In Console
- Go to Cloud Run → trading-bot → Logs tab
- Real-time log streaming available

---

## Important Notes

1. **Cloud Run Scaling:**
   - By default, scales to zero (stops when idle)
   - Set `--min-instances=1` to keep running 24/7
   - Costs more but ensures continuous operation

2. **Free Tier:**
   - Cloud Run: 2 million requests/month
   - Compute Engine: e2-micro free for 1 year
   - $300 free credit for new accounts

3. **Billing:**
   - Cloud Run: Pay only for CPU/memory used
   - Very cheap for continuous running (~$0.10-0.50/month)
   - Set billing alerts in GCP console

---

## Recommendation

**Use Google Cloud Run** because:
- ✅ Easiest to deploy
- ✅ Cheapest option (~$0.10-0.50/month)
- ✅ No server management
- ✅ Automatic scaling
- ✅ Free tier covers most usage

**Setup Time:** ~15-20 minutes

---

## Next Steps

1. Create Google Cloud account (free $300 credit)
2. Create project in GCP Console
3. Install Google Cloud SDK
4. Follow Cloud Run setup steps above
5. Deploy and monitor!

See `DEPLOYMENT.md` for more detailed instructions.

