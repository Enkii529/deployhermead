# Brain API Setup

- Preferred endpoint: `http://192.168.56.1:8090`
- Fallback endpoints: `http://192.168.1.151:8090`, `http://100.67.101.95:8090`
- Health check: `curl http://192.168.56.1:8090/health`
- Expected JSON response:
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
- Ingest endpoint: `POST http://192.168.56.1:8090/ingest/text`
- Request body (JSON):
```json
{
  "text": "...",
  "title": "...",
  "tags": [...],
  "source": "...",
  "created_by": "..."
}
```
- Integration rules:
  - Markdown files are the source of truth.
  - The VM must use the Brain API for writes; do **not** write directly to the Windows memory folder.
  - Low-confidence or failed classifications go to `/data/memory/inbox/`.
  - Obsidian is only the Windows human editor for `R:\ClawdbotShared\Brain`.
