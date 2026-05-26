#!/usr/bin/env python3
"""
Queue Cleanup & Archive for Bot_Exchange.
Archives old done/failed tasks, checks queue thresholds.
"""
import os
import sys
import shutil
import tarfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BOT_EXCHANGE_ROOT = os.path.join(
    os.environ.get("APP_ROOT", "/media/sf_ClawdbotShared"),
    "Brain", "Bot_Exchange"
)
INBOX_DIR = os.path.join(BOT_EXCHANGE_ROOT, "queue", "inbox")
WORKING_DIR = os.path.join(BOT_EXCHANGE_ROOT, "queue", "working")
DONE_DIR = os.path.join(BOT_EXCHANGE_ROOT, "queue", "done")
FAILED_DIR = os.path.join(BOT_EXCHANGE_ROOT, "queue", "failed")
ARCHIVE_ROOT = os.path.join(BOT_EXCHANGE_ROOT, "archive")
ASSETS_ROOT = os.path.join(BOT_EXCHANGE_ROOT, "assets")

# Thresholds
INBOX_WARN = 100
WORKING_WARN = 50
# Archive anything older than 7 days
ARCHIVE_AGE_DAYS = 7
# Delete archives older than 30 days
ARCHIVE_KEEP_DAYS = 30

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def count_files(dir_path):
    if not os.path.isdir(dir_path):
        return 0
    return len([p for p in Path(dir_path).iterdir() if p.is_file()])

def archive_old_files(dir_path, archive_date_str):
    """Move files older than ARCHIVE_AGE_DAYS into a dated archive folder and compress."""
    if not os.path.isdir(dir_path):
        return 0
    cutoff = datetime.now() - timedelta(days=ARCHIVE_AGE_DAYS)
    to_archive = []
    for p in Path(dir_path).iterdir():
        if p.is_file():
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime < cutoff:
                to_archive.append(p)
    if not to_archive:
        return 0
    # Create archive subdirectory: archive/YYYY-MM-DD/
    archive_subdir = os.path.join(ARCHIVE_ROOT, archive_date_str, os.path.basename(dir_path))
    ensure_dir(archive_subdir)
    moved = 0
    for p in to_archive:
        try:
            shutil.move(str(p), os.path.join(archive_subdir, p.name))
            moved += 1
        except Exception as e:
            print(f"Error moving {p}: {e}", file=sys.stderr)
    # Compress the archive subdir into a tarball
    tar_path = os.path.join(ARCHIVE_ROOT, f"{archive_date_str}.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(archive_subdir, arcname=os.path.basename(archive_subdir))
    # Remove the uncompressed directory after archiving
    shutil.rmtree(archive_subdir, ignore_errors=True)
    return moved

def cleanup_old_archives():
    """Delete archive tarballs older than ARCHIVE_KEEP_DAYS."""
    cutoff = datetime.now() - timedelta(days=ARCHIVE_KEEP_DAYS)
    deleted = 0
    for p in Path(ARCHIVE_ROOT).glob("*.tar.gz"):
        if p.is_file():
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime < cutoff:
                try:
                    p.unlink()
                    deleted += 1
                except Exception as e:
                    print(f"Error deleting archive {p}: {e}", file=sys.stderr)
    return deleted

def main():
    log_lines = []
    timestamp = datetime.utcnow().isoformat() + "Z"
    archive_date_str = datetime.now().strftime("%Y-%m-%d")
    log_lines.append(f"=== Queue Cleanup {timestamp} ===")

    ensure_dir(ARCHIVE_ROOT)

    # Check queue counts
    inbox_count = count_files(INBOX_DIR)
    working_count = count_files(WORKING_DIR)
    done_count = count_files(DONE_DIR)
    failed_count = count_files(FAILED_DIR)

    log_lines.append(f"Queue counts: inbox={inbox_count}, working={working_count}, done={done_count}, failed={failed_count}")

    # Warnings for backlogs
    if inbox_count > INBOX_WARN:
        log_lines.append(f"WARNING: Inbox count {inbox_count} exceeds threshold {INBOX_WARN}")
    if working_count > WORKING_WARN:
        log_lines.append(f"WARNING: Working count {working_count} exceeds threshold {WORKING_WARN}")

    # Archive old done files
    done_archived = archive_old_files(DONE_DIR, archive_date_str)
    log_lines.append(f"Archived {done_archived} old files from DONE")

    # Archive old failed files
    failed_archived = archive_old_files(FAILED_DIR, archive_date_str)
    log_lines.append(f"Archived {failed_archived} old files from FAILED")

    # Optionally archive old assets (task outputs) older than 30 days
    # We'll treat assets as long-term storage; maybe archive to tar.gz and delete original?
    # For now, just count them.
    assets_count = count_files(ASSETS_ROOT)
    log_lines.append(f"Asset tasks count: {assets_count}")

    # Cleanup old archives
    archives_deleted = cleanup_old_archives()
    log_lines.append(f"Deleted {archives_deleted} old archive tarballs")

    log_lines.append("=== End Cleanup ===")

    for line in log_lines:
        print(line)

    sys.exit(0)

if __name__ == "__main__":
    main()