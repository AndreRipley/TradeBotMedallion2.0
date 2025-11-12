#!/bin/bash
# Push current branch to TradeBotMedallion2.0 repository

set -e

REPO_DIR="/Users/andreripley/Desktop/TradeBot"
TARGET_REMOTE="medallion"
TARGET_URL="https://github.com/AndreRipley/TradeBotMedallion2.0.git"
BRANCH="main"

cd "$REPO_DIR"

echo "=========================================="
echo "Push to $TARGET_URL"
echo "=========================================="

echo "📦 Ensuring remote '$TARGET_REMOTE' points to $TARGET_URL"
if git remote | grep -q "^${TARGET_REMOTE}$"; then
  git remote set-url "$TARGET_REMOTE" "$TARGET_URL"
else
  git remote add "$TARGET_REMOTE" "$TARGET_URL"
fi

# Show current status
echo ""
echo "📋 Current git status:"
git status --short

echo ""
echo "📥 Fetching remote (if it exists)..."
if git ls-remote "$TARGET_REMOTE" &> /dev/null; then
  git fetch "$TARGET_REMOTE" || true
else
  echo "ℹ️  Remote appears to be empty or inaccessible yet; continuing."
fi

# Warn about divergence
echo ""
echo "⚠️  If the remote has divergent history, the push may be rejected."
echo "    Resolve by pulling/merging or using --force (with caution)."

# Push branch
echo ""
echo "📤 Pushing branch '$BRANCH' to '$TARGET_REMOTE'..."
if git push "$TARGET_REMOTE" "$BRANCH":"$BRANCH"; then
  echo ""
  echo "✅ Successfully pushed $BRANCH to $TARGET_REMOTE"
else
  echo ""
  echo "❌ Push failed. Review the messages above for details."
  echo "   If histories differ, consider synchronizing first:"
  echo "     git pull $TARGET_REMOTE $BRANCH"
  echo "   then re-run this script."
  exit 1
fi
