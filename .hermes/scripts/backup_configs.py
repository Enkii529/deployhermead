#!/usr/bin/env python3
"""
Configuration Backup for Brain ecosystem.
Backs up critical configuration and code files daily.
Keeps last 30 compressed backups.
"""
import os
import sys
import tarfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Backup destinations
BACKUP_DIR = os.path.expanduser("~/hermes/backups")
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Paths to include (relative to root or absolute)
# We'll include:
# - ~/.hermes/config.yaml
# - ~/.hermes/agent_catalog.json
# - Command center panel: /media/sf_ClawdbotShared/Brain/command_center_panel/
# - Bot_Exchange bridge and workers: /media/sf_ClawdbotShared/Brain/Bot_Exchange/bridge.py and workers/
# Optionally, include Bot_Exchange/status/
APP_ROOT = os.environ.get("APP_ROOT", "/media/sf_ClawdbotShared")
INCLUDE_PATHS = [
    os.path.expanduser("~/.hermes/config.yaml"),
    os.path.expanduser("~/.hermes/agent_catalog.json"),
    os.path.join(APP_ROOT, "Brain", "command_center_panel"),
    os.path.join(APP_ROOT, "Brain", "Bot_Exchange", "bridge.py"),
    os.path.join(APP_ROOT, "Brain", "Bot_Exchange", "workers"),
    os.path.join(APP_ROOT, "Brain", "Bot_Exchange", "status"),
]

# Retention: keep 30 most recent backups
MAX_BACKUPS = 30

def should_include(path):
    """Check if path exists and should be included."""
    return os.path.exists(path)

def create_backup():
    date_str = datetime.now().strftime("%Y-%m-%d")
    tar_name = f"brain-config-backup-{date_str}.tar.gz"
    tar_path = os.path.join(BACKUP_DIR, tar_name)
    
    # Avoid overwriting existing backup for same day (unlikely)
    if os.path.exists(tar_path):
        print(f"Backup {tar_path} already exists, skipping.", file=sys.stderr)
        return 0
    
    print(f"Creating backup: {tar_path}")
    
    with tarfile.open(tar_path, "w:gz") as tar:
        for src in INCLUDE_PATHS:
            if should_include(src):
                arcname = os.path.basename(src) if os.path.isfile(src) else src
                try:
                    tar.add(src, arcname=arcname, recursive=True)
                    print(f"  Added: {src}")
                except Exception as e:
                    print(f"  Error adding {src}: {e}", file=sys.stderr)
            else:
                print(f"  Skipped (not found): {src}")
    
    return 1

def cleanup_old_backups():
    """Delete old backups to keep only MAX_BACKUPS most recent."""
    backups = sorted(Path(BACKUP_DIR).glob("brain-config-backup-*.tar.gz"), key=os.path.getmtime, reverse=True)
    to_delete = backups[MAX_BACKUPS:]
    deleted = 0
    for p in to_delete:
        try:
            p.unlink()
            deleted += 1
        except Exception as e:
            print(f"Error deleting backup {p}: {e}", file=sys.stderr)
    return deleted

def main():
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"=== Configuration Backup {timestamp} ===")
    
    created = create_backup()
    deleted = cleanup_old_backups()
    
    print(f"Backups created: {created}")
    print(f"Old backups deleted: {deleted}")
    print("=== End Backup ===")
    
    sys.exit(0)

if __name__ == "__main__":
    main()