#!/usr/bin/env python3
"""
brain_get_page - Safe wrapper for gbrain page retrieval
Read-only operation, no write lock needed.
Uses GBRAIN_HOME environment variable.
"""
import subprocess
import json
import sys
import os

GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"


def run_gbrain_get_page(page_id: str) -> dict:
    """Run gbrain get page and return parsed results."""
    env = os.environ.copy()
    env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
    env["GBRAIN_HOME"] = BRAIN_ROOT

    cmd = [GBRAIN_PATH, "get", page_id]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        return {
            "success": result.returncode == 0,
            "page_id": page_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Get page timed out after 30s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: brain_get_page.py <page_id>")
        sys.exit(1)

    page_id = sys.argv[1]
    result = run_gbrain_get_page(page_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()