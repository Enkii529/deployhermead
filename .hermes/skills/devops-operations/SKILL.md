---
name: devops-operations
description: Comprehensive guide for maintaining, troubleshooting, and operating Hermes/OpenClaw infrastructure. Covers system health checks, operational audits, n8n workflow automation, and service recovery procedures.
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
category: devops
tags: [devops, health-check, audit, automation, n8n, troubleshooting, monitoring, infrastructure]
---

# DevOps Operations

This umbrella skill centralizes all operational maintenance for the Hermes/OpenClaw ecosystem: health monitoring, service audits, workflow automation, and incident response. It replaces the previous separate skills: `n8n-automation`, `operational-audit`, and `system-health-audit`.

## When to Use

- Perform routine health checks or full operational reviews
- Troubleshoot service outages or degraded performance
- Build, debug, or extend n8n workflows
- Investigate recurring blockers or system patterns
- Recover services after failures
- Set up new automation or monitoring

## Prerequisites

- Running Hermes gateway and associated services
- Access to the host system (terminal, file read/write)
- n8n instance with API key (for automation work)
- Optional: MCP server configured for direct n8n access

## Quick Reference Map

- **System Health Check** → See [System Health Check](#system-health-check)
- **Operational Audit / Review** → See [Operational Audit](#operational-audit)
- **n8n Workflow Automation** → See [n8n Workflow Management](#n8n-workflow-management)

---

## System Health Check

Rapid verification of critical services with recovery guidance.

### What It Does

Checks that core infrastructure is up and provides recovery steps if issues are found.

### Services Verified

| Service | Expected Endpoint / Check | Primary Fix Location |
|---------|---------------------------|----------------------|
| n8n | `curl -s -o /dev/null -w "%{http_code}" http://localhost:5678` → `200` | See [n8n Recovery](#n8n-recovery) |
| Hermes Gateway | `ps aux | grep -E "hermes.*gateway" | grep -v grep` running Python process | `systemctl --user status hermes-gateway` |
| Brain API | `curl -s http://192.168.56.1:8090/health` → JSON response | Windows host Docker compose |
| Docker containers | `docker ps` shows expected containers | `docker start <name>` or `docker compose up -d` |
| Brain Command Center Panel | `curl -s http://127.0.0.1:8787` → UI response | `~/openclaw-command-center/.../app.py` |
| Enki Browser | `curl -s http://127.0.0.1:4318` (404 on `/` is fine) | Process restart |

### Common Pitfalls

- **Brain API location**: It runs on the Windows host, not the Ubuntu VM. The IP `192.168.56.1` is host-only adapter.
- **VirtualBox IP changes**: If `192.168.56.1` fails, try `192.168.1.151` or `100.67.101.95`.
- **Enki Browser returns 404 on `/`**: expected; health check uses `/api/` or similar.
- **command_center_panel**: Flask UI, not the Brain ingestion API.

### Recovery Procedures

#### n8n Recovery

```bash
# Health check
curl -sS http://localhost:5678/api/v1/healthz

# Restart container
docker restart n8n

# Check logs
docker logs n8n
```

#### Brain API Recovery (Windows Host)

```powershell
# SSH to Windows from VM first (ensure SSH key)
ssh user@192.168.56.1

# Then on Windows host:
cd R:\codex\brain-stack
docker compose up -d

# Verify firewall allows inbound TCP 8090 on host-only network
```

#### SSH Key Issues

The VM→Windows SSH uses `~/.ssh/enkii_windows_ed25519`. If missing or broken:

```bash
# Generate new key on VM
ssh-keygen -t ed25519 -f ~/.ssh/enkii_windows_ed25519 -N ""

# Install public key on Windows at C:\Users\Jason\.ssh\authorized_keys
# See references/ssh_key_setup.md for details
```

#### Port Conflicts

If a service fails to start due to port in use:

```bash
# Check what's using the port
ss -tulpn | grep :PORT

# Kill stray process or reconfigure service
kill <PID>
```

---

## Operational Audit

Comprehensive review of system activity over a defined time window (default 72 hours), producing a structured report with executive summary, blockers, recommendations, and patterns.

### Trigger

User asks for an operational review, system status, project update, or analysis of past activity.

### Process

1. **Define Scope** – Time range, systems to include (Hermes, n8n, Bot_Exchange, etc.), focus areas.
2. **Data Collection** – Use minimal, targeted reads:
   - `session_search(query="...", limit=20)` for relevant conversations
   - `terminal` for status commands (`hermes gateway status`, `docker ps`, `df -h`, `ps aux`)
   - `read_file` for logs (`~/.hermes/logs/gateway.log`), configs, task queues
3. **Categorize Findings**:
   - Completed Work
   - Partially Completed Work (with remaining steps/blockers)
   - Requested But Not Completed
   - Blockers (who/what, what's needed)
   - Recommendations (concrete, actionable)
   - Recurring Patterns (ownership gaps, tool failures, missing inputs)
4. **Prioritization** – Rank by urgency, impact, dependency risk.
5. **Output** – Clear tables and bullet points. If report >4000 words or >10 sections, split into multiple messages or provide executive summary with offer to send full details.

### Pitfalls

- **Stdout limit**: `execute_code` printing large files hits 50KB limit. Use `read_file` and extract snippets; accumulate data in variables, print concise summary.
- **Message length limit**: Responses truncated after ~10,000 chars. Break into parts: executive summary first, then sections in follow-up turns; compress redundant details.
- **Gateway polling conflicts**: Warnings like "Telegram polling conflict (1/3)" indicate multiple gateway instances or token reuse. Ensure only one systemd-managed gateway: `systemctl --user status hermes-gateway`. Kill stray processes.
- **Incomplete follow-through**: Data collection often stops before analysis. After gathering, immediately synthesize findings and propose fixes.

### Report Template

Use `templates/operational_audit_report.md` as a skeleton matching required sections.

### Scripts

- `scripts/gather_common_status.sh` – Collect concise system status (gateway, disk, processes) for inclusion in reports.

---

## n8n Workflow Management

Build, troubleshoot, and extend n8n workflows; covers MCP integration, direct database access, common node patterns (dedupe, scoring, summarization), and persistence strategies.

### Setup

1. **Verify n8n health**
   ```bash
   curl -sS http://localhost:5678/api/v1/healthz
   ```
   Expected: `{"status":"OK"}`. If not, check container logs (`docker logs n8n`).

2. **Obtain API key** from n8n UI: Settings → API → Create new key. Copy JWT.

3. **Configure Hermes**
   - For MCP: set `N8N_API_URL` and `N8N_API_KEY` in MCP server config.
   - For direct DB edits: SQLite DB usually at `~/.n8n/database.sqlite` (or mounted volume). Ensure Hermes has read/write.

4. **SSRF strict mode** may block MCP; disable if needed: `-e N8N_MCP_STRICT_MODE=false` in container env. Or use curl with JWT header directly.

### Core Patterns

#### Deduplication Node (Function)

Robust pattern that persists dedupe state across runs using `$getWorkflowStaticData` (with fallback) and supports content hashing:

```javascript
// references/dedupe-node-pattern.js
const store = (typeof $getWorkflowStaticData === 'function')
  ? $getWorkflowStaticData('global')
  : (typeof getWorkflowStaticData === 'function' ? getWorkflowStaticData('global') : {});
store.urls = store.urls || {};
store.titles = store.titles || {};
store.hashes = store.hashes || {};
const sevenDays = 7 * 24 * 60 * 60 * 1000;
const now = new Date().toISOString();
const newItems = [];

function isOlderThan7Days(ts) {
  if (!ts) return false;
  try { return (Date.now() - new Date(ts).getTime()) > sevenDays; } catch (e) { return true; }
}
function safeString(val) {
  if (val == null) return '';
  return String(val);
}
if (!Array.isArray(items)) {
  console.error('Dedupe: expected items array, got:', items);
  return items || [];
}
for (const item of items) {
  try {
    const data = item.json || {};
    const title = safeString(data.title);
    const url = safeString(data.url || data.link);
    if (!url && !title) continue;
    const normTitle = title.toLowerCase().replace(/[^a-z0-9\\s]/g, '').trim();
    if (!normTitle && !url) continue;

    if (url && store.urls[url] && !isOlderThan7Days(store.urls[url])) {
      item.duplicate = true; item.duplicate_reason = 'url'; continue;
    }
    if (normTitle && store.titles[normTitle] && !isOlderThan7Days(store.titles[normTitle])) {
      item.duplicate = true; item.duplicate_reason = 'title'; continue;
    }

    const content = safeString(data.raw_content || data.content || data.description || '');
    let hash = '';
    if (content.length > 0) {
      try {
        const crypto = require('crypto');
        hash = crypto.createHash('sha1').update(content.substring(0, 500)).digest('hex');
        if (store.hashes[hash] && !isOlderThan7Days(store.hashes[hash])) {
          item.duplicate = true; item.duplicate_reason = 'content'; continue;
        }
      } catch (e) { hash = ''; }
    }

    newItems.push(item);
    if (url) store.urls[url] = now;
    if (normTitle) store.titles[normTitle] = now;
    if (hash) store.hashes[hash] = now;
  } catch (err) {
    console.error('Dedupe item error:', err.message);
    newItems.push(item);
  }
}
function prune(obj) {
  for (const key in obj) {
    if (isOlderThan7Days(obj[key])) delete obj[key];
  }
}
prune(store.urls);
prune(store.titles);
prune(store.hashes);
console.log(`Dedupe: processed ${items.length} items, kept ${newItems.length}, store sizes: urls=${Object.keys(store.urls).length}, titles=${Object.keys(store.titles).length}, hashes=${Object.keys(store.hashes).length}`);
return newItems;
```

**Why it works**:
- Handles n8n version differences (`$getWorkflowStaticData` vs `getWorkflowStaticData`)
- Persists across restarts via n8n internal store
- Auto-prunes entries older than 7 days
- Logs summary counts for debugging

#### File Output Pattern

Write Markdown briefings using `Read/Write File` node. Ensure path starts with `/files/` and directory exists on host:

```
/files/briefings/{{$now.format('YYYY-MM-DD_HH')}}.md
```

Container must mount: `-v /host/path/automation_outputs:/files`.

#### Summarization with Local LLM

Use Function node to call `OLLAMA_BASE_URL` or another provider. See patterns in `linear` and `docker-management` skills for similar approaches.

### Troubleshooting

#### SSRF Protection Blocks Localhost

**Symptom**: MCP tools error with "SSRF protection: Localhost access is blocked in strict mode".

**Fix**:
- Restart n8n with env var `N8N_MCP_STRICT_MODE=false`:
  ```bash
  docker run -d --name n8n -p 5678:5678 \
    -e N8N_MCP_STRICT_MODE=false \
    -v /home/openclaw/openclaw-command-center/automation_outputs:/files \
    n8nio/n8n:2.18.5
  ```
- Or configure MCP server's `allowed_hosts` to include localhost.

#### Deduplicate Node Throws `$getWorkflowStaticData is not defined`

**Cause**: n8n version uses different variable name.

**Fix**: Use compatibility pattern shown above (checks both `$` and non-`$` variants).

#### Missing `/files` Directory or Permission Denied

```bash
mkdir -p /home/openclaw/openclaw-command-center/automation_outputs/{briefings,logs}
chmod -R 777 /home/openclaw/openclaw-command-center/automation_outputs  # temporary for testing
docker inspect n8n | grep -A 2 Mounts  # verify mount
```

#### Workflow Not Appearing After Container Restart

n8n stores workflows in internal DB. If you manually edited SQLite, ensure correct ownership (`node:node` UID/GID). Or import via UI: Workflows → Import → JSON.

#### Execution Stops at a Node with No Output

Ensure Function nodes end with `return newItems;`. Use `console.log` for debugging and check execution logs in UI.

### MCP Access

If SSRF blocks MCP, either disable strict mode (see above) or use direct curl with JWT in `Authorization: Bearer <token>` header.

---

## Reference Material

This section contains detailed session-specific notes and configuration details.

### n8n MCP Integration Notes

From the integration work:
- MCP server needs `N8N_API_URL` and `N8N_API_KEY` environment variables.
- If SSRF blocks localhost, set `mcp_servers.n8n.allowed_hosts` to include `localhost` or disable strict mode.
- Use host.docker.internal for Docker-on-Linux scenarios.

### n8n Database Direct Edit

SQLite location: `~/.n8n/database.sqlite` (default) or mounted volume. Ensure proper permissions for the user running n8n (usually UID 1000 or node:node).

### Known Service Ports

- n8n: 5678 (HTTP)
- Brain API: 8090 (HTTP, on Windows host)
- Brain Command Center Panel: 8787 (HTTP)
- Enki Browser: 4318 (HTTP)

### Operational Review Patterns

- Use `session_search` with date filters when possible to bound results.
- Collect status with `scripts/gather_common_status.sh` for quick snapshot.
- For large log files, read only recent lines with offset/limit; avoid printing entire file.
- Prioritize findings by urgency, impact, and dependency risk.

---

## Templates

- `templates/workflow-skeleton.json` – Minimal n8n workflow JSON with common nodes (trigger, action, output)
- `templates/operational_audit_report.md` – Structured report skeleton for operational reviews

## Scripts

- `scripts/verify-n8n-connection.sh` – Health check for n8n endpoint; prints OK or error
- `scripts/gather_common_status.sh` – Collects gateway, disk, and process status in concise format
- `scripts/test_vm_to_windows_ssh.sh` – Verifies SSH connectivity from VM to Windows host

---

## Revision History

- v1.0.0 (2026-05-18) – Initial umbrella consolidation of `n8n-automation`, `operational-audit`, and `system-health-audit`.