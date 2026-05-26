#!/usr/bin/env bash
set -euo pipefail

# Configuration
BACKUP_DIR="${HOME}/hermes-agent-backup"
GIT_REMOTE="${GITHUB_BACKUP_AGENT_REMOTE:-git@github.com-deployhermead:Enkii529/deployhermead.git}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Sources to backup (adjust paths if your setup differs)
SOURCES=(
  "${HOME}/hermes-command-center"
  "${HOME}/openclaw-command-center"
  "${HOME}/.hermes"
  "${HOME}/hermes/scripts"
)

# Exclusion patterns (common caches, envs, large binaries, secrets)
EXCLUDE_PATTERNS=(
  ".git" "node_modules" "__pycache__" ".pytest_cache"
  ".venv" "venv" "env" ".env" ".env.*"
  "logs" "cache" "tmp" "temp"
  ".DS_Store" "Thumbs.db"
  "*.pyc" "*.pyo" "*.pyd" "*.swp" "*.swo" "*~"
  ".idea" ".vscode" "*.code-workspace"
  "dist" "build" "target" ".tox" ".coverage" "htmlcov" ".cache"
  ".npm" ".yarn" "package-lock.json" "yarn.lock"
  "Pipfile.lock" "poetry.lock" "Cargo.lock" "go.sum"
  ".terraform" ".vagrant" ".docker"
  ".ssh"
  "*.onnx" "*.ckpt" "*.safetensors" "*.bin" "*.pt" "*.pth"
  "kokoro_models" "models" "checkpoints"
)

# Temporary exclude file
EXCLUDE_FILE="$(mktemp)"
trap 'rm -f "$EXCLUDE_FILE"' EXIT
for pat in "${EXCLUDE_PATTERNS[@]}"; do
  echo "- $pat" >> "$EXCLUDE_FILE"
done

# Rsync each source
for src in "${SOURCES[@]}"; do
  if [ -e "$src" ]; then
    dest="${BACKUP_DIR}/$(basename "$src")"
    mkdir -p "$dest"
    rsync -av --delete --exclude-from="$EXCLUDE_FILE" "$src"/ "$dest"/
  else
    echo "Warning: source $src missing, skipping."
  fi
done

# Save crontab (comment out existing lines to avoid accidental execution on restore)
mkdir -p "${BACKUP_DIR}/config"
crontab -l 2>/dev/null | sed 's/^/# /' > "${BACKUP_DIR}/config/user_crontab.txt" || true

# Git setup
cd "$BACKUP_DIR"
if [ ! -d ".git" ]; then
  git init
  git branch -M main
  git remote add origin "$GIT_REMOTE"
  git config user.email "automationsopenclaw@gmail.com"
  git config user.name "Enzo"
fi

# Commit if changes
git add -A
if git diff-index --quiet HEAD --; then
  echo "No changes to commit."
else
  git commit -m "Nightly Hermes agent backup $(date +%Y-%m-%d)"
  git push origin main
fi

echo "✅ Hermes agent backup completed."
