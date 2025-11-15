# Quick Cloud Deployment Guide

## 🚀 Deploy to Google Cloud Run (Recommended)

### Prerequisites
1. ✅ Google Cloud account (free $300 credit)
2. ✅ Google Cloud SDK installed (`gcloud`)
3. ✅ Alpaca API credentials

---

## Step-by-Step Deployment

### Step 1: Install Google Cloud SDK (if not installed)

**macOS:**
```bash
brew install google-cloud-sdk
```

**Or download from:**
https://cloud.google.com/sdk/docs/install

### Step 2: Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create trading-bot-project --name="Trading Bot"

# Set as active project
gcloud config set project trading-bot-project

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### Step 3: Enable Billing

**Important:** Even free tier requires billing enabled!

1. Go to: https://console.cloud.google.com/billing
2. Link a billing account (free tier still applies)
3. You get $300 free credit + free tier benefits

### Step 4: Deploy Using Script

```bash
# Make script executable
chmod +x deploy_gcp.sh

# Run deployment script
./deploy_gcp.sh
```

**Or manually:**

```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Build container
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/trading-bot

# Deploy to Cloud Run
gcloud run deploy trading-bot \
  --image gcr.io/$GCP_PROJECT_ID/trading-bot \
  --platform managed \
  --region us-central1 \
  --min-instances=1 \
  --allow-unauthenticated
```

### Step 5: Set Environment Variables

**Option A: Via Console (Easiest)**
1. Go to: https://console.cloud.google.com/run
2. Click on `trading-bot` service
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add these variables:

```
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
STOCKS=AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,V,UNH,XOM,JNJ,JPM,WMT,MA,PG,LLY,AVGO,HD,CVX,MRK,ABBV,COST,ADBE,PEP,TMO,MCD,CSCO,NFLX,ABT,ACN
POSITION_SIZE=1000.0
TIMEZONE=America/New_York
LOG_LEVEL=INFO
```

6. Click "Deploy"

**Option B: Via Command Line**
```bash
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars="ALPACA_API_KEY=your_key,ALPACA_SECRET_KEY=your_secret,ALPACA_BASE_URL=https://paper-api.alpaca.markets,STOCKS=AAPL,MSFT,GOOGL,POSITION_SIZE=1000.0,TIMEZONE=America/New_York,LOG_LEVEL=INFO"
```

### Step 6: Verify Deployment

```bash
# Check service status
gcloud run services describe trading-bot --region=us-central1

# View logs
gcloud run services logs read trading-bot --region=us-central1 --limit=50

# Stream logs (real-time)
gcloud run services logs read trading-bot --region=us-central1 --follow
```

---

## 🎯 Quick Commands Reference

### Deploy
```bash
./deploy_gcp.sh
```

### View Logs
```bash
gcloud run services logs read trading-bot --region=us-central1 --limit=50
```

### Stream Logs
```bash
# Use the provided script
./stream_logs.sh

# Or manually
gcloud run services logs read trading-bot --region=us-central1 --follow
```

### Check Status
```bash
gcloud run services describe trading-bot --region=us-central1
```

### Update Environment Variables
```bash
gcloud run services update trading-bot \
  --region=us-central1 \
  --update-env-vars="KEY=value"
```

### Redeploy After Code Changes
```bash
# Just run deploy script again
./deploy_gcp.sh
```

---

## 💰 Cost Information

### Cloud Run Pricing
- **Free Tier**: 2 million requests/month
- **After Free Tier**: ~$0.10-0.50/month for continuous running
- **With min-instances=1**: ~$5-10/month (keeps running 24/7)

### Free Credits
- **New Accounts**: $300 free credit (valid for 90 days)
- **Free Tier**: Always free (2M requests/month)

---

## ⚙️ Configuration Options

### Keep Bot Running 24/7
```bash
# Set minimum instances to 1 (prevents scaling to zero)
gcloud run services update trading-bot \
  --min-instances=1 \
  --region=us-central1
```

### Scale to Zero (Cheaper, but may have cold starts)
```bash
# Remove minimum instances
gcloud run services update trading-bot \
  --min-instances=0 \
  --region=us-central1
```

### Increase Resources (if needed)
```bash
gcloud run services update trading-bot \
  --memory=512Mi \
  --cpu=1 \
  --region=us-central1
```

---

## 🔍 Troubleshooting

### "Billing account not found"
- Enable billing: https://console.cloud.google.com/billing
- Even free tier requires billing enabled

### "Permission denied"
- Run: `./deploy_fix_permissions.sh`
- Or manually enable APIs and grant permissions

### "Container failed to become healthy"
- Check logs: `gcloud run services logs read trading-bot --region=us-central1`
- Ensure `main.py` has health check endpoint (already included)

### "Insufficient buying power" errors
- Add funds to Alpaca paper account: https://app.alpaca.markets/paper/dashboard/account
- Or reduce `POSITION_SIZE` in environment variables

---

## 📊 Monitoring

### View Logs in Console
1. Go to: https://console.cloud.google.com/run
2. Click on `trading-bot` service
3. Click "Logs" tab
4. See real-time logs

### View Metrics
1. Go to: https://console.cloud.google.com/run
2. Click on `trading-bot` service
3. Click "Metrics" tab
4. See CPU, memory, requests

---

## 🔄 Updating the Bot

### After Making Code Changes

1. **Commit changes to Git** (optional but recommended)
```bash
git add .
git commit -m "Update bot"
git push
```

2. **Redeploy**
```bash
./deploy_gcp.sh
```

The script will rebuild the container and deploy the new version.

---

## ✅ Verification Checklist

- [ ] Google Cloud SDK installed (`gcloud --version`)
- [ ] Authenticated (`gcloud auth login`)
- [ ] Project created and set (`gcloud config set project`)
- [ ] Billing enabled
- [ ] APIs enabled (Cloud Build, Cloud Run)
- [ ] Dockerfile exists
- [ ] Environment variables set in Cloud Run
- [ ] Service deployed successfully
- [ ] Logs showing bot activity
- [ ] Bot checking stocks every minute during market hours

---

## 🎉 Success!

Once deployed, your bot will:
- ✅ Run 24/7 in the cloud
- ✅ Check stocks every minute during market hours
- ✅ Execute trades automatically
- ✅ Log all activity
- ✅ Handle errors gracefully

**Monitor it:**
- View logs: `./view_logs.sh` or Cloud Console
- Check status: Cloud Run console
- Verify trades: Alpaca dashboard

---

## Need Help?

- **Deployment Issues**: Check `GCP_DEPLOYMENT.md`
- **Environment Variables**: Check `CLOUD_RUN_ENV_VARS.md`
- **Troubleshooting**: Check logs first, then documentation

