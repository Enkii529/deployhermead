import os
import glob
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

# NOTE: This panel may run on Windows (Docker mapping C:\\clawdbotshared -> /clawdbotshared)
# or on the Ubuntu VM where the shared drive is mounted at /media/sf_ClawdbotShared.
APP_ROOT = os.environ.get("APP_ROOT", "/media/sf_ClawdbotShared")
EXTRACTED = os.path.join(APP_ROOT, "extracted-assets")
CHATGPT_DIR = os.path.join(EXTRACTED, "chatgpt")
LYRICS_DIR = os.path.join(EXTRACTED, "lyrics")
LOG_DIR = os.path.join(EXTRACTED, "logs")
MANIFEST = os.path.join(EXTRACTED, "librarian_manifest.csv")

BOT_EXCHANGE = os.path.join(APP_ROOT, "Bot_Exchange")
INBOX = os.path.join(BOT_EXCHANGE, "queue", "inbox")
WORKING = os.path.join(BOT_EXCHANGE, "queue", "working")
DONE = os.path.join(BOT_EXCHANGE, "queue", "done")
FAILED = os.path.join(BOT_EXCHANGE, "queue", "failed")

CHAT_DIR = os.path.join(BOT_EXCHANGE, "events", "chat")
CHAT_FEED = os.path.join(CHAT_DIR, "feed.jsonl")

app = Flask(__name__, static_folder="static")


def mtime(path: str):
    try:
        ts = os.path.getmtime(path)
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    except Exception:
        return None


def count_files(path: str):
    try:
        return len([p for p in glob.glob(os.path.join(path, "*")) if os.path.isfile(p)])
    except Exception:
        return 0


def latest_log():
    try:
        logs = sorted(glob.glob(os.path.join(LOG_DIR, "librarian_*.log")), key=os.path.getmtime, reverse=True)
        return logs[0] if logs else None
    except Exception:
        return None


def tail(path: str, n: int = 60):
    """Return last N lines from a log.

    Some logs are UTF-16 (common when produced by PowerShell/Tee-Object),
    which looks like garbage if read as UTF-8. Detect NUL bytes and decode.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()

        # Heuristic: lots of NULs => UTF-16LE text.
        if data.count(b"\x00") > max(20, len(data) // 50):
            text = data.decode("utf-16-le", errors="replace")
        else:
            text = data.decode("utf-8", errors="replace")

        lines = text.splitlines(True)
        return "".join(lines[-n:])
    except Exception:
        return ""


def ensure_chat_feed():
    os.makedirs(CHAT_DIR, exist_ok=True)
    if not os.path.exists(CHAT_FEED):
        with open(CHAT_FEED, "w", encoding="utf-8") as f:
            f.write("")


def read_chat_tail(n: int = 60):
    ensure_chat_feed()
    try:
        with open(CHAT_FEED, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        lines = lines[-n:]
        msgs = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                msgs.append(json.loads(line))
            except Exception:
                continue
        return msgs
    except Exception:
        return []


def append_chat(msg: dict):
    ensure_chat_feed()
    with open(CHAT_FEED, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


@app.get("/api/status")
def api_status():
    ll = latest_log()
    return jsonify(
        {
            "librarian": {
                "manifest": {"path": MANIFEST, "mtime": mtime(MANIFEST)},
                "latest_log": {"path": ll, "mtime": mtime(ll) if ll else None, "tail": tail(ll, 40) if ll else ""},
                "counts": {
                    "chatgpt_files": count_files(CHATGPT_DIR),
                    "lyrics_files": count_files(LYRICS_DIR),
                },
            },
            "command_center": {
                "queues": {
                    "inbox": count_files(INBOX),
                    "working": count_files(WORKING),
                    "done": count_files(DONE),
                    "failed": count_files(FAILED),
                }
            },
        }
    )


@app.get("/api/chat")
def api_chat_get():
    n = int(request.args.get("tail", "60"))
    n = max(1, min(500, n))
    return jsonify({"ok": True, "messages": read_chat_tail(n)})


@app.post("/api/chat")
def api_chat_post():
    payload = request.get_json(force=True, silent=False)
    msg = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": "chat",
        "from": payload.get("from", "unknown"),
        "to": payload.get("to", "all"),
        "task_id": payload.get("task_id", ""),
        "text": payload.get("text", ""),
    }
    append_chat(msg)
    return jsonify({"ok": True})


@app.post("/api/task")
def api_task():
    import json as _json
    from uuid import uuid4

    payload = request.get_json(force=True, silent=False)
    task_id = payload.get("task_id") or f"ui-{uuid4()}"
    payload["task_id"] = task_id
    os.makedirs(INBOX, exist_ok=True)
    out = os.path.join(INBOX, f"{task_id}.json")
    with open(out, "w", encoding="utf-8") as f:
        _json.dump(payload, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "path": out})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    # LOCAL ONLY
    app.run(host="127.0.0.1", port=port)
