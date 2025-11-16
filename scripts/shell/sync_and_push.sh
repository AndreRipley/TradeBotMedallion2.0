#!/bin/bash
# Pull remote changes and push local changes

echo "Step 1: Fetching remote changes..."
git fetch origin main

echo ""
echo "Step 2: Pulling and merging remote changes..."
git pull origin main --no-edit

echo ""
echo "Step 3: Checking for merge conflicts..."
if git diff --check; then
    echo "✅ No merge conflicts detected"
else
    echo "⚠️  Merge conflicts detected. Please resolve them manually."
    exit 1
fi

echo ""
echo "Step 4: Pushing changes to GitHub..."
git push origin main

echo ""
echo "✅ Done! Changes pushed to GitHub."

