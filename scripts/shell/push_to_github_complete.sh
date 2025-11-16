#!/bin/bash
# Complete git sync and push script - handles divergent branches

cd /Users/andreripley/Desktop/TradeBot

echo "=========================================="
echo "Git Sync and Push Script"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Configure pull strategy to merge (safer than rebase)
echo "⚙️  Configuring git pull strategy (merge)..."
git config pull.rebase false

# Show current status
echo ""
echo "📋 Current git status:"
git status --short
echo ""

# Add all changes
echo "📦 Adding all changes..."
git add -A
echo ""

# Show what will be committed
echo "📝 Files staged for commit:"
git status --short
echo ""

# Check if there are changes to commit
if git diff --cached --quiet && git diff --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Add Cloud Run deployment support with health check endpoint

- Added HTTP health check server for Cloud Run compatibility
- Created deployment scripts for Google Cloud Platform
- Added environment variable documentation
- Updated main.py to include health check endpoint on port 8080
- Created deploy_fix_permissions.sh for automated deployment
- Added CLOUD_RUN_ENV_VARS.md guide"
    echo ""
fi

# Pull remote changes with merge strategy
echo "📥 Pulling remote changes (merge strategy)..."
if git pull origin main --no-rebase; then
    echo "✅ Pull successful"
else
    echo "⚠️  Pull encountered merge conflicts. Please resolve manually."
    echo ""
    echo "To resolve conflicts:"
    echo "1. Check which files have conflicts: git status"
    echo "2. Edit the conflicted files"
    echo "3. Run: git add <file>"
    echo "4. Run: git commit"
    echo "5. Run this script again"
    exit 1
fi
echo ""

# Push changes
echo "📤 Pushing to GitHub..."
if git push origin main; then
    echo ""
    echo "=========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Push failed. Check the error above."
    echo "=========================================="
    exit 1
fi
