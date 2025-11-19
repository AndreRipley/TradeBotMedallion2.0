# Setting GCP Environment Variables

You have several options for setting `GCP_PROJECT_ID` and `GCP_REGION`. Choose the method that works best for you:

## Option 1: Set in Current Shell Session (Temporary)

**Best for**: One-time deployment or testing

```bash
# Set variables in your current terminal session
export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"

# Then run the deployment script
./earnings_volatility_yfinance/gcp_deploy.sh
```

**Note**: These will only last for the current terminal session. Close the terminal and you'll need to set them again.

---

## Option 2: Use Configuration File (Recommended)

**Best for**: Reusable configuration

1. **Edit the config file**:
   ```bash
   # Edit the config file with your values
   nano earnings_volatility_yfinance/gcp_config.sh
   # or
   vim earnings_volatility_yfinance/gcp_config.sh
   ```

2. **Set your values**:
   ```bash
   export GCP_PROJECT_ID="your-actual-project-id"
   export GCP_REGION="us-central1"
   ```

3. **Source it before running deploy**:
   ```bash
   source earnings_volatility_yfinance/gcp_config.sh
   ./earnings_volatility_yfinance/gcp_deploy.sh
   ```

---

## Option 3: Add to Shell Profile (Permanent)

**Best for**: Using the same project/region frequently

### For Zsh (macOS default):
```bash
# Edit your ~/.zshrc file
nano ~/.zshrc

# Add these lines at the end:
export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"

# Save and reload
source ~/.zshrc
```

### For Bash:
```bash
# Edit your ~/.bashrc or ~/.bash_profile
nano ~/.bashrc

# Add these lines at the end:
export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"

# Save and reload
source ~/.bashrc
```

**Note**: These will be available in all new terminal sessions.

---

## Option 4: Interactive Prompt (Easiest)

**Best for**: Quick setup without editing files

The deployment script now prompts you if variables aren't set:

```bash
# Just run the script - it will ask for values if needed
./earnings_volatility_yfinance/gcp_deploy.sh
```

You'll see prompts like:
```
GCP_PROJECT_ID not set.
Enter your GCP Project ID: your-project-id
GCP_REGION not set.
Enter your GCP Region (default: us-central1): us-central1
```

---

## Option 5: Inline with Command

**Best for**: Quick one-off runs

```bash
GCP_PROJECT_ID="your-project-id" GCP_REGION="us-central1" ./earnings_volatility_yfinance/gcp_deploy.sh
```

---

## Finding Your Project ID

If you don't know your GCP Project ID:

```bash
# List all projects
gcloud projects list

# Or get current project
gcloud config get-value project
```

## Common Regions

- `us-central1` (Iowa) - Good default
- `us-east1` (South Carolina)
- `us-west1` (Oregon)
- `europe-west1` (Belgium)
- `asia-east1` (Taiwan)

---

## Recommended Approach

For most users, **Option 4 (Interactive Prompt)** is the easiest - just run the script and it will ask for what it needs.

For repeated deployments, use **Option 2 (Config File)** - edit `gcp_config.sh` once, then source it before each deployment.

