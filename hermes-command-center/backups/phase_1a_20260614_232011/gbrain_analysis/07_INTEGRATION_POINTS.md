# 07_INTEGRATION_POINTS.md

How the upgraded Brain integrates with our existing OpenClaw/Hermes infrastructure.

---

## Our Current Infrastructure (re-cap)

- **Brain location:** `/media/sf_ClawdbotShared/Brain` (NFS mount, shared with Windows)
- **Command Center Panel:** Flask app on 127.0.0.1:8787 (status, queue, chat)
- **Bot_Exchange:** File-based queue system (`queue/`, `workers/`, `status`)
- **Inter-agent tasks:** File protocol `inter_agent_tasks/` (queue, in_progress, completed) for @Hermes ↔ @hemesmsibot coordination
- **n8n:** Running on port 5678, for complex workflow automation
- **Hermes agent:** This instance (Linux), with skills in `~/.hermes/skills/`
- **Credentials:** `~/openclaw-command-center/credentials.txt`
- **System state:** `system_registry/` (CURRENT_SESSION.md, OPENCLAW_WORKLOG.md)
- **Wiki:** `wiki/` (static markdown, not served by default)

---

## Integration Categories

1. **Bot_Exchange** – queue of tasks/workflows
2. **Inter-Agent Tasks** – cross-platform coordination
3. **n8n** – visual workflow engine
4. **Command Center Panel** – dashboard/UI
5. **Hermes Skills System** – our extension mechanism
6. **Credentials** – secure storage
7. **Telegram** – delivery channel
8. **System State** – logs, session continuity

---

## 1. Bot_Exchange Integration

**Current purpose:** A file-based queue where tasks are dropped and workers process them.

**Brain upgrade opportunity:** Use Bot_Exchange as the source of "conversations" for the dream cycle's entity sweep.

**Integration:**
- Dream cycle skill reads processed tasks from `Bot_Exchange/queue/` and `Bot_Exchange/archive/` to extract entities the user discussed.
- Alternatively, we could have a dedicated `brain_ingest` worker that monitors Bot_Exchange queue and triggers ingestion skills in real-time:
  - When a task file is created in `queue/`, the worker reads it.
  - If task type is `meeting_transcript`, call `meeting-ingestion`.
  - If task type is `content_link`, call `idea-ingest`.
  - If task type is `voice_note`, call `voice-note-ingest`.
- This decouples ingestion from Hermes gateway and allows parallel processing via Bot_Exchange workers.

**Implementation:**
- Create `Bot_Exchange/workers/brain_ingest_worker.py` that:
  - Watches `queue/` for new JSON task files (polling or inotify)
  - Based on `task_type`, invokes appropriate Hermes skill via Hermes Python API or CLI
  - Marks task `in_progress` then `completed` with result
- Configure worker to run as systemd service or in `screen`/`tmux`.

**Benefit:** Offloads heavy ingestion from main Hermes gateway; preserves reliability of Bot_Exchange.

---

## 2. Inter-Agent Tasks Integration

**Current purpose:** File-based protocol between @Hermes (Linux) and @hemesmsibot (Windows). Each agent has its own worker that picks up tasks from the shared `inter_agent_tasks/queue/`.

**Brain upgrade opportunity:** Use this to offload heavy brain maintenance jobs to the Windows agent, which may have different resources (GPU, memory).

**Integration:**
- For expensive jobs (concept synthesis, embedding refresh, bulk enrichment), submit a task file with `type: brain_maintenance` and instruct which phase.
- The Windows agent runs its own brain instance (maybe shared same Brain repo) and processes the task.
- Results written back to `inter_agent_tasks/completed/` with output.

**Example task file:**
```json
{
  "task_id": "brain-dream-2026-06-14",
  "source": "@Hermes (Enzo)",
  "target": "@hemesmsibot",
  "type": "brain_maintenance",
  "instruction": "Run dream cycle phase 'synthesize' on conversations from 2026-06-13. Save report to dream-cycle-summaries/2026-06-13.md.",
  "created_at": "2026-06-14T02:00:00"
}
```
- The Windows agent's worker picks this up, runs the phase, writes report, marks completed.

**Benefit:** Distribute compute load; can run heavier models on Windows if available.

---

## 3. n8n Integration

**Current purpose:** Workflow automation (HTTP triggers, webhooks, scheduled jobs).

**Brain upgrade opportunity:** Use n8n for:
- **Scheduled ingestion workflows** that Hermes cron doesn't cover (e.g., scrape RSS feeds, collect tweets, pull YouTube subscriptions)
- **Webhook receivers** for external services: Circleback meeting webhook → trigger meeting-ingestion; Twitter account activity API → tweet ingest; Gmail push notifications → email ingest.
- **Complex multi-step enrichment** that involves multiple API calls and branching.

**Integration:**
- n8n workflows call Hermes via MCP tools or via HTTP API (expose Hermes skills as webhooks).
- Alternatively, n8n writes task files to `inter_agent_tasks/queue/` for Hermes to pick up.
- n8n also writes raw data to Brain's `sources/.raw/` and then triggers Hermes to process.

**Example n8n workflow:**
1. Schedule trigger: every 30 min
2. HTTP Request: fetch YouTube subscriptions RSS (new videos)
3. For each video URL: call Hermes MCP tool `idea-ingest` with URL
4. Log outcomes

**Implementation:**
- In n8n, set up "Hermes" as a custom node using HTTP Request node pointing to `http://127.0.0.1:8787/mcp` if we expose MCP over HTTP, or write to file.
- Create webhook endpoints in Hermes gateway to accept external triggers (need auth token).

**Benefit:** Leverages n8n's robust scheduling and webhook handling; Hermes focuses on brain logic.

---

## 4. Command Center Panel Integration

**Current purpose:** Flask dashboard for system status, queue visualization, chat.

**Brain upgrade:** Add Brain Health and Brain Query widgets.

**Integration points:**

### Add Brain Health metrics to status page
- Endpoint: `GET /brain-health` returns JSON from `maintain` skill (run on demand or cache).
- Display: health score, page counts, link density, last dream cycle result.
- Update Panel's `app.py` to call `brain_health_check()` (Python function) or read `system_registry/brain-health-latest.md`.

### Add Brain Search widget
- Simple search box that calls `brain_query` via HTTP and shows results with snippets.
- Useful for quick lookups from the browser.

### Add Recent Activity feed
- Show latest timeline entries from `system_registry/signal_log.jsonl` or `brain_data/timeline_recent.jsonl`.
- Could show: "Captured idea from chat: ...", "Enriched person: Jane Doe", "Fixed 12 citations".

### Show Cron Job Status
- Already shows queue; could add section for brain-related cron jobs (dream cycle, maintain, ingestion) with last run status.

**Implementation:**
- Modify `command_center_panel/templates/` to include new sections.
- Add routes in `command_center_panel/routes/brain.py`.
- These routes call our Python brain functions directly (same process) or via Hermes API.

**Benefit:** Centralized visibility into brain health and activity.

---

## 5. Hermes Skills System Integration

**Current:** Skills in `~/.hermes/skills/` are loaded by Hermes agent.

**Brain upgrade:** Add a new namespace `brain/` under skills.

**Directory structure:**
```
~/.hermes/
  skills/
    brain/
      brain-ops/          # convention (mostly docs)
      signal-detector/
      ingest/
      idea-ingest/
      meeting-ingestion/
      media-ingest/
      voice-note-ingest/
      enrich/
      briefing/
      daily-task-prep/
      maintain/
      citation-fixer/
      concept-synthesis/
      dream-cycle/
      ... etc
    devops/
      brain-first/
      brain-context/
    brain_tools/           # Python implementations of brain_* tools
      __init__.py
      search.py
      query.py
      get_page.py
      put_page.py
      ...
```

**Registration:**
- Skills are automatically discovered by Hermes if they have `SKILL.md` in subdirectory.
- Tools in `brain_tools/` need to be registered in Hermes MCP server. Add to `hermes/mcp_server.py`:

```python
from .skills.brain_tools import search as brain_search_tool
mcp_server.add_tool("brain_search", brain_search_tool)
```

**Skill loading order:** When a brain skill is triggered, it may rely on other skills (e.g., `ingest` calls `idea-ingest`). Hermes resolver should handle that by reading skill triggers. But also explicit dependencies can be declared in skill frontmatter `dependencies:`.

**Benefit:** Clean organization; easy to enable/disable whole categories.

---

## 6. Credentials Integration

**Current:** `~/openclaw-command-center/credentials.txt` holds email and n8n credentials.

**Brain upgrade needs:**
- Gmail API (OAuth2 or app password) – already present? Check file.
- Twitter/X API bearer token – add if not present.
- Optional: Crustdata/Crunchbase API keys for Tier 1 enrichment (add later).
- Supabase/S3 for raw file storage (if we go to cloud) – add later.

**Integration:**
- Create `hermes/credentials/brain.json` (or extend existing) with keys:
  ```json
  {
    "gmail": {"username": "...", "password": "..."},
    "twitter_bearer": "...",
    "openai_api_key": "...",
    "supabase_url": "...",
    "supabase_key": "..."
  }
  ```
- Load in brain tools using `hermes.config.load_credentials('brain')`.

**Security:** Ensure credentials file is 600 permissions. Already n8n uses it; we'll follow same pattern.

---

## 7. Telegram Integration

**Current:** Hermes sends messages to Telegram home channel or DMs.

**Brain upgrade:**
- Daily briefing already sent to Telegram.
- Dream cycle report also sent (maybe only if issues).
- Citation fixer notification if many failures.
- Signal detector runs silently (no user-visible output).

**Integration:**
- Use existing `send_message(platform='telegram', target='home', message=...)` in Python.
- For rich formatting, use markdown; Telegram supports code blocks, bold, links.
- Could send images (graphs) if we generate them.

**Example:** Morning briefing includes:
```
BRAIN PULSE (since last briefing)
✓ Contradictions resolved: 3
• Top entities: Jane Doe (people/jane-doe), Acme Corp (companies/acme), resilience framework (concepts/resilience)
...
```

**Benefit:** User stays informed without needing to check panel.

---

## 8. System State & Logging

**Current:** `system_registry/` holds CURRENT_SESSION.md and OPENCLAW_WORKLOG.md.

**Brain upgrade:** Expand with brain-specific state:

**New files in `system_registry/` or `openclaw_state/`:**
- `brain_health_history.jsonl` – daily health scores and dimension breakdowns
- `brain_executions.jsonl` – every cron job run for brain skills (timestamp, job_name, duration, tokens, cost, status)
- `signal_log.jsonl` – each signal-detector run summary: ideas captured, entities enriched
- `dream_cycle_state.json` – last run phases, timestamps, errors, counts
- `enrichment_queue.json` – entities pending enrichment (thin pages)
- `citation_fixer_state.json` – last scanned page, remaining gaps
- `brain_version` – schema version (for migrations)

**Integration with Hermes logging:**
- Hermes already writes to `OPENCLAW_WORKLOG.md`. Brain skills should log using Hermes logger (`logging.getLogger('hermes.brain')`) so messages go there too.
- For structured data, write JSONL files to `system_registry/` or `openclaw_state/` (shared across sessions).

**Benefit:** Troubleshooting and historical analysis.

---

## 9. Wiki Integration

**Current:** `wiki/` contains static markdown files (documentation, not necessarily brain content). No HTTP server by default.

**Brain upgrade:** Some brain-generated content belongs in wiki:
- Concept synthesis writes `concepts/README.md` (intellectual map) – this is brain content, not docs.
- Pattern pages under `patterns/` – also brain content.
- Dream cycle summaries under `dream-cycle-summaries/` – brain content.

**Question:** Should we keep brain content separate from wiki docs? gbrain writes to `wiki/` subdirectories: `wiki/originals/`, `wiki/personal/patterns/`, `wiki/people/` – they use wiki as the root for all brain content.

**Decision:** We can either:
- Option A: Use Brain root as the root for all content (like gbrain). `originals/`, `concepts/`, `people/` at top level. Wiki stays for documentation only.
- Option B: Follow gbrain and put content under `wiki/` as subdirectories: `wiki/originals/`, `wiki/concepts/`, `wiki/people/`, `wiki/patterns/`, etc.

**Pros/Cons:**
- A: Simpler path structure, brain content separate from docs. Already have many top-level dirs (Bot_Exchange, docs, etc.). Could add `originals/` etc at top. But might clutter top-level.
- B: Organizes all knowledge under `wiki/` as the "brain" root. Matches gbrain exactly. Clean separation: `docs/` for docs, `wiki/` for brain.

**Recommendation:** Option B. Move existing `wiki/` to be the brain content root. Keep `docs/` for pure documentation. This aligns with gbrain and gives clear boundary.

**Migration:**
- Create `wiki/originals/`, `wiki/concepts/`, `wiki/people/` (if not exist)
- Move any existing relevant content from Brain root into `wiki/` subdirs? Maybe not necessary; new content follows new structure.
- Adjust all tool paths to use `/media/sf_ClawdbotShared/Brain/wiki/...` for brain pages.

Update `Operation_Instructions.md` to reflect new structure.

---

## 10. Shared Brain Synchronization

**Current:** Shared via NFS at `/media/sf_ClawdbotShared/Brain` for both Linux and Windows.

**Brain upgrade implications:**
- Vector DB (PGLite or Chroma) stores index files. Must be accessible to both agents if both will search.
  - PGLite uses SQLite file; if both agents access same file, need file locking. Not safe for concurrent writers.
  - ChromaDB uses SQLite for metadata and separate files for vectors; concurrent reads safe, writes need care.
  - Recommendation: Only one agent (Linux/@Hermes) writes to brain at a time. Windows agent reads via NFS or uses read-only replica. Alternatively, use a server-based Postgres DB accessible to both.
- Dream cycle should run on one agent only (Linux) to avoid conflicts.
- Inter-agent tasks can still be used to offload specific phases that are read-only or can be synchronized.

**Strategy:**
- Keep write authority with @Hermes (Linux). It runs all cron jobs, updates brain.
- @hemesmsibot reads brain via NFS for querying but does not write (except maybe via explicit task to @Hermes).
- If we need Postgres, run it on Linux and expose to Windows via network (not NFS for DB).

**Implementation:** Document in inter-agent protocol: brain writes are single-writer.

---

## 11. Operation_Instructions.md Updates

This file is our constitution. Must be updated to include new brain conventions.

**New sections to add:**

### Brain-First Lookup
> Before any external API call, check brain first. See `skills/devops/brain-first.md`.

### Signal Detection
> Every user message is scanned for original thinking and entity mentions. The brain compounds automatically. See `skills/brain/signal-detector/SKILL.md`.

### Filing Rules
> All brain content must be filed by primary subject using directories under `wiki/`. See `wiki/_brain-filing-rules.md`.

### Citation Standard
> Every fact in brain pages requires inline `[Source: ...]` citation. Format: `[Source: provider, YYYY-MM-DD]` or `[Source: User, context, YYYY-MM-DD]`. See `skills/conventions/quality.md`.

### Back-Linking Iron Law
> Every mention of a person or company that has a brain page MUST create a back-link from that entity's page. The graph must be bidirectional.

### Raw Source Preservation
> All ingested items must have raw source stored in `.raw/` sidecar or cloud storage. Do not lose provenance.

### Dream Cycle
> Nightly at 2 AM, the dream cycle runs: entity sweep, citation fix, consolidation, embed, backfill. Do not interfere. Report in `system_registry/dream-cycle-YYYY-MM-DD.md`.

### Brain Health
> Weekly maintain job runs. Health score target >85. See `system_registry/brain-health-*.md`.

### Directory Structure (post-migration)
```
Brain/
├── Bot_Exchange/        (unchanged)
├── docs/                (documentation)
├── wiki/                (brain content root)
│   ├── originals/       (user's ideas)
│   ├── concepts/        (mental models)
│   ├── people/          (person pages)
│   ├── companies/       (company pages)
│   ├── meetings/        (meeting pages)
│   ├── media/           (videos, podcasts, articles)
│   ├── ideas/           (product/business ideas)
│   ├── personal/        (reflections)
│   ├── patterns/        (detected recurring themes)
│   ├── sources/.raw/    (raw source files)
│   └── ...
├── system_registry/     (state)
├── inter_agent_tasks/   (unchanged)
└── command_center_panel/ (unchanged)
```

---

## 12. Testing & Validation

After implementing each integration, test end-to-end:

1. **Signal flow:** Send a Telegram message with an idea and a person mention → verify `originals/` page created, `people/` page created or updated, back-link added.
2. **Search flow:** Call `brain_query("topic")` → get relevant pages with scores.
3. **Cron flow:** Wait for dream cycle cron → check `dream-cycle-summaries/latest.md` exists and contains meaningful stats.
4. **Panel flow:** Open `/status` page → Brain Health widget shows >0 pages, health score.
5. **Inter-agent flow:** Submit a task to enrich a specific person via file protocol → Windows agent picks it up, enriches, completes.
6. **n8n flow:** Trigger n8n webhook that causes an article to be ingested → verify brain page created.

---

## Implementation Checklist (Overall)

- [ ] Choose vector DB (PGLite vs Chroma) and set up
- [ ] Implement core tools: `brain_search`, `brain_query`, `brain_get_page`, `brain_put_page`, `brain_add_timeline_entry`, `brain_upload_raw`
- [ ] Create `brain_extract_links` and `brain_extract_timeline`
- [ ] Copy skill files from gbrain (adapt paths/tool names)
- [ ] Register tools in Hermes MCP server
- [ ] Add `signal-detector` gateway hook (always-on)
- ]] Create directories: `wiki/originals/`, `wiki/concepts/`, `wiki/ideas/`, `wiki/patterns/`, etc.
- [ ] Update Operation_Instructions.md with new conventions
- [ ] Migrate Wiki structure (if Option B)
- [ ] Implement `maintain` skill with all dimensions
- [ ] Implement `dream-cycle` orchestrator
- [ ] Set up cronjobs in Hermes: daily briefing, weekly maintain, nightly dream
- [ ] Build n8n workflows for email, Twitter, YouTube (optional)
- [ ] Enhance Command Center Panel with brain health and search
- [ ] Add structured logging to `system_registry/`
- [ ] Test end-to-end flows
- [ ] Document in `docs/BRAIN_CLI.md`

---

## Conclusion

The upgraded Brain will seamlessly integrate with our existing infrastructure by:
- Using Bot_Exchange for task queuing
- Using inter_agent_tasks for cross-platform work distribution
- Using n8n for external webhooks and complex pipelines
- Using Command Center Panel for visibility
- Using Hermes skills as the execution engine
- Using credentials.txt for API keys
- Using Telegram for user notifications

All while maintaining the shared NFS brain at `/media/sf_ClawdbotShared/Brain` (or its `wiki/` subfolder).

Next step: Start implementing the quick wins from `05_QUICK_WINS.md` to get basic functionality in place, then follow the phased implementation in `04_IMPLEMENTATION_PLAN.md`.