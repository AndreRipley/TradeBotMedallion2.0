#!/bin/bash
# Git sync script - pulls remote changes and pushes local changes

cd /Users/andreripley/Desktop/TradeBot

echo "Step 1: Pulling remote changes from GitHub..."
git pull origin main

echo ""
echo "Step 2: Pushing local changes to GitHub..."
git push origin main

echo ""
echo "✅ Done! Repository synced with GitHub."

