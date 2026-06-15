#!/usr/bin/env python3
"""
brain_add_timeline_entry - Safe wrapper for adding timeline entries to entity pages
WRITE OPERATION - Includes safety controls (lock, backup, kill switch).
Uses GBRAIN_HOME environment variable.
"""
import subprocess
import json
import sys
import os
import fcntl
import time
from pathlib import Path
from datetime import datetime

GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"
WIKI_ROOT = os.path.join(BRAIN_ROOT, "wiki")
BACKUP_ROOT = os.path.join(BRAIN_ROOT, ".brain_backups")
LOCK_FILE = os.path.join(BRAIN_ROOT, ".brain_write.lock")
KILL_SWITCH_FILE = os.path.join(BRAIN_ROOT, ".brain_kill_switch")


def check_kill_switch() -> bool:
    return os.path.exists(KILL_SWITCH_FILE)


class WriteLock:
    def __init__(self, lock_path: str, timeout: int = 30):
        self.lock_path = lock_path
        self.timeout = timeout
        self.lock_fd = None

    def acquire(self) -> bool:
        try:
            self.lock_fd = open(self.lock_path, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n{time.time()}\n")
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            return False

    def release(self):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            except:
                pass
            self.lock_fd.close()
            self.lock_fd = None
            try:
                os.remove(self.lock_path)
            except:
                pass

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Could not acquire write lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def create_backup(page_path: str) -> str:
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel_path = os.path.relpath(page_path, BRAIN_ROOT)
    backup_name = f"{rel_path.replace('/', '_')}.{timestamp}.bak"
    backup_path = os.path.join(BACKUP_ROOT, backup_name)
    import shutil
    shutil.copy2(page_path, backup_path)
    return backup_path


def find_page_path(entity_type: str, entity_slug: str) -> str | None:
    """Find page path, checking both type subdirectory and wiki root."""
    # Check type subdirectory first
    page_path = os.path.join(WIKI_ROOT, entity_type, f"{entity_slug}.md")
    if os.path.exists(page_path):
        return page_path
    # Check wiki root (legacy pages)
    page_path = os.path.join(WIKI_ROOT, f"{entity_slug}.md")
    if os.path.exists(page_path):
        return page_path
    return None


def add_timeline_entry(entity_type: str, entity_slug: str, date: str, event: str, source: str = "", dry_run: bool = False) -> dict:
    """Add a timeline entry to an entity page."""
    # Validate entity type
    valid_types = ["people", "companies", "concepts", "projects", "meetings", "originals", "ideas", "personal", "patterns", "media"]
    if entity_type not in valid_types:
        return {"success": False, "error": f"Invalid entity type. Must be one of: {valid_types}"}

    page_path = find_page_path(entity_type, entity_slug)

    if not page_path:
        return {"success": False, "error": f"Entity page not found for {entity_type}/{entity_slug}"}

    # Read current page
    with open(page_path, 'r') as f:
        content = f.read()

    # Parse frontmatter and body
    frontmatter = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            import yaml
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except:
                pass
            body = parts[2]

    # Find or create timeline section
    timeline_marker = "## Timeline"
    if timeline_marker not in body:
        # Add timeline section at end
        new_body = body.rstrip() + f"\n\n{timeline_marker}\n\n"
    else:
        new_body = body

    # Format timeline entry
    entry = f"- **{date}**: {event}"
    if source:
        entry += f" [[Source: {source}]]"

    # Insert after timeline marker
    if timeline_marker in new_body:
        idx = new_body.index(timeline_marker) + len(timeline_marker)
        new_body = new_body[:idx] + f"\n{entry}" + new_body[idx:]
    else:
        new_body = new_body + f"\n{entry}"

    # Reconstruct full content
    import yaml
    new_frontmatter = "---\n" + yaml.dump(frontmatter, sort_keys=False) + "---\n"
    new_content = new_frontmatter + new_body

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "entity_type": entity_type,
            "entity_slug": entity_slug,
            "preview": f"Would add to {page_path}:\n{entry}",
            "message": "DRY RUN - No changes made. Use --apply to write."
        }

    # Kill switch check
    if check_kill_switch():
        return {"success": False, "error": "KILL SWITCH ACTIVE - Writes disabled"}

    # Acquire lock and write
    lock = WriteLock(LOCK_FILE)
    if not lock.acquire():
        return {"success": False, "error": "Could not acquire write lock"}

    try:
        backup_path = create_backup(page_path)
        with open(page_path, 'w') as f:
            f.write(new_content)

        # Re-index
        env = os.environ.copy()
        env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
        env["GBRAIN_HOME"] = BRAIN_ROOT
        cmd = [GBRAIN_PATH, "import", WIKI_ROOT, "--no-embed"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)

        return {
            "success": True,
            "dry_run": False,
            "entity_type": entity_type,
            "entity_slug": entity_slug,
            "page_path": page_path,
            "backup_path": backup_path,
            "entry_added": entry,
            "reindex_code": result.returncode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        lock.release()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add timeline entry to entity page")
    parser.add_argument("entity_type", help="Entity type (people, companies, concepts, projects, meetings)")
    parser.add_argument("entity_slug", help="Entity slug (e.g., 'jason-smith')")
    parser.add_argument("date", help="Date (YYYY-MM-DD or ISO format)")
    parser.add_argument("event", help="Event description")
    parser.add_argument("--source", help="Source reference")
    parser.add_argument("--apply", action="store_true", help="Actually write (default dry-run)")

    args = parser.parse_args()

    dry_run = not args.apply
    result = add_timeline_entry(args.entity_type, args.entity_slug, args.date, args.event, args.source, dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()