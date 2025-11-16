#!/bin/bash
# Push changes to GitHub

echo "Checking git status..."
git status

echo ""
echo "Adding all changes..."
git add -A

echo ""
echo "Files staged for commit:"
git status --short

echo ""
echo "Committing changes..."
git commit -m "Add Cloud Run deployment support with health check endpoint

- Added HTTP health check server for Cloud Run compatibility
- Created deployment scripts for Google Cloud Platform
- Added environment variable documentation
- Updated main.py to include health check endpoint on port 8080
- Created deploy_fix_permissions.sh for automated deployment
- Added CLOUD_RUN_ENV_VARS.md guide"

echo ""
echo "Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Done! Changes pushed to GitHub."

