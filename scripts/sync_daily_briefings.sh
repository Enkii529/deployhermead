#!/usr/bin/env bash
set -euo pipefail

# Sync daily AI briefings from cron output to shared Brain folder
SRC_DIR="${HOME}/hermes/cron/output/1493c05d3ee1"
DEST_DIR="/media/sf_ClawdbotShared/Brain/daily_briefings"

mkdir -p "$DEST_DIR"

# Only sync .md briefings (skip any temp files)
rsync -av --include="*.md" --exclude="*" "$SRC_DIR"/ "$DEST_DIR"/

echo "✅ Daily briefings synced to $DEST_DIR"