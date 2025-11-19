# Fixing GCP Permission Issues

## Problem
You're getting permission errors when trying to enable APIs. This usually means:
1. You don't have the right IAM roles on the project
2. Billing is not enabled
3. The project doesn't exist or you're not the owner

## Solution Steps

### Step 1: Verify Project Access

Check if you can access the project:
```bash
gcloud projects describe trading-bot-894185
```

If this fails, the project might not exist or you don't have access.

### Step 2: Check Your Roles

See what roles you have:
```bash
gcloud projects get-iam-policy trading-bot-894185 \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:$(gcloud config get-value account)"
```

You need one of these roles:
- **Owner** (recommended)
- **Editor**
- Or at minimum: **Service Usage Admin** + **Project IAM Admin**

### Step 3: Grant Yourself Owner Role

If you're the project creator, you should already be Owner. If not, ask someone with Owner role to grant you:

```bash
# If you have Owner role, grant yourself (or ask project owner to run):
gcloud projects add-iam-policy-binding trading-bot-894185 \
  --member="user:andreripleyedu@gmail.com" \
  --role="roles/owner"
```

### Step 4: Enable Billing

**Important**: APIs require billing to be enabled.

1. Go to: https://console.cloud.google.com/billing?project=trading-bot-894185
2. Link a billing account to the project
3. Or enable billing if you haven't already

### Step 5: Enable APIs Manually (Alternative)

If the script fails, enable APIs one by one:

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com --project=trading-bot-894185

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com --project=trading-bot-894185

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com --project=trading-bot-894185

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com --project=trading-bot-894185

# Note: Cloud Scheduler might have restrictions - see below
```

### Step 6: Cloud Scheduler Issue

The error mentions Cloud Scheduler is an "internal service". This might mean:
1. Your account/organization has restrictions
2. You need to use Cloud Tasks instead (alternative)
3. Or enable it through the Console

**Try enabling via Console**:
1. Go to: https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com?project=trading-bot-894185
2. Click "Enable"

**Or use Cloud Tasks** (alternative scheduler):
- Cloud Tasks can be used instead of Cloud Scheduler
- I can modify the script to use Cloud Tasks if needed

### Step 7: Verify Everything

After fixing permissions and enabling billing:

```bash
# Check billing status
gcloud billing projects describe trading-bot-894185

# Try enabling an API again
gcloud services enable run.googleapis.com --project=trading-bot-894185
```

## Quick Fix Checklist

- [ ] Verify project exists and you can access it
- [ ] Check you have Owner/Editor role
- [ ] Enable billing on the project
- [ ] Try enabling APIs via Console if CLI fails
- [ ] Re-run deployment script

## Alternative: Create New Project

If you can't get permissions on this project, create a new one:

```bash
# Create new project
gcloud projects create your-new-project-id --name="Trading Bot"

# Set as current project
gcloud config set project your-new-project-id

# Enable billing (you'll need to do this in Console)
# Then run deployment script again
```

## Need Help?

If you're still stuck:
1. Check Cloud Console: https://console.cloud.google.com/iam-admin/iam?project=trading-bot-894185
2. Verify billing: https://console.cloud.google.com/billing?project=trading-bot-894185
3. Check API status: https://console.cloud.google.com/apis/dashboard?project=trading-bot-894185

