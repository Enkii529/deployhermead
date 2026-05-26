#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Hermes agent deployment..."

# 1. Copy backed-up directories back to the home folder.
echo "📦 Copying files..."
cp -r hermes-command-center "$HOME/" 2>/dev/null || true
cp -r openclaw-command-center "$HOME/" 2>/dev/null || true
cp -r .hermes "$HOME/" 2>/dev/null || true
cp -r scripts "$HOME/hermes/" 2>/dev/null || true

# 2. Restore crontab (un-comment saved lines) if present.
if [ -f config/user_crontab.txt ]; then
  echo "⏰ Restoring crontab..."
  crontab config/user_crontab.txt 2>/dev/null || true
fi

# 3. Create output folder for daily briefings (if missing)
mkdir -p "$HOME/hermes-command-center/daily_briefings"

# 4. Permissions (adjust as needed)
chmod -R u+rwX,go+rX,go-w "$HOME/hermes-command-center" "$HOME/openclaw-command-center" "$HOME/.hermes" "$HOME/hermes" 2>/dev/null || true

echo "✅ Deployment finished."
echo "→ Next steps:"
echo " - Restart your Hermes agent (e.g., systemctl --user restart hermes or reboot)"
echo " - Ensure the Brain is mounted at /media/sf_ClawdbotShared"
echo " - Test with a brief: hermes --skill ai-brief"
