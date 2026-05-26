#!/bin/bash
# Verify ai-brief skill has required updates.
SKILL_PATH="$HOME/.hermes/skills/productivity/ai-brief/SKILL.md"
echo "Checking ai-brief skill updates..."
if [ ! -f "$SKILL_PATH" ]; then
    echo "ERROR: ai-brief skill not found at $SKILL_PATH"
    exit 1
fi
missing=0
grep -q "delegation.child_timeout_seconds" "$SKILL_PATH" || { echo "Missing: delegation.child_timeout_seconds reference"; missing=$((missing+1)); }
grep -q "Telegram media timeout" "$SKILL_PATH" || { echo "Missing: Telegram media timeout reference"; missing=$((missing+1)); }
grep -q "ffmpeg missing" "$SKILL_PATH" || { echo "Missing: ffmpeg missing note"; missing=$((missing+1)); }
if [ $missing -eq 0 ]; then
    echo "All required updates present."
else
    echo "Found $missing missing updates."
fi
