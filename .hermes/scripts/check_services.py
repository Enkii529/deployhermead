#!/usr/bin/env python3
"""
Service Health Monitor for Brain ecosystem.
Checks if critical services are running and logs status.
Alerts: If any service is down, logs CRITICAL and exits with code 1.
"""
import os
import sys
import subprocess
import json
from datetime import datetime

# Configure services to monitor (name -> process pattern)
SERVICES = {
    "Hermes Agent": "hermes.*main",
    "n8n": "n8n.*node",
    "Command Center Panel": "app.py.*command_center_panel",
    "Bot_Exchange Bridge": "bridge.py",
}

def check_service(name, pattern):
    """Check if a service process matching pattern is running."""
    try:
        # Use pgrep with -f to match full command line
        result = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return True, pids
        else:
            return False, []
    except Exception as e:
        return False, []

def main():
    log_lines = []
    all_ok = True
    timestamp = datetime.utcnow().isoformat() + "Z"

    log_lines.append(f"=== Service Health Check {timestamp} ===")

    for name, pattern in SERVICES.items():
        running, pids = check_service(name, pattern)
        if running:
            log_lines.append(f"✓ {name}: RUNNING (PIDs: {', '.join(pids)})")
        else:
            log_lines.append(f"✗ {name}: DOWN")
            all_ok = False

    # Also check if command center endpoint is responding
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8787/api/status", timeout=5) as resp:
            if resp.status == 200:
                log_lines.append("✓ Command Center API: RESPONDING")
            else:
                log_lines.append(f"✗ Command Center API: HTTP {resp.status}")
                all_ok = False
    except Exception as e:
        log_lines.append(f"✗ Command Center API: UNREACHABLE ({e})")
        all_ok = False

    log_lines.append("=== End Health Check ===")

    # Write to stdout (cron captures this)
    for line in log_lines:
        print(line)

    # Exit code: 0 if all OK, 1 if any failures
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()