#!/bin/bash
set -e

SOURCE="/home/openclaw/hermes-command-center/daily_briefings/"
DEST="/media/sf_ClawdbotShared/outputs/daily-crypto-brief/"

# Ensure destination exists
mkdir -p "$DEST"

# Check source exists
if [ ! -d "$SOURCE" ]; then
  echo "ERROR: Source directory $SOURCE does not exist"
  exit 1
fi

# Sync files (mirror)
rsync -av --delete "$SOURCE" "$DEST"

echo "Successfully synced daily briefings from $SOURCE to $DEST at $(date)"
