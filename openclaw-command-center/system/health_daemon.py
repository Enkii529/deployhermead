#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import logging
from datetime import datetime, timezone

# === Configuration ===
HEALTH_STATUS_PATH = "/media/sf_ClawdbotShared/Brain/wiki/data/health_status.json"
LOG_PATH = os.path.expanduser("~/health_daemon.log")
CHECK_INTERVAL = 60  # seconds

# Define services: name -> {check_cmd, restart_cmd, max_restart_attempts, cooldown_seconds}
SERVICES = {
    "wiki": {
        "check_cmd": "curl -sf http://localhost:8765/ > /dev/null",
        # Start wiki server if not running
        "restart_cmd": "sh -c 'if ! pgrep -f \"http.server 8765\" > /dev/null; then nohup /usr/bin/python3 -m http.server 8765 --directory /media/sf_ClawdbotShared/Brain/wiki >> /home/openclaw/wiki_server.log 2>&1 & fi'",
        "max_attempts": 3,
        "cooldown": 300
    },
    "n8n": {
        "check_cmd": "curl -sf http://localhost:5678/healthz > /dev/null",
        # Assume container named 'n8n'
        "restart_cmd": "docker start n8n",
        "max_attempts": 3,
        "cooldown": 300
    },
    "brain_mount": {
        "check_cmd": "test -w /media/sf_ClawdbotShared/Brain",
        "restart_cmd": None,  # cannot auto-mount safely
        "max_attempts": 1,
        "cooldown": 0
    }
}

# === Logging Setup ===
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# === State Tracking ===
# Keep in-memory track of restart attempts and last try time per service
restart_info = {name: {"attempts": 0, "last_try": 0} for name in SERVICES}

def run_cmd(cmd):
    """Run a shell command, return True if exit code 0."""
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Command failed: {cmd} – {e}")
        return False

def load_status():
    if os.path.exists(HEALTH_STATUS_PATH):
        try:
            with open(HEALTH_STATUS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_update": None, "services": {}}

def save_status(status):
    try:
        with open(HEALTH_STATUS_PATH, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to write status: {e}")

def check_and_heal():
    status = load_status()
    now = time.time()
    new_service_status = {}

    for name, cfg in SERVICES.items():
        # Perform health check
        up = run_cmd(cfg["check_cmd"])
        state = status.get("services", {}).get(name, {"status": "unknown", "message": "", "last_check": None})
        state["last_check"] = datetime.now(timezone.utc).isoformat()

        if up:
            state["status"] = "up"
            state["message"] = ""
            # Reset restart attempts on recovery
            restart_info[name]["attempts"] = 0
            logging.info(f"{name} is up")
        else:
            # Service down
            state["status"] = "down"
            state["message"] = "Check failed"
            logging.warning(f"{name} is down")

            # Determine if we should attempt restart
            info = restart_info[name]
            if info["attempts"] < cfg["max_attempts"] and (now - info["last_try"] > cfg["cooldown"]):
                if cfg["restart_cmd"]:
                    logging.info(f"Attempting restart of {name}")
                    run_cmd(cfg["restart_cmd"])
                    info["last_try"] = now
                    info["attempts"] += 1
                    # After restart, re-check after a short delay
                    time.sleep(5)
                    if run_cmd(cfg["check_cmd"]):
                        state["status"] = "up"
                        state["message"] = "Recovered by restart"
                        logging.info(f"{name} recovered")
                    else:
                        state["message"] = "Restart attempt failed"
                        logging.error(f"{name} restart failed")
                else:
                    state["message"] = "No auto‑restart configured"
            else:
                state["message"] = "Max restart attempts exceeded"
                if info["attempts"] >= cfg["max_attempts"]:
                    state["status"] = "critical"
        new_service_status[name] = state

    status["services"] = new_service_status
    status["last_update"] = datetime.now(timezone.utc).isoformat()
    save_status(status)

def main():
    logging.info("Health daemon started")
    while True:
        try:
            check_and_heal()
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Health daemon stopped")
        sys.exit(0)
