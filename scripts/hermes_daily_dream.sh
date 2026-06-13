#!/bin/bash
# Hermes Daily Dream Consolidation wrapper
# Calls the native Python consolidation script from hermes-dream-consolidation skill

set -e

SKILL_DIR="/home/openclaw/hermes/skills/devops/hermes-dream-consolidation"
DREAM_SCRIPT="$SKILL_DIR/scripts/dream.py"

if [ ! -f "$DREAM_SCRIPT" ]; then
    echo "ERROR: Dream consolidation script not found at $DREAM_SCRIPT"
    exit 1
fi

# Run the consolidation
python3 "$DREAM_SCRIPT"