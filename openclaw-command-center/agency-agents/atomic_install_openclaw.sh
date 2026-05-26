#!/usr/bin/env bash
set -euo pipefail

AGENCY_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
AGENTS_DIR="$OPENCLAW_DIR/agents"
AGENCY_WORKSPACE="$OPENCLAW_DIR/agency-agents"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

echo "==> Starting atomic agency-agents install for OpenClaw"
echo "    Agency dir: $AGENCY_DIR"
echo "    OpenClaw dir: $OPENCLAW_DIR"

# 1. Ensure base directories exist
mkdir -p "$AGENTS_DIR"
mkdir -p "$AGENCY_WORKSPACE"

# 2. Collect agent IDs from integrations/openclaw (exclude README.md)
mapfile -t AGENTS < <(ls -1 "$AGENCY_DIR/integrations/openclaw" | grep -v '^README.md$')
TOTAL=${#AGENTS[@]}
echo "==> Found $TOTAL agents to process"

# 3. Create directories and copy agent files (no config writes yet)
for agent in "${AGENTS[@]}"; do
  # Agent workspace
  mkdir -p "$AGENCY_WORKSPACE/$agent"
  # Agent sessions
  mkdir -p "$AGENTS_DIR/$agent/sessions"
  # Agent directory (copy if not already present)
  if [ ! -d "$AGENTS_DIR/$agent/agent" ]; then
    mkdir -p "$AGENTS_DIR/$agent/agent"
    cp -r "$AGENCY_DIR/integrations/openclaw/$agent/"* "$AGENTS_DIR/$agent/agent/" 2>/dev/null || true
  fi
done
echo "==> Agent directories and files copied."

# 4. Build the JSON config atomically
#    Start with a default config if not present, else read existing
if [ -f "$CONFIG_FILE" ]; then
  CONFIG=$(cat "$CONFIG_FILE")
else
  CONFIG='{"agents":{"defaults":{"workspace":"'"$OPENCLAW_DIR/worspace"'","models":{"openrouter/auto":{"alias":"OpenRouter"},"openrouter/free":{}},"model":{"primary":"openrouter/free"}},"list":[]}}'
fi

# Use jq to merge agents list (if jq not available, fallback to python)
if command -v jq &>/dev/null; then
  echo "==> Using jq to merge config"
  # Build list of agent objects
  AGENT_JSON=$(for agent in "${AGENTS[@]}"; do
    echo '{"id":"'"$agent"'","name":"'"$agent"'","workspace":"'"$AGENCY_WORKSPACE/$agent"'","agentDir":"'"$AGENTS_DIR/$agent/agent"'"}'
  done | jq -s '.')

  # Merge into config
  NEW_CONFIG=$(jq '.agents.list = '"$AGENT_JSON" <<<"$CONFIG")
  echo "$NEW_CONFIG" > "$CONFIG_FILE"
else
  echo "==> jq not found, using python3"
  python3 - <<EOF
import json, os, sys

config_path = "$CONFIG_FILE"
agents_dir = "$AGENTS_DIR"
agency_ws = "$AGENCY_WORKSPACE"

# Load or init config
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {
        "agents": {
            "defaults": {
                "workspace": os.path.expanduser("~/.openclaw/workspace"),
                "models": {
                    "openrouter/auto": {"alias": "OpenRouter"},
                    "openrouter/free": {}
                },
                "model": {"primary": "openrouter/free"}
            },
            "list": []
        }
    }

# Build agent entries
agent_list = []
for agent in ${AGENTS[@]};
    entry = {
        "id": agent,
        "name": agent,
        "workspace": os.path.join(agency_ws, agent),
        "agentDir": os.path.join(agents_dir, agent, "agent")
    }
    # Avoid duplicates
    if not any(e.get("id") == agent for e in config["agents"]["list"]):
        agent_list.append(entry)

# Append new agents
config["agents"]["list"].extend(agent_list)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("Config written with", len(config["agents"]["list"]), "total agents")
EOF
fi

echo "==> Atomic install complete. Config written once to $CONFIG_FILE"
echo "==> Total agents in config: $(jq '.agents.list | length' "$CONFIG_FILE" 2>/dev/null || echo 'unknown')"