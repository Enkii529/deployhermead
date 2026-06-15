#!/usr/bin/env python3
"""
brain_extract_links - Safe wrapper for gbrain link extraction
Read-only operation (extracts links, creates stub pages optionally).
Uses GBRAIN_HOME environment variable.
"""
import subprocess
import json
import sys
import os

GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"
WIKI_ROOT = os.path.join(BRAIN_ROOT, "wiki")


def run_gbrain_extract_links(stale_only: bool = False, create_stubs: bool = False, dry_run: bool = True) -> dict:
    """Run gbrain extract links."""
    env = os.environ.copy()
    env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
    env["GBRAIN_HOME"] = BRAIN_ROOT

    cmd = [GBRAIN_PATH, "extract"]

    if stale_only:
        cmd.append("--stale")

    if create_stubs:
        cmd.append("--create-stubs")

    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "dry_run": dry_run
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Link extraction timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract links from brain content")
    parser.add_argument("--stale", action="store_true", help="Only process pages not yet extracted")
    parser.add_argument("--create-stubs", action="store_true", help="Create stub pages for missing entities")
    parser.add_argument("--apply", action="store_true", help="Actually create stubs (default dry-run)")

    args = parser.parse_args()

    dry_run = not args.apply
    result = run_gbrain_extract_links(args.stale, args.create_stubs, dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()