#!/bin/bash
# Wrapper invoked by launchd (or any cron-like scheduler) to run the
# daily refresh and push the result to GitHub. Loads .env automatically
# via daily.py. Idempotent — safe to run twice in a day; the dedup
# window in daily.py prevents re-publishing the same items.
#
# Schedule via launchd (preferred on macOS):
#   ~/Library/LaunchAgents/com.ppstacy.causal-ai-kb.daily.plist
# To install / reload:
#   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ppstacy.causal-ai-kb.daily.plist
# To check status:
#   launchctl print gui/$(id -u)/com.ppstacy.causal-ai-kb.daily

set -euo pipefail

REPO_DIR="/Users/jpan2/Projects/causal-ai-kb"
cd "$REPO_DIR"

# Make sure /opt/homebrew/bin is on PATH so `gh` and `git` resolve when
# launchd invokes us with a minimal environment.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

mkdir -p .logs
exec >> .logs/daily.out 2>> .logs/daily.err

echo "===== $(date -u +%FT%TZ) — daily-cron run ====="

.venv/bin/python scripts/daily.py

# Stage and commit only if there are changes
git add daily/ config/learned_keywords.yaml || true
if git diff --cached --quiet; then
  echo "no changes to commit"
  exit 0
fi
git commit -m "daily: $(date -u +%Y-%m-%d) (launchd)"
git push
echo "pushed."
