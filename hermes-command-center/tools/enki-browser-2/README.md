# Enki Browser 2 – AI‑First Browser Service

## Overview
Enki Browser 2 is an upgraded AI‑first browser control service built on **Node.js + Express + Playwright**.
It provides a backend HTTP API for automated browser navigation, interaction, and artifact capture.

Designed for integration with backend agents/automation systems, it enables reliable browser automation with persistent profiles, run‑level auditing, and optional open‑mode for unknown domains.

## Installation

```bash
cd /home/openclaw/openclaw-command-center/tools/enki-browser-2
npm install
```

### Playwright Browsers
```bash
npx playwright install chromium
```

## Configuration

| Env var       | Default                                    | Description                                    |
|---------------|--------------------------------------------|------------------------------------------------|
| `PORT`        | `4318`                                     | HTTP port                                      |
| `DATA_DIR`    | `./data`                                   | Data directory (profile, allowed domains, etc.)|
| `CONFIG_DIR`  | `./config`                                 | Config directory (known‑good domains)          |
| `RUNS_DIR`    | `./runs`                                   | Run artifacts folder                           |
| `PROFILE_DIR` | `./data/profile`                           | Chromium persistent profile                    |
| `ENKI_OPEN_MODE`| `true` (recommended)                      | When `true`, allow unknown domains             |

If `ENKI_OPEN_MODE=false`, unknown domains are gated by approval workflow (approval‑gate is available in both modes).

## Start the Service

```bash
cd /home/openclaw/openclaw-command-center/tools/enki-browser-2
ENKI_OPEN_MODE=true PORT=4318 node server.js
```

PID is written to `.server.pid` when started via this command.

## API Endpoints

| Method | Endpoint                | Description                                                  |
|--------|-------------------------|--------------------------------------------------------------|
| GET    | `/health`               | Service health + configuration info                           |
| GET    | `/policy`               | Current policy state (open mode, known good count, etc.)     |
| POST   | `/navigate`             | Navigate to URL (body: `{"url": "https://..."}`)            |
| POST   | `/open`                 | Alias for `/navigate`                                        |
| POST   | `/screenshot`           | Returns screenshot PNG of active page                        |
| POST   | `/screenshot/save`      | Save screenshot to run folder → `screenshot.png`             |
| GET    | `/visible-text`         | Extract visible text and save `visible-text.txt` in run      |
| GET    | `/dom-summary`          | Return DOM summary and save `dom-summary.json` in run        |
| GET    | `/console`              | Return captured console messages (saved to `console.json`)   |
| GET    | `/network-failures`     | Return failed network requests (saved to `network-failures.json`) |
| POST   | `/click`                | Click element by selector (body: `{"selector": "a"}`)       |
| POST   | `/fill`                 | Fill input field (body: `{"selector": "input", "value": "text"}`) |
| POST   | `/press`                | Press a key (body: `{"key": "Enter"}`)                      |
| POST   | `/run`                  | Execute a structured browser task and save run artifacts     |
| GET    | `/runs`                 | List available run folders                                   |
| GET    | `/runs/:id`             | Inspect run and list artifact files                          |

## Run & Artifacts

Each browser task creates a **timestamped run folder** under `runs/` (format `YYYY-MM-DDTHH-mm-ss-SSSZ`).
Typical run artifacts:

- `metadata.json`    — run metadata (runId, timestamps, URL, profile, openMode)
- `screenshot.png`   — screenshot when requested
- `visible-text.txt` — visible page text when requested
- `dom-summary.json` — DOM summary when requested
- `console.json`     — captured console messages
- `network-failures.json` — captured failed network requests
- `run.json`         — run description + action results

## Policy / Approval Gate

When `ENKI_OPEN_MODE=false`:
- Unknown domains are blocked (403) until approved.
- Approvals can be performed via the `/approvals/allow` endpoint (implemented in the approval layer; the service maintains allowed/pending lists under `data/`).

When `ENKI_OPEN_MODE=true`:
- Unknown domains are allowed and logged in run metadata.
- No navigation blocking occurs — but logs and policy stats remain available.

## Examples

### Health check
```bash
curl http://localhost:4318/health
```

### Navigate & capture
```bash
curl -X POST http://localhost:4318/navigate -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
curl http://localhost:4318/visible-text
curl http://localhost:4318/dom-summary
curl http://localhost:4318/screenshot --output screenshot.png
```

### Execute structured run
```bash
curl -X POST http://localhost:4318/run -H 'Content-Type: application/json' -d '{
  "url": "https://example.com",
  "actions": [
    { "type": "screenshot" },
    { "type": "visibleText" },
    { "type": "domSummary" }
  ]
}'
```


## CLI Wrapper

A convenience shell script `enki` is provided for quick CLI access to the API.

```bash
# Health check
./enki health

# Navigate to example.com
./enki open https://example.com

# Click a link (selector)
./enki click "a"

# Fill an input (selector + value)
./enki fill "input[name=q]" "test value"

# Press a key
./enki press "Enter"

# Get visible text
./enki text

# Get DOM summary
./enki dom

# Get console messages
./enki console

# Get network failures
./enki network

# Get page content (HTML)
./enki content

# Capture screenshot
./enki screenshot

# Inspect a specific run (provide runId)
./enki inspect-run 2026-05-04T02-42-16.472Z

# List run folders
./enki runs

# Run structured task (navigate + screenshot + text + dom)
./enki run https://example.com
```

The wrapper defaults to `http://127.0.0.1:4318`; you can override the base URL with `ENKI_BROWSER_URL`:
```bash
ENKI_BROWSER_URL=http://yourhost:4318 ./enki health
```

## Smoke Test

Run the smoke test sequence against `https://example.com` with `ENKI_OPEN_MODE=true`:

1. `GET /health`
2. `POST /navigate` → https://example.com
3. `GET /visible-text`
4. `GET /dom-summary`
5. `GET /console`
6. `GET /network-failures`
7. `POST /screenshot/save`

A timestamped run folder with all expected files should be created in `runs/`.

## Architecture Summary

- **Node.js (CommonJS)** — runtime  
- **Express** — HTTP API server  
- **Playwright** — Chromium automation (persistent profile)  
- **Chromium persistent context** — uses `data/profile`  
- **Runs folder** — `runs/` stores per‑task artifacts  
- **Open mode** – `ENKI_OPEN_MODE=true` allows unknown domains (logs them instead of blocking)  
- **Approval‑gate mode** – `ENKI_OPEN_MODE=false` retains old safety gate logic for unknown domains  

## Known Limitations

- Click/fill/press use selector‑only support (no text/role‑based fallback currently).  
- Run folder is created lazily — some artifacts may not appear until after a triggering endpoint is called.  
- Console and network logs accumulate in memory per active session and are written to disk when requested or at run completion.  
- The service does not perform automatic browser updates or install browsers on start.  

## Maintenance

- Stop the service gracefully by killing the PID file’s process (`kill $(cat .server.pid)`).  
- To clean runs, remove stale folders under `runs/`.  
- To reset the browser profile, remove or rename `data/profile`.  

## Security Notes

- No remote shell/exec endpoints are exposed.  
- Run logs may contain request/response metadata — redact secrets if sharing logs.  
- The service is intended for controlled automation use within trusted environments.  
