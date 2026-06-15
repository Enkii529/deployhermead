#!/usr/bin/env python3
"""
brain_put_page - Safe wrapper for gbrain page creation/update
WRITE OPERATION - Includes all safety controls:
- Slug validator
- Duplicate check before page creation
- Dry-run mode
- Backup/rollback folder for modified pages
- Write lock file
- Kill switch config for signal detector
Uses GBRAIN_HOME environment variable.
"""
import subprocess
import json
import sys
import os
import re
import shutil
import fcntl
import time
from pathlib import Path
from datetime import datetime
import getpass
import socket

GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"
WIKI_ROOT = os.path.join(BRAIN_ROOT, "wiki")
BACKUP_ROOT = os.path.join(BRAIN_ROOT, ".brain_backups")
LOCK_FILE = os.path.join(BRAIN_ROOT, ".brain_write.lock")
KILL_SWITCH_FILE = os.path.join(BRAIN_ROOT, ".brain_kill_switch")
AUDIT_LOG_FILE = os.path.join(BRAIN_ROOT, "system_registry", "brain_write_audit.jsonl")

# Actor info
ACTOR_USER = getpass.getuser()
ACTOR_HOST = socket.gethostname()
ACTOR_PID = os.getpid()


# Kill switch check
def check_kill_switch() -> bool:
    """Check if kill switch is active (file exists = writes disabled)."""
    return os.path.exists(KILL_SWITCH_FILE)


# Write lock
class WriteLock:
    def __init__(self, lock_path: str, timeout: int = 30):
        self.lock_path = lock_path
        self.timeout = timeout
        self.lock_fd = None

    def acquire(self) -> bool:
        """Acquire exclusive write lock."""
        try:
            self.lock_fd = open(self.lock_path, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n{time.time()}\n")
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            return False

    def release(self):
        """Release write lock."""
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
            raise RuntimeError("Could not acquire write lock - another write in progress")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Slug validator
def validate_slug(slug: str) -> tuple[bool, str]:
    """Validate slug format: lowercase, hyphens, alphanumeric only."""
    if not slug:
        return False, "Slug cannot be empty"
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        return False, "Slug must be lowercase alphanumeric with hyphens only (e.g., 'my-page-name')"
    if len(slug) > 100:
        return False, "Slug too long (max 100 chars)"
    if slug.startswith('-') or slug.endswith('-'):
        return False, "Slug cannot start or end with hyphen"
    if '--' in slug:
        return False, "Slug cannot contain consecutive hyphens"
    return True, ""


# Duplicate check with case normalization
def normalize_slug(slug: str) -> str:
    """Normalize slug for comparison: lowercase, collapse hyphens, strip."""
    slug = slug.lower()
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def find_existing_page(page_type: str, slug: str) -> str | None:
    """Find existing page with case-insensitive matching."""
    normalized_slug = normalize_slug(slug)
    type_dir = os.path.join(WIKI_ROOT, page_type)
    if not os.path.exists(type_dir):
        return None
    for fname in os.listdir(type_dir):
        if fname.endswith('.md'):
            existing_slug = normalize_slug(fname[:-3])  # remove .md
            if existing_slug == normalized_slug:
                return os.path.join(type_dir, fname)
    return None


# Duplicate check
def check_duplicate(page_type: str, slug: str) -> tuple[bool, str]:
    """Check if page already exists in wiki structure (case-insensitive)."""
    page_path = os.path.join(WIKI_ROOT, page_type, f"{slug}.md")
    if os.path.exists(page_path):
        return True, f"Page already exists at {page_path}"
    
    # Case-insensitive check for legacy pages
    existing = find_existing_page(page_type, slug)
    if existing:
        return True, f"Page already exists (case variant) at {existing}"
    
    return False, ""


# Backup/rollback
def create_backup(page_path: str) -> str:
    """Create timestamped backup of existing page."""
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel_path = os.path.relpath(page_path, BRAIN_ROOT)
    backup_name = f"{rel_path.replace('/', '_')}.{timestamp}.bak"
    backup_path = os.path.join(BACKUP_ROOT, backup_name)
    shutil.copy2(page_path, backup_path)
    return backup_path


def write_audit_log(action: str, slug: str, dry_run: bool, success: bool, files_changed: list, backup_path: str = None, error: str = None):
    """Write audit log entry to JSONL file."""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": "brain_put_page",
        "action": action,  # "create" or "update"
        "slug": slug,
        "dry_run": dry_run,
        "apply": not dry_run,
        "actor": {
            "user": ACTOR_USER,
            "host": ACTOR_HOST,
            "pid": ACTOR_PID
        },
        "files_changed": files_changed,
        "backup_path": backup_path,
        "success": success,
        "error": error
    }
    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def run_gbrain_put(title: str, content: str, page_type: str, tags: list = None, dry_run: bool = False, slug: str = None) -> dict:
    """Run gbrain put page with safety controls."""
    env = os.environ.copy()
    env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
    env["GBRAIN_HOME"] = BRAIN_ROOT

    # Generate slug from title if not provided
    if slug is None:
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        slug = re.sub(r'-+', '-', slug)

    # Validate slug
    valid, msg = validate_slug(slug)
    if not valid:
        write_audit_log("create", slug, dry_run, False, [], None, f"Invalid slug: {msg}")
        return {"success": False, "error": f"Invalid slug: {msg}", "slug": slug}

    # Check duplicate - only block in dry-run mode; allow updates in apply mode
    exists, msg = check_duplicate(page_type, slug)
    if exists and dry_run:
        write_audit_log("create", slug, dry_run, False, [], None, f"Duplicate page: {msg}")
        return {"success": False, "error": f"Duplicate page: {msg}", "slug": slug, "exists": True}
    elif exists and not dry_run:
        # In apply mode, allow update - will create backup below
        pass

    # Determine wiki path
    wiki_path = os.path.join(WIKI_ROOT, page_type, f"{slug}.md")

    # Build frontmatter (no slug - gbrain derives from file path)
    frontmatter = f"---\ntitle: \"{title}\"\ntype: {page_type}\ncreated: {datetime.now().isoformat()}\n"
    if tags:
        frontmatter += f"tags: {json.dumps(tags)}\n"
    frontmatter += "---\n\n"

    full_content = frontmatter + f"# {title}\n\n" + content

    if dry_run:
        write_audit_log("create", slug, dry_run, True, [wiki_path], None, None)
        return {
            "success": True,
            "dry_run": True,
            "slug": slug,
            "wiki_path": wiki_path,
            "preview": full_content[:500] + ("..." if len(full_content) > 500 else ""),
            "message": "DRY RUN - No changes made. Use --apply to write."
        }

    # Kill switch check
    if check_kill_switch():
        write_audit_log("create", slug, dry_run, False, [], None, "KILL SWITCH ACTIVE - Writes disabled")
        return {"success": False, "error": "KILL SWITCH ACTIVE - Writes disabled"}

    # Acquire write lock
    lock = WriteLock(LOCK_FILE)
    if not lock.acquire():
        write_audit_log("create", slug, dry_run, False, [], None, "Could not acquire write lock")
        return {"success": False, "error": "Could not acquire write lock - another write in progress"}

    try:
        # Create backup if file exists
        backup_path = None
        files_changed = [wiki_path]
        if os.path.exists(wiki_path):
            backup_path = create_backup(wiki_path)
            files_changed = [wiki_path, backup_path]

        # Write page
        os.makedirs(os.path.dirname(wiki_path), exist_ok=True)
        with open(wiki_path, 'w') as f:
            f.write(full_content)

        # Re-index with gbrain
        cmd = [GBRAIN_PATH, "import", WIKI_ROOT, "--no-embed"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)

        write_audit_log("create", slug, dry_run, True, files_changed, backup_path, None)

        return {
            "success": True,
            "dry_run": False,
            "slug": slug,
            "wiki_path": wiki_path,
            "backup_path": backup_path,
            "reindex_stdout": result.stdout,
            "reindex_stderr": result.stderr,
            "reindex_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        write_audit_log("create", slug, dry_run, False, [], None, "Re-index timed out after 60s")
        return {"success": False, "error": "Re-index timed out after 60s"}
    except Exception as e:
        write_audit_log("create", slug, dry_run, False, [], None, str(e))
        return {"success": False, "error": str(e)}
    finally:
        lock.release()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Safe brain page creation with safety controls")
    parser.add_argument("title", help="Page title")
    parser.add_argument("content", help="Page content (markdown)")
    parser.add_argument("--type", default="concepts", help="Page type/wiki directory (default: concepts)")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--apply", action="store_true", help="Actually write (default is dry-run)")
    parser.add_argument("--slug", help="Custom slug (auto-generated from title if not provided)")

    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

    # Kill switch check
    if check_kill_switch():
        result = {"success": False, "error": "KILL SWITCH ACTIVE - Writes disabled"}
        print(json.dumps(result, indent=2))
        return

    dry_run = not args.apply
    result = run_gbrain_put(args.title, args.content, args.type, tags, dry_run, args.slug)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()