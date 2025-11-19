# Cloud Run Refactor Summary

## Files Created

### 1. `main_cloud.py`
**Purpose**: Cloud Run Job entry point with mode-based execution

**Key Features**:
- Removed APScheduler dependency
- Added `argparse` for `--mode` argument (entry/exit)
- **Entry Mode**: 
  - Scans universe at 3:15 PM
  - Waits until 3:45 PM if needed
  - Re-validates and submits orders
  - Exits after completion
- **Exit Mode**:
  - Fetches all open positions
  - Closes them immediately
  - Exits after completion
- Logging configured for Cloud Run (stdout/stderr)

### 2. `Dockerfile`
**Purpose**: Containerizes the bot for Cloud Run

**Key Features**:
- Base: `python:3.11-slim`
- Installs system dependencies for numpy/pandas/scipy
- Copies application code
- Sets PYTHONPATH
- Entrypoint: `python -m earnings_volatility_yfinance.main_cloud`

### 3. `gcp_deploy.sh`
**Purpose**: Automated deployment script

**Steps**:
1. Enables required APIs (Run, Scheduler, Artifact Registry, Secret Manager)
2. Creates Artifact Registry repository
3. Builds and pushes Docker image
4. Creates/updates Cloud Run Job with secrets
5. Creates two Cloud Scheduler jobs:
   - `earnings-entry`: 3:15 PM ET (Mon-Fri) → `--mode entry`
   - `earnings-exit`: 9:45 AM ET (Mon-Fri) → `--mode exit`

**Configuration**:
- Job name: `earnings-bot`
- Region: Configurable (default: `us-central1`)
- Resources: 2 CPU, 2GB RAM, 30min timeout
- Secrets linked from Secret Manager

### 4. `setup_secrets.py`
**Purpose**: Interactive script to set up secrets in Google Secret Manager

**Features**:
- Checks if secrets exist
- Prompts to create/update missing secrets
- Optionally uses values from local `.env` file
- Creates secrets: `alpaca-key`, `alpaca-secret`, `supabase-url`, `supabase-key`, `api-ninjas-key`

### 5. `.dockerignore`
**Purpose**: Excludes unnecessary files from Docker build

### 6. `CLOUD_RUN_DEPLOYMENT.md`
**Purpose**: Comprehensive deployment guide with troubleshooting

## Architecture Changes

### Before (24/7 Script)
- Persistent Python script running continuously
- APScheduler for internal scheduling
- Manual deployment
- Local execution

### After (Cloud Run Jobs)
- Ephemeral containers that run on-demand
- External scheduling via Cloud Scheduler
- Automated deployment via script
- Cloud-based execution

## Execution Flow

### Entry Mode (3:15 PM ET)
```
Cloud Scheduler → Cloud Run Job (--mode entry)
  ↓
1. Scan universe (2-5 min)
  ↓
2. Wait until 3:45 PM (if needed)
  ↓
3. Re-validate signals
  ↓
4. Submit orders
  ↓
5. Exit (container shuts down)
```

### Exit Mode (9:45 AM ET)
```
Cloud Scheduler → Cloud Run Job (--mode exit)
  ↓
1. Fetch open positions
  ↓
2. Close all positions
  ↓
3. Exit (container shuts down)
```

## Deployment Steps

1. **Set environment variables**:
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   export GCP_REGION="us-central1"
   ```

2. **Set up secrets**:
   ```bash
   pip install google-cloud-secret-manager
   python3 earnings_volatility_yfinance/setup_secrets.py
   ```

3. **Deploy**:
   ```bash
   ./earnings_volatility_yfinance/gcp_deploy.sh
   ```

4. **Verify**:
   ```bash
   gcloud run jobs list --region=$GCP_REGION
   gcloud scheduler jobs list --location=$GCP_REGION
   ```

## Benefits

1. **Cost Efficiency**: Pay only for execution time, not idle time
2. **Scalability**: Cloud Run handles scaling automatically
3. **Reliability**: Built-in retries and error handling
4. **Security**: Secrets managed by Google Secret Manager
5. **Monitoring**: Integrated with Cloud Logging and Monitoring
6. **Maintenance**: No need to manage a persistent server

## Testing

Test locally before deploying:
```bash
# Build Docker image locally
docker build -t earnings-bot-test -f earnings_volatility_yfinance/Dockerfile .

# Test entry mode
docker run --rm earnings-bot-test --mode entry

# Test exit mode
docker run --rm earnings-bot-test --mode exit
```

Test in Cloud Run:
```bash
# Manual execution
gcloud run jobs execute earnings-bot \
  --region=$GCP_REGION \
  --args='--mode,entry'
```

## Next Steps

1. Review and customize `gcp_deploy.sh` configuration
2. Set up secrets using `setup_secrets.py`
3. Deploy using `gcp_deploy.sh`
4. Monitor logs and adjust as needed
5. Set up Cloud Monitoring alerts

