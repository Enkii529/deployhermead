#!/usr/bin/env python3
"""
Log Rotation & Cleanup.
Compresses old log files and deletes very old archives.
Targets:
- /home/openclaw/logs/
- /media/sf_ClawdbotShared/Brain/extracted-assets/logs/
- (Optionally) Hermes agent logs: /home/openclaw/.hermes/hermes-agent/logs if exists
"""
import os
import sys
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Directories to process
LOG_DIRS = [
    "/home/openclaw/logs",
    "/media/sf_ClawdbotShared/Brain/extracted-assets/logs",
    os.path.expanduser("~/.hermes/hermes-agent/logs"),
]

# Age thresholds (days)
COMPRESS_AGE_DAYS = 7   # compress .log files older than this
DELETE_AGE_DAYS = 30    # delete .gz files older than this

def compress_log_file(path):
    """Compress a .log file to .log.gz, preserving original mtime."""
    gz_path = str(path) + ".gz"
    try:
        with open(path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        # Copy original modification time to gz file
        mtime = os.stat(path).st_mtime
        os.utime(gz_path, (mtime, mtime))
        # Remove original after successful compression
        os.remove(path)
        return True
    except Exception as e:
        print(f"Failed to compress {path}: {e}", file=sys.stderr)
        return False

def delete_old_gz(path):
    """Delete a .gz file."""
    try:
        os.remove(path)
        return True
    except Exception as e:
        print(f"Failed to delete {path}: {e}", file=sys.stderr)
        return False

def main():
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"=== Log Cleanup {timestamp} ===")
    
    cutoff_compress = datetime.now() - timedelta(days=COMPRESS_AGE_DAYS)
    cutoff_delete = datetime.now() - timedelta(days=DELETE_AGE_DAYS)
    
    total_compressed = 0
    total_deleted = 0
    
    for log_dir in LOG_DIRS:
        if not os.path.isdir(log_dir):
            continue
        print(f"Scanning: {log_dir}")
        for entry in Path(log_dir).iterdir():
            if entry.is_file():
                # If it's a .log and older than compress threshold, compress it
                if entry.suffix == ".log":
                    mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                    if mtime < cutoff_compress:
                        if compress_log_file(entry):
                            total_compressed += 1
                            print(f"  Compressed: {entry.name}")
                # If it's a .gz and older than delete threshold, delete it
                elif entry.suffix == ".gz":
                    mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                    if mtime < cutoff_delete:
                        if delete_old_gz(entry):
                            total_deleted += 1
                            print(f"  Deleted: {entry.name}")
    
    print(f"Total log files compressed: {total_compressed}")
    print(f"Total archive files deleted: {total_deleted}")
    print("=== End Log Cleanup ===")
    sys.exit(0)

if __name__ == "__main__":
    main()