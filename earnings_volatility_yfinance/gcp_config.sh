#!/bin/bash
# Configuration file for GCP deployment
# Copy this file and set your values, then source it before running gcp_deploy.sh

# Your Google Cloud Project ID
export GCP_PROJECT_ID="trading-bot-894185"

# Your preferred GCP region (e.g., us-central1, us-east1, europe-west1)
export GCP_REGION="us-central1"

# Optional: Custom service account email (defaults to earnings-bot-sa@PROJECT_ID.iam.gserviceaccount.com)
# export SERVICE_ACCOUNT="custom-sa@your-project-id.iam.gserviceaccount.com"

