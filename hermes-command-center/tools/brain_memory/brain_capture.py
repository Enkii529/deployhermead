#!/usr/bin/env python3
"""
brain_capture - Analyze text and propose OR APPLY brain captures
Supports --apply mode to safely write proposed pages.
All safety controls enforced.
"""
import json
import sys
import os
import re
import subprocess
import shutil
import getpass
import socket
import fcntl
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Constants
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"
WIKI_ROOT = os.path.join(BRAIN_ROOT, "wiki")
KILL_SWITCH_FILE = os.path.join(BRAIN_ROOT, ".brain_kill_switch")
LOCK_FILE = os.path.join(BRAIN_ROOT, ".brain_write.lock")
BACKUP_ROOT = os.path.join(BRAIN_ROOT, ".brain_backups")
GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
AUDIT_LOG_FILE = os.path.join(BRAIN_ROOT, "system_registry", "brain_write_audit.jsonl")

ACTOR_USER = getpass.getuser()
ACTOR_HOST = socket.gethostname()
ACTOR_PID = os.getpid()

# Entity patterns for extraction
ENTITY_PATTERNS = {
    "people": [
        r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
        r'@([A-Za-z0-9_]+)',
    ],
    "companies": [
        r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)\s+(?:Inc|LLC|Corp|Ltd|Corporation|Company)\b',
        r'\b(?:OpenAI|Anthropic|Google|Microsoft|Amazon|Meta|NVIDIA|Tesla|SpaceX)\b',
    ],
    "concepts": [
        r'\b(?:RAG|LLM|API|MCP|PGLite|gbrain|Hermes|n8n|Docker|Kubernetes|Python|TypeScript|JavaScript)\b',
        r'\b(?:vector search|embedding|fine-tuning|LoRA|quantization|inference|training)\b',
    ],
    "projects": [
        r'\b(?:Phase \d+[A-Z]?|Project [A-Z][a-z]+|Operation [A-Z][a-z]+)\b',
    ],
}

WIKI_TYPES = ["originals", "concepts", "people", "companies", "meetings", "media", "ideas", "personal", "patterns", "sources"]

# Safety controls
def validate_slug(slug: str) -> tuple[bool, str]:
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
            raise RuntimeError("Could not acquire write lock - another write in progress")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def create_backup(page_path: str) -> str:
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel_path = os.path.relpath(page_path, BRAIN_ROOT)
    backup_name = f"{rel_path.replace('/', '_')}.{timestamp}.bak"
    backup_path = os.path.join(BACKUP_ROOT, backup_name)
    shutil.copy2(page_path, backup_path)
    return backup_path


def write_audit_log(action: str, slug: str, dry_run: bool, success: bool, files_changed: list, backup_path: str = None, error: str = None, command: str = "brain_capture"):
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "action": action,
        "slug": slug,
        "dry_run": dry_run,
        "apply": not dry_run,
        "actor": {"user": ACTOR_USER, "host": ACTOR_HOST, "pid": ACTOR_PID},
        "files_changed": files_changed,
        "backup_path": backup_path,
        "success": success,
        "error": error
    }
    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')


# Legacy duplicate detection helpers
def normalize_slug(slug: str) -> str:
    slug = slug.lower()
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug

def find_existing_page(page_type: str, slug: str) -> str | None:
    normalized_slug = normalize_slug(slug)
    type_dir = os.path.join(WIKI_ROOT, page_type)
    if not os.path.exists(type_dir):
        return None
    for fname in os.listdir(type_dir):
        if fname.endswith('.md'):
            existing_slug = normalize_slug(fname[:-3])
            if existing_slug == normalized_slug:
                return os.path.join(type_dir, fname)
    return None


# Apply helpers
def apply_new_page(page: dict) -> dict:
    page_type = page["type"]
    slug = page["slug"]
    title = page["name"]
    content = f"# {title}\n\nCreated via brain_capture --apply.\n\n## Notes\n\nThis page was auto-generated from entity extraction. Expand and refine as needed.\n"
    
    wiki_path = os.path.join(WIKI_ROOT, page_type, f"{slug}.md")
    
    # Validate slug
    valid, msg = validate_slug(slug)
    if not valid:
        write_audit_log("create", slug, False, False, [], None, f"Invalid slug: {msg}", "brain_capture")
        return {"success": False, "error": f"Invalid slug: {msg}", "slug": slug, "page": page}
    
    # Check duplicate (case-insensitive)
    page_path = os.path.join(WIKI_ROOT, page_type, f"{slug}.md")
    if os.path.exists(page_path):
        existing = find_existing_page(page_type, slug)
        if existing:
            write_audit_log("create", slug, False, False, [], None, f"Duplicate page: exists at {existing}", "brain_capture")
            return {"success": False, "error": f"Duplicate page: exists at {existing}", "slug": slug, "page": page}
        return {"success": False, "error": f"Duplicate page: {page_path}", "slug": slug, "page": page}
    
    # Kill switch
    if check_kill_switch():
        write_audit_log("create", slug, False, False, [], None, "KILL SWITCH ACTIVE - Writes disabled", "brain_capture")
        return {"success": False, "error": "KILL SWITCH ACTIVE - Writes disabled", "slug": slug, "page": page}
    
    # Acquire lock
    lock = WriteLock(LOCK_FILE)
    if not lock.acquire():
        write_audit_log("create", slug, False, False, [], None, "Could not acquire write lock", "brain_capture")
        return {"success": False, "error": "Could not acquire write lock - another write in progress", "slug": slug, "page": page}
    
    try:
        frontmatter = f"---\ntitle: \"{title}\"\ntype: {page_type}\ncreated: {datetime.now().isoformat()}\nsource: capture\n---\n\n"
        full_content = frontmatter + f"# {title}\n\n" + content
        
        os.makedirs(os.path.dirname(wiki_path), exist_ok=True)
        with open(wiki_path, 'w') as f:
            f.write(full_content)
        
        # Reindex with gbrain
        env = os.environ.copy()
        env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
        env["GBRAIN_HOME"] = BRAIN_ROOT
        cmd = [GBRAIN_PATH, "import", WIKI_ROOT, "--no-embed"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
        
        write_audit_log("create", slug, False, True, [wiki_path], None, None, "brain_capture")
        
        return {"success": True, "slug": slug, "page_type": page_type, "path": wiki_path, "reindex_code": result.returncode, "action": "created"}
    except Exception as e:
        write_audit_log("create", slug, False, False, [], None, str(e), "brain_capture")
        return {"success": False, "error": str(e), "slug": slug, "page": page}
    finally:
        lock.release()


def apply_captures(proposals: dict, dry_run: bool) -> dict:
    if dry_run:
        return {
            "dry_run": True,
            "would_create": len(proposals["new_pages"]),
            "would_add_timeline": len(proposals["timeline_entries"]),
            "would_preserve_source": 1 if proposals["source_preservation"] else 0,
            "pages": [],
            "timeline_entries": [],
            "source_preserved": False
        }
    
    results = {"dry_run": False, "pages_created": [], "timeline_entries_added": [], "source_preserved": None, "files_modified": []}
    
    # Create new pages
    for page in proposals["new_pages"]:
        result = apply_new_page(page)
        if result["success"]:
            results["pages_created"].append(result)
            results["files_modified"].append(result["path"])
        else:
            results.setdefault("errors", []).append(result)
    
    # Preserve source
    if proposals["source_preservation"]:
        source_info = proposals["source_preservation"][0] if proposals["source_preservation"] else None
        if source_info:
            raw_dir = os.path.join(WIKI_ROOT, "sources", ".raw")
            os.makedirs(raw_dir, exist_ok=True)
            raw_path = source_info["proposed_raw_path"]
            try:
                with open(raw_path, 'w') as f:
                    f.write(f"# Source Capture\n\n**Text:**\n\n{source_info['source_text']}\n\n**Metadata:**\n\n- timestamp: {source_info['timestamp']}\n- source: {source_info['source_type']}\n")
                write_audit_log("source_preserve", "capture_source", False, True, [raw_path], None, None, "brain_capture")
                results["source_preserved"] = raw_path
                results["files_modified"].append(raw_path)
            except Exception as e:
                write_audit_log("source_preserve", "capture_source", False, False, [], None, str(e), "brain_capture")
                results.setdefault("errors", []).append({"error": str(e), "type": "source_preserve"})
    
    return results


# Original extraction functions
def extract_entities(text: str) -> dict:
    entities = {k: set() for k in ENTITY_PATTERNS.keys()}
    for etype, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                match = match.strip()
                if len(match) > 1:
                    entities[etype].add(match)
    return {k: list(v) for k, v in entities.items()}


def check_existing_pages(entities: dict) -> dict:
    existing = {}
    for etype, names in entities.items():
        existing[etype] = {}
        type_dir = os.path.join(WIKI_ROOT, etype)
        if os.path.exists(type_dir):
            for name in names:
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                slug = re.sub(r'-+', '-', slug)
                page_path = os.path.join(type_dir, f"{slug}.md")
                existing[etype][name] = {"slug": slug, "exists": os.path.exists(page_path), "path": page_path}
        else:
            for name in names:
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                slug = re.sub(r'-+', '-', slug)
                existing[etype][name] = {"slug": slug, "exists": False, "path": os.path.join(type_dir, f"{slug}.md")}
    return existing


def propose_captures(text: str, source: str = "manual_capture") -> dict:
    entities = extract_entities(text)
    existing = check_existing_pages(entities)
    
    proposals = {"new_pages": [], "timeline_entries": [], "links_to_create": [], "source_preservation": []}
    
    # New pages
    for etype, items in existing.items():
        for name, info in items.items():
            if not info["exists"]:
                proposals["new_pages"].append({"type": etype, "name": name, "slug": info["slug"], "path": info["path"], "action": "create_stub"})
    
    # Timeline entries for dates
    date_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
    dates = re.findall(date_pattern, text)
    if dates:
        for etype in ["projects", "concepts"]:
            for name, info in existing.get(etype, {}).items():
                if info["exists"]:
                    proposals["timeline_entries"].append({
                        "entity_type": etype, "entity_slug": info["slug"], "date": dates[0],
                        "event": f"Mentioned in capture: {text[:100]}...", "source": source
                    })
    
    # Links to existing pages
    for etype, items in existing.items():
        for name, info in items.items():
            if info["exists"]:
                proposals["links_to_create"].append({"from_page": "current_capture", "to_page": info["path"], "link_text": name, "type": "wikilink"})
    
    # Source preservation
    proposals["source_preservation"].append({
        "source_text": text,
        "source_type": source,
        "timestamp": datetime.now().isoformat(),
        "proposed_raw_path": os.path.join(WIKI_ROOT, "sources", ".raw", f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    })
    
    return {"timestamp": datetime.now().isoformat(), "source": source, "text_analyzed": text[:500] + ("..." if len(text) > 500 else ""),
            "entities_found": entities, "existing_pages": existing, "proposals": proposals, "dry_run": True, "kill_switch_active": check_kill_switch()}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze text and propose OR APPLY brain captures")
    parser.add_argument("text", nargs="*", help="Text to analyze (if empty, reads from stdin)")
    parser.add_argument("--source", default="manual_capture", help="Source identifier")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--apply", action="store_true", help="Actually write proposed pages (default is dry-run)")
    
    args = parser.parse_args()
    
    if args.stdin:
        text = sys.stdin.read()
    elif args.text:
        text = " ".join(args.text)
    else:
        print("Usage: brain_capture.py \"text to analyze\" or --stdin")
        sys.exit(1)
    
    result = propose_captures(text, args.source)
    
    if args.apply:
        apply_result = apply_captures(result["proposals"], dry_run=False)
        result["apply_result"] = apply_result
        result["dry_run"] = False
    else:
        # Include dry-run counts for user info
        result["proposals_summary"] = {"would_create": len(result["proposals"]["new_pages"]), "would_add_timeline": len(result["proposals"]["timeline_entries"])}
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
