#!/usr/bin/env bash
set -euo pipefail

# Sync daily AI briefings from ai_brief output to shared Brain folder
SRC_DIR="${HOME}/hermes-command-center/daily_briefings"
DEST_DIR="/media/sf_ClawdbotShared/Brain/daily_briefings"

mkdir -p "$DEST_DIR"

# Sync transcript, worksheet, and audio files
rsync -av --include="transcript_*.md" --include="worksheet_*.md" --include="briefing_*.mp3" --include="audio_text_*.txt" --exclude="*" "$SRC_DIR"/ "$DEST_DIR"/

echo "✅ Daily briefings synced to $DEST_DIR"