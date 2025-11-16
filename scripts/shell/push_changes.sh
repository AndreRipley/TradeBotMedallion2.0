#!/bin/bash
# Push changes to GitHub

set -e

cd /Users/andreripley/Desktop/TradeBot

echo "=========================================="
echo "PUSHING TO GITHUB"
echo "=========================================="
echo ""

echo "📋 Checking git status..."
git status --short

echo ""
echo "📦 Adding all changes..."
git add -A

echo ""
echo "📝 Files to be committed:"
git status --short

echo ""
echo "💾 Committing changes..."
git commit -m "Improve position monitoring frequency and add account balance checks

- Changed position monitoring from every 5 minutes to every 1 minute for better risk management
- Added account balance checking before trades to prevent insufficient buying power errors
- Updated default stock list to 30 diversified stocks (from 5)
- Added comprehensive documentation (TROUBLESHOOTING_LOW_TRADES.md, POSITION_CHECK_ANALYSIS.md, FIX_BUYING_POWER.md)
- Added log streaming scripts (stream_logs.sh, view_logs.sh, check_cloud_bot.sh)
- Improved error messages for buying power issues"

echo ""
echo "📥 Pulling remote changes..."
git config pull.rebase false
git pull origin main --no-rebase || echo "Note: Pull may have conflicts, continuing..."

echo ""
echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Successfully pushed to GitHub!"

