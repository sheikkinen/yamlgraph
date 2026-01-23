#!/bin/bash
# Set GitHub Actions secrets for Daily Digest workflow
#
# Prerequisites:
#   brew install gh
#   gh auth login
#
# Usage:
#   cd examples/daily_digest
#   ./scripts/gh-secrets.sh

set -e

# === CONFIGURE THESE VALUES ===
FLY_APP_URL="https://your-app-name.fly.dev"
DIGEST_API_TOKEN="your-secret-token-from-fly-secrets"
RECIPIENT_EMAIL="you@example.com"
# ==============================

echo "Setting GitHub Actions secrets..."

gh secret set FLY_APP_URL --body "$FLY_APP_URL"
gh secret set DIGEST_API_TOKEN --body "$DIGEST_API_TOKEN"
gh secret set RECIPIENT_EMAIL --body "$RECIPIENT_EMAIL"

echo ""
echo "✅ All secrets set. Verify with: gh secret list"
echo ""
echo "To trigger manually: gh workflow run daily-digest.yml"
