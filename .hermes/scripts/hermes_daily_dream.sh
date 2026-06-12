#!/bin/bash
# Hermes daily dream consolidation wrapper
# Checks conditions via should-dream.sh, then runs Python consolidation

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILLS_DIR="$HOME/hermes/skills"
SHOULD_DREAM="$SKILLS_DIR/devops/hermes-dream-consolidation/scripts/should-dream.sh"
DREAM_PY="$SKILLS_DIR/devops/hermes-dream-consolidation/scripts/dream.py"

# Run condition check
if ! bash "$SHOULD_DREAM"; then
    echo "$(date): Conditions not met for dream consolidation — skipping"
    exit 0
fi

# Run consolidation
echo "$(date): Starting Hermes memory consolidation"
python3 "$DREAM_PY"
