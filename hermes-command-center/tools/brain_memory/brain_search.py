#!/usr/bin/env python3
"""
brain_search - Safe wrapper for gbrain keyword search
Read-only operation, no write lock needed.
Uses GBRAIN_HOME environment variable.
"""
import subprocess
import json
import sys
import os

GBRAIN_PATH = os.path.expanduser("~/.bun/bin/gbrain")
BRAIN_ROOT = "/media/sf_ClawdbotShared/Brain"


def run_gbrain_search(query: str, limit: int = 10) -> dict:
    """Run gbrain search and return parsed results."""
    env = os.environ.copy()
    env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
    env["GBRAIN_HOME"] = BRAIN_ROOT

    cmd = [GBRAIN_PATH, "search", query, "--limit", str(limit)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        return {
            "success": result.returncode == 0,
            "query": query,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Search timed out after 30s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: brain_search.py <query> [--limit N]")
        sys.exit(1)

    query = sys.argv[1]
    limit = 10
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    result = run_gbrain_search(query, limit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()