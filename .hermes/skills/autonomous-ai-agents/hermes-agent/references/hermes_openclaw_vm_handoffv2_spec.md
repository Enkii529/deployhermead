# Hermes/OpenClaw Ubuntu VM Brain Handoff v2

This file is for Hermes/OpenClaw running inside the Ubuntu VirtualBox VM.

The Brain Support Stack runs separately on the Windows host. Do not modify the OpenClaw Ubuntu VM setup to run these containers. The VM should only call the Brain API over HTTP.

## Brain API Endpoint

Preferred VirtualBox host-only endpoint:

```text
http://192.168.56.1:8090
```

Fallback endpoints if networking differs:

```text
http://192.168.1.151:8090
http://100.67.101.95:8090
```

Health check:

```bash
curl http://192.168.56.1:8090/health
```

Expected healthy shape:

```json
{
  "api": "ok",
  "memory_root": "/data/memory",
  "memory_writable": true,
  "required_folders_present": true,
  "ollama_reachable": true,
  "selected_model": "qwen2.5-coder:7b",
  "selected_model_available": true
}
```

## Environment Variables For Hermes/OpenClaw

Add these to the Ubuntu VM service environment:

```bash
OPENCLAW_BRAIN_API_BASE_URL=http://192.168.56.1:8090
OPENCLAW_BRAIN_INGEST_TEXT_URL=http://192.168.56.1:8090/ingest/text
OPENCLAW_BRAIN_HEALTH_URL=http://192.168.56.1:8090/health
OPENCLAW_BRAIN_SHARED_MEMORY_PATH=/path/to/the/Brain/shared/folder
```

Set `OPENCLAW_BRAIN_SHARED_MEMORY_PATH` to the actual Ubuntu mount path for the VirtualBox shared folder that maps to Windows `R:\ClawdbotShared\Brain`. Common VirtualBox shared folder paths look like `/media/sf_Brain`, but use the path that exists in this VM.

If OpenClaw already has a config file, use the same values there.

## Ingest Text

POST JSON to:

```text
POST http://192.168.56.1:8090/ingest/text
```

Request body:

```json
{
  "text": "required text to store in the Infinite Brain memory vault",
  "title": "optional title",
  "tags": ["optional", "tags"],
  "source": "optional source identifier or URL",
  "created_by": "Jason"
}
```

Example:

```bash
curl -s -X POST http://192.168.56.1:8090/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "OpenClaw should save important decisions into the Brain markdown memory vault.",
    "title": "OpenClaw Brain Decision Capture",
    "tags": ["openclaw", "brain", "memory"],
    "source": "ubuntu-vm-openclaw",
    "created_by": "ai"
  }'
```

Response shape:

```json
{
  "path": "/data/memory/concepts/example.md",
  "note_id": "2026-05-08-example",
  "title": "Example",
  "type": "concepts",
  "status": "active",
  "confidence": "high",
  "ollama_used": true,
  "review_required": false
}
```

## Integration Rules

- Treat markdown files as the source of truth.
- The VM may read/search the shared folder directly when it needs local markdown context.
- Use the Brain API for generated writes and ingestion so it can enforce frontmatter, folders, and low-confidence routing.
- Direct shared-folder writes are only for human-reviewed maintenance or emergency repair, not normal AI note creation.
- Low-confidence, invalid, or failed AI classification is routed to `/data/memory/inbox/`.
- Do not invent edges. Send raw content and let the Brain API decide.
- Obsidian is only the Windows human-facing editor for `R:\ClawdbotShared\Brain`.

## Minimal Python Client

```python
import requests

BRAIN_API = "http://192.168.56.1:8090"
BRAIN_SHARED_MEMORY_PATH = "/path/to/the/Brain/shared/folder"


def brain_health() -> dict:
    response = requests.get(f"{BRAIN_API}/health", timeout=10)
    response.raise_for_status()
    return response.json()


def ingest_text(text: str, title: str | None = None, tags: list[str] | None = None, source: str | None = None) -> dict:
    response = requests.post(
        f"{BRAIN_API}/ingest/text",
        json={
            "text": text,
            "title": title,
            "tags": tags or [],
            "source": source or "ubuntu-vm-openclaw",
            "created_by": "ai",
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()
```

## If The VM Cannot Connect

1. Confirm Windows stack is running:

```powershell
cd R:\codex\brain-stack
docker compose ps
curl http://127.0.0.1:8090/health
```

2. From Ubuntu VM, try:

```bash
curl http://192.168.56.1:8090/health
curl http://192.168.1.151:8090/health
curl http://100.67.101.95:8090/health
```

3. If all fail, allow inbound Windows Firewall traffic for TCP port `8090` on the VirtualBox host-only/private network.
```
