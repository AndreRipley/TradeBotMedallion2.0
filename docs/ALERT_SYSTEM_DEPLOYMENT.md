# Trading Alert System - GCP Deployment Guide

## 🚀 Deploy to Google Cloud Run

This guide will help you deploy the Trading Alert System to Google Cloud Run.

## Prerequisites

1. ✅ Google Cloud account (free $300 credit)
2. ✅ Google Cloud SDK installed (`gcloud`)
3. ✅ Alpha Vantage API key (optional, for real data)
4. ✅ Billing enabled (required even for free tier)

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Run deployment script
./scripts/shell/deploy_alert_system.sh
```

### Option 2: Manual Deployment

```bash
# 1. Set project
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 3. Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/trading-alert-system

# 4. Deploy to Cloud Run
gcloud run deploy trading-alert-system \
  --image gcr.io/YOUR_PROJECT_ID/trading-alert-system \
  --platform managed \
  --region us-central1 \
  --min-instances=1 \
  --max-instances=1 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=3600 \
  --allow-unauthenticated
```

## Environment Variables

After deployment, set these in Cloud Run console:

### Required
- `ALPHA_VANTAGE_API_KEY` - Your Alpha Vantage API key (or leave empty for mock data)

### Optional (with defaults)
- `DATABASE_URL` - Database URL (default: `sqlite:///./data/trading_alerts.db`)
- `RSI_THRESHOLD` - RSI cross-under threshold (default: `28.0`)
- `MIN_MARKET_CAP` - Minimum market cap filter (default: `5000000000`)
- `THREE_MONTH_MIN_RETURN` - 3-month return threshold (default: `80.0`)
- `SIX_MONTH_MIN_RETURN` - 6-month return threshold (default: `90.0`)
- `YTD_MIN_RETURN` - YTD return threshold (default: `100.0`)
- `UPDATE_INTERVAL_MINUTES` - Update interval (default: `5`)
- `MARKET_HOURS_ONLY` - Only run during market hours (default: `true`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

## Setting Environment Variables

1. Go to: https://console.cloud.google.com/run
2. Click on `trading-alert-system` service
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add environment variables
6. Click "Deploy"

## Initial Setup After Deployment

Once deployed, you need to initialize the system:

### 1. Build the Universe

```bash
# SSH into Cloud Run instance or use Cloud Shell
gcloud run services exec trading-alert-system --region=us-central1 --command="python3 -m app.universe.build"
```

Or run locally and sync database, or use Cloud SQL instead of SQLite.

### 2. Compute RSI

```bash
gcloud run services exec trading-alert-system --region=us-central1 --command="python3 -m app.indicators.compute_rsi --all"
```

### 3. Monitor Will Run Automatically

The service will automatically:
- Update candles every 5 minutes
- Update RSI values
- Detect RSI cross-under events
- Create alerts

## Using Cloud SQL (Recommended for Production)

For production, use Cloud SQL instead of SQLite:

1. Create Cloud SQL instance:
```bash
gcloud sql instances create trading-alerts-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

2. Create database:
```bash
gcloud sql databases create trading_alerts --instance=trading-alerts-db
```

3. Set environment variable:
```
DATABASE_URL=postgresql://user:password@/trading_alerts?host=/cloudsql/PROJECT_ID:us-central1:trading-alerts-db
```

4. Update Cloud Run service to connect to Cloud SQL:
```bash
gcloud run services update trading-alert-system \
  --add-cloudsql-instances=PROJECT_ID:us-central1:trading-alerts-db \
  --region=us-central1
```

## Monitoring & Logs

### View Logs

```bash
gcloud run services logs read trading-alert-system \
  --region=us-central1 \
  --follow
```

### Check Service Status

```bash
gcloud run services describe trading-alert-system \
  --region=us-central1
```

## Cost Estimate

- **Cloud Run**: ~$0.10-0.50/month (with min-instances=1)
- **Cloud SQL** (if used): ~$7-10/month for db-f1-micro
- **Total**: ~$7-11/month for production setup

## Troubleshooting

### Service Won't Start

1. Check logs: `gcloud run services logs read trading-alert-system --region=us-central1`
2. Verify environment variables are set correctly
3. Check database connection (if using Cloud SQL)

### No Alerts Generated

1. Ensure universe is built: `python3 -m app.universe.build`
2. Ensure RSI is computed: `python3 -m app.indicators.compute_rsi --all`
3. Check that candles exist in database
4. Verify RSI threshold is appropriate

### Database Issues

- SQLite files are ephemeral in Cloud Run (use Cloud SQL for persistence)
- Ensure `/app/data` directory exists and is writable
- Consider using Cloud Storage for SQLite backup

## Architecture

The alert system runs as a single Cloud Run service that:
- Continuously monitors the universe
- Updates candles and RSI every 5 minutes
- Detects RSI cross-under events
- Stores alerts in database

For production, consider:
- Separate services for universe building, RSI computation, and monitoring
- Cloud SQL for persistent database
- Cloud Scheduler for periodic universe rebuilds
- Pub/Sub for alert notifications

