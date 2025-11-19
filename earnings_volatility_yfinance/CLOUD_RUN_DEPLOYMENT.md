# Google Cloud Run Deployment Guide

This guide walks you through deploying the Earnings Volatility Trading Bot as a Google Cloud Run Job.

## Architecture Overview

- **Cloud Run Job**: Runs the bot container on-demand
- **Cloud Scheduler**: Triggers the job at specific times
  - Entry job: 3:15 PM ET (Mon-Fri) → executes trades at 3:45 PM ET
  - Exit job: 9:45 AM ET (Mon-Fri) → closes positions
- **Secret Manager**: Stores sensitive credentials securely

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally
4. **Python 3.11+** (for setup scripts)

## Step-by-Step Deployment

### 1. Install Dependencies

```bash
# Install Google Cloud Secret Manager client (for setup script)
pip install google-cloud-secret-manager

# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
```

### 2. Set Environment Variables

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"  # or your preferred region
```

Or edit `gcp_deploy.sh` and set these variables directly.

### 3. Set Up Secrets

Run the setup script to configure secrets in Secret Manager:

```bash
python3 earnings_volatility_yfinance/setup_secrets.py
```

This script will:
- Check if secrets exist
- Prompt you to create/update them
- Optionally use values from your local `.env` file

Required secrets:
- `alpaca-key`: Alpaca API Key
- `alpaca-secret`: Alpaca API Secret
- `supabase-url`: Supabase Project URL
- `supabase-key`: Supabase Anon Key
- `api-ninjas-key`: API Ninjas API Key (optional)

### 4. Deploy to Cloud Run

Run the deployment script:

```bash
cd /Users/andreripley/Desktop/TradeBot
./earnings_volatility_yfinance/gcp_deploy.sh
```

This script will:
1. Enable required APIs
2. Create Artifact Registry repository
3. Build and push Docker image
4. Create/update Cloud Run Job
5. Create Cloud Scheduler jobs (entry and exit)

### 5. Verify Deployment

Check that everything is set up correctly:

```bash
# List Cloud Run Jobs
gcloud run jobs list --region=$GCP_REGION

# List Cloud Scheduler jobs
gcloud scheduler jobs list --location=$GCP_REGION

# Test the job manually (entry mode)
gcloud run jobs execute earnings-bot \
  --region=$GCP_REGION \
  --args='--mode,entry'

# Test the job manually (exit mode)
gcloud run jobs execute earnings-bot \
  --region=$GCP_REGION \
  --args='--mode,exit'
```

### 6. View Logs

```bash
# View recent logs
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=earnings-bot" \
  --limit=50 \
  --format=json

# Stream logs in real-time
gcloud logging tail \
  "resource.type=cloud_run_job AND resource.labels.job_name=earnings-bot"
```

## How It Works

### Entry Mode (3:15 PM ET)

1. **Cloud Scheduler** triggers the job at 3:15 PM ET
2. **Cloud Run Job** starts with `--mode entry`
3. Bot scans universe for earnings (takes ~2-5 minutes)
4. Bot waits until 3:45 PM ET (if needed)
5. Bot re-validates signals
6. Bot submits orders
7. Job completes and container shuts down

### Exit Mode (9:45 AM ET)

1. **Cloud Scheduler** triggers the job at 9:45 AM ET
2. **Cloud Run Job** starts with `--mode exit`
3. Bot fetches all open positions from database
4. Bot closes all positions
5. Job completes and container shuts down

## Configuration

### Modify Schedules

To change the schedule times, edit `gcp_deploy.sh`:

```bash
# Entry job schedule (3:15 PM ET, Mon-Fri)
ENTRY_SCHEDULE="15 15 * * 1-5"

# Exit job schedule (9:45 AM ET, Mon-Fri)
EXIT_SCHEDULE="45 9 * * 1-5"
```

Then re-run the deployment script to update the schedules.

### Modify Job Resources

Edit `gcp_deploy.sh` to change resource limits:

```bash
--memory=2Gi \
--cpu=2 \
--task-timeout=30m
```

### Update Secrets

To update a secret value:

```bash
# Using gcloud CLI
echo -n "your-secret-value" | gcloud secrets versions add alpaca-key --data-file=-

# Or use the setup script
python3 earnings_volatility_yfinance/setup_secrets.py
```

## Troubleshooting

### Job Fails to Start

1. Check logs: `gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=earnings-bot" --limit=10`
2. Verify secrets exist: `gcloud secrets list`
3. Check service account permissions

### Secrets Not Found

1. Verify secrets exist: `gcloud secrets list`
2. Check secret names match in `gcp_deploy.sh`
3. Ensure service account has `roles/secretmanager.secretAccessor`

### Scheduler Not Triggering

1. Check scheduler status: `gcloud scheduler jobs describe earnings-entry --location=$GCP_REGION`
2. Verify timezone: Should be `America/New_York`
3. Check service account has permission to invoke Cloud Run Job

### Docker Build Fails

1. Ensure Docker is running: `docker ps`
2. Check Dockerfile syntax
3. Verify all dependencies are in `requirements.txt`

## Cost Estimation

- **Cloud Run Job**: Pay per execution (~$0.00002400 per vCPU-second, ~$0.00000250 per GiB-second)
- **Cloud Scheduler**: Free tier: 3 jobs per month, then $0.10 per job per month
- **Artifact Registry**: $0.10 per GB/month for storage
- **Secret Manager**: $0.06 per secret version per month

Estimated monthly cost: **$5-15** (depending on execution frequency)

## Manual Execution

You can manually trigger the job anytime:

```bash
# Entry mode
gcloud run jobs execute earnings-bot \
  --region=$GCP_REGION \
  --args='--mode,entry'

# Exit mode
gcloud run jobs execute earnings-bot \
  --region=$GCP_REGION \
  --args='--mode,exit'
```

## Monitoring

Set up alerts in Cloud Monitoring:

1. Go to Cloud Console → Monitoring → Alerting
2. Create alert for Cloud Run Job failures
3. Set notification channel (email, Slack, etc.)

## Cleanup

To remove all resources:

```bash
# Delete Cloud Scheduler jobs
gcloud scheduler jobs delete earnings-entry --location=$GCP_REGION
gcloud scheduler jobs delete earnings-exit --location=$GCP_REGION

# Delete Cloud Run Job
gcloud run jobs delete earnings-bot --region=$GCP_REGION

# Delete Docker image (optional)
gcloud artifacts docker images delete $IMAGE_URI

# Delete secrets (optional - be careful!)
gcloud secrets delete alpaca-key
gcloud secrets delete alpaca-secret
gcloud secrets delete supabase-url
gcloud secrets delete supabase-key
gcloud secrets delete api-ninjas-key
```

## Support

For issues or questions:
1. Check logs first
2. Verify all secrets are set correctly
3. Ensure service account has proper permissions
4. Check Cloud Run Job execution history in Cloud Console

