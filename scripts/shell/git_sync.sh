#!/bin/bash
set -e

cd /Users/andreripley/Desktop/TradeBot

echo "📥 Pulling remote changes..."
git pull origin main || {
    echo "⚠️  Pull encountered issues. Checking status..."
    git status
    echo ""
    echo "If there are merge conflicts, please resolve them manually."
    exit 1
}

echo ""
echo "✅ Remote changes pulled successfully"
echo ""
echo "📤 Pushing local changes..."
git push origin main

echo ""
echo "✅ Successfully pushed to GitHub!"

