# Deployment Checklist - Trading Alert System

## ✅ Pre-Deployment Checklist

### Code Ready
- [x] All modules implemented (universe, indicators, alerts, realtime, backtest)
- [x] Main entrypoint created (`app/main.py`)
- [x] Configuration system with environment variable support
- [x] Database models and initialization
- [x] Error handling and logging
- [x] Unit tests added

### Deployment Files
- [x] Dockerfile created (`Dockerfile.alert`)
- [x] Deployment script created (`scripts/shell/deploy_alert_system.sh`)
- [x] `.gcloudignore` created
- [x] Requirements.txt includes all dependencies
- [x] Documentation created (`docs/ALERT_SYSTEM_DEPLOYMENT.md`)

## 🚀 Deployment Steps

### 1. Prerequisites
- [ ] Google Cloud account with billing enabled
- [ ] Google Cloud SDK installed (`gcloud`)
- [ ] Project ID set: `gcloud config set project YOUR_PROJECT_ID`
- [ ] Alpha Vantage API key (optional, for real data)

### 2. Deploy
```bash
# Set project ID
export GCP_PROJECT_ID=your-project-id

# Run deployment script
./scripts/shell/deploy_alert_system.sh
```

### 3. Configure Environment Variables
After deployment, set in Cloud Run console:
- [ ] `ALPHA_VANTAGE_API_KEY` (if using real data)
- [ ] `DATABASE_URL` (if using Cloud SQL)
- [ ] `LOG_LEVEL=INFO`
- [ ] Any custom thresholds if needed

### 4. Initialize System
After deployment, initialize the database:

**Option A: Using Cloud Run exec (if supported)**
```bash
gcloud run services exec trading-alert-system \
  --region=us-central1 \
  --command="python3 -m app.universe.build"
```

**Option B: Run locally first, then deploy**
1. Build universe locally: `python3 -m app.universe.build`
2. Compute RSI: `python3 -m app.indicators.compute_rsi --all`
3. Upload database to Cloud Storage or use Cloud SQL

**Option C: Use Cloud SQL (Recommended)**
1. Create Cloud SQL instance
2. Update `DATABASE_URL` environment variable
3. Run initialization commands

### 5. Verify Deployment
- [ ] Check service is running: `gcloud run services list`
- [ ] View logs: `gcloud run services logs read trading-alert-system --region=us-central1 --follow`
- [ ] Verify alerts are being generated
- [ ] Check database has data

## 📋 Production Considerations

### Database
- [ ] **Use Cloud SQL** instead of SQLite for persistence
- [ ] Set up automated backups
- [ ] Configure connection pooling

### Monitoring
- [ ] Set up Cloud Monitoring alerts
- [ ] Configure log-based alerts for errors
- [ ] Monitor service health

### Scaling
- [ ] Current: `min-instances=1, max-instances=1` (single instance)
- [ ] Consider multiple instances if needed
- [ ] Use Cloud Scheduler for periodic universe rebuilds

### Security
- [ ] Store API keys in Secret Manager (not env vars)
- [ ] Use IAM for service authentication
- [ ] Enable VPC connector if needed

### Cost Optimization
- [ ] Monitor Cloud Run costs
- [ ] Use Cloud SQL with appropriate tier
- [ ] Consider Cloud Storage for SQLite backups

## 🔧 Troubleshooting

### Service Won't Start
1. Check logs: `gcloud run services logs read trading-alert-system --region=us-central1`
2. Verify environment variables
3. Check database connection

### No Data
1. Ensure universe is built
2. Verify RSI is computed
3. Check data providers are working

### High Costs
1. Review Cloud Run instance configuration
2. Check Cloud SQL usage
3. Monitor API call frequency

## 📊 Post-Deployment

### Monitor These Metrics
- Alert generation rate
- RSI update frequency
- Database size
- API call costs
- Service uptime

### Regular Maintenance
- [ ] Weekly universe rebuild (if needed)
- [ ] Monthly performance review
- [ ] Quarterly cost review
- [ ] Monitor for API rate limits

## ✅ Ready to Deploy?

If all checkboxes above are complete, you're ready to deploy!

```bash
./scripts/shell/deploy_alert_system.sh
```

