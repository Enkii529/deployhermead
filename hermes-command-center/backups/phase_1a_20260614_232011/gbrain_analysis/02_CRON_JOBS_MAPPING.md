# 02_CRON_JOBS_MAPPING.md

All gbrain cron jobs and schedules mapped to our system.

---

## Reference Cron Schedule (from `docs/guides/cron-schedule.md`)

| Frequency | Job | Brain Interaction | Recipe | Our Status |
|-----------|-----|-------------------|--------|-----------|
| Every 30 min | Email monitoring | Search sender, update people pages | email-to-brain | ❌ |
| Every 30 min | X/Twitter collection | Create/update media pages, entity extraction | x-to-brain | ❌ |
| 3x/day weekdays | Meeting sync | Full ingestion + attendee propagation | meeting-sync | ❌ |
| Weekly | Calendar sync | Daily files + attendee enrichment | calendar-to-brain | ❌ |
| Daily AM | Morning briefing | Search calendar attendees, deal status, active threads | briefing skill | ✅ (needs brain integration) |
| Weekly | Brain maintenance | `gbrain doctor`, embed stale, orphan detection | maintain skill | ❌ |
| Nightly | Dream cycle | Entity sweep, enrich thin spots, fix citations | maintain + enrich + citation-fixer | ❌ |

---

## Implementation: Cron Setup Pattern

```bash
# Email collector — every 30 minutes
*/30 * * * * cd /path/to/email-collector && node email-collector.mjs collect && node email-collector.mjs digest

# X/Twitter collector — every 30 minutes
*/30 * * * * cd /path/to/x-collector && node x-collector.mjs collect >> /tmp/x-collector.log 2>&1

# Meeting sync — 10 AM, 4 PM, 9 PM on weekdays
0 10,16,21 * * 1-5 cd /path/to/meeting-sync && node meeting-sync.mjs >> /tmp/meeting-sync.log 2>&1

# Calendar sync — Sundays at 10 AM
0 10 * * 0 cd /path/to/calendar-sync && node calendar-sync.mjs --start $(date -v-7d +%Y-%m-%d) --end $(date +%Y-%m-%d)

# Brain health — weekly Mondays at 6 AM
0 6 * * 1 gbrain doctor --json >> /tmp/gbrain-health.log 2>&1 && gbrain embed --stale

# Dream cycle — nightly at 2 AM
0 2 * * * /path/to/dream-cycle.sh
```

### Our Adaptation

We'll use Hermes `cronjob` tool instead of system crontab. Benefits: Hermes manages execution, tool access, and delivery.

Example:
```json
{
  "schedule": "*/30 * * * *",
  "prompt": "Run email-to-brain integration: fetch new emails, extract entities, enrich people/company pages, save raw emails, create timeline entries.",
  "skills": ["email-to-brain", "enrich", "brain-ops"],
  "deliver": "local"
}
```

---

## Mandatory: Quiet Hours Gate

**Every cron job that sends notifications MUST check quiet hours first.**

Pattern:
```bash
# In every cron script:
if ! bash scripts/quiet-hours-gate.sh; then
  mkdir -p /tmp/cron-held
  echo "$OUTPUT" > /tmp/cron-held/$(basename "$0" .sh).md
  exit 0
fi
# Not quiet hours — send normally
```

Our implementation: In Hermes cron jobs, check quiet hours before delivering to Telegram. If quiet, save to `~/hermes/cron/output/held/` and include in next morning briefing.

---

## Execution Pattern: Cron via Minions

**Rule:** Scheduled work runs as Minion jobs, not `agentTurn`.

Why:
- Durability: Gateway restart won't lose state
- Observability: `gbrain jobs list` shows every run
- Steering: Can send inbox messages to running job
- Concurrency safety: Idempotency keys prevent stacking

### Postgres Mode (fire-and-forget):
```json
{
  "schedule": "*/30 * * * *",
  "kind": "shell",
  "cmd": "gbrain jobs submit ea-inbox-sweep --params '{\"slot\":\"$(date -u +%Y-%m-%dT%H:%M)\"}' --idempotency-key ea-inbox-sweep:$(date -u +%Y-%m-%dT%H:%M)"
}
```

### PGLite Mode (inline):
```json
{
  "schedule": "*/30 * * * *",
  "kind": "shell",
  "cmd": "gbrain jobs submit ea-inbox-sweep --params '{}' --follow"
}
```

Our adaptation: For Hermes, we don't have Minions. Use Hermes `delegate_task` for durable background work with `notify_on_complete=true`. Or use n8n workflows as the job queue.

---

## Travel-Aware Timezone Handling

Agent reads calendar for flights/hotels to infer current location/timezone. Cron jobs that would fire during sleeping hours at destination get held and folded into morning briefing.

Our implementation: In cron jobs, check `system_state/current_timezone.md` (updatable via manual command or calendar inference). Adjust quiet hours accordingly.

---

## Job: Dream Cycle (The Most Important)

### What It Does (Pseudo-code)
```python
def dream_cycle():
    # Phase 1: Entity Sweep
    conversations = get_todays_conversations()
    for message in conversations:
        entities = detect_entities(message)
        for entity in entities:
            page = brain_search(entity.name)
            if not page:
                create_page(entity)        # new entity, create + enrich
            elif page.is_thin():
                enrich_page(entity)        # thin page, fill it out
            else:
                update_timeline(entity)    # existing page, add today's mentions

    # Phase 2: Fix Broken Citations
    pages = list_pages(type='person', limit=100)
    for page in pages:
        for entry in page.timeline:
            if not entry.has_source_attribution():
                fix_citation(entry)
            if entry.has_tweet_url() and not entry.url_is_valid():
                fix_url(entry)

    # Phase 3: Consolidate Memory
    patterns = detect_patterns_across_conversations()
    for pattern in patterns:
        promote_to_memory(pattern)     # ephemeral → durable knowledge

    # Phase 4: Sync
    brain_sync()
    brain_embed_stale()
```

### Setup for Hermes
Create cron job at 2 AM:
```json
{
  "schedule": "0 2 * * *",
  "prompt": "Run dream cycle: 1) Scan today's conversations (Bot_Exchange/queue/, system_registry/OPENCLAW_WORKLOG.md, inter_agent_tasks/) for entities I mentioned. 2) For each person/company/idea: check if brain page exists; create or update if thin. 3) Audit citations on recent timeline entries, fix missing [Source: ...]. 4) Run concept-synthesis on new concept stubs. 5) Detect patterns across reflections (originals/, voice-notes/). 6) Embed any stale pages (if we have vector DB). 7) Report results to brain-dream-cycle-summaries/YYYY-MM-DD.md.",
  "skills": ["signal-detector", "enrich", "citation-fixer", "concept-synthesis", "maintain"],
  "deliver": "local"
}
```

---

## Job: Morning Briefing

Already exists, but enhance to include:
- Brain pulse (contradictions resolved overnight, top mentions, new facts)
- Held messages from quiet hours
- Pending consolidation count

See `skills/briefing/SKILL.md` for full spec.

Our implementation: In our existing briefing cron, add `gbrain recall` equivalent if we have recall capability, otherwise query recent timeline entries.

---

## Job: Brain Health / Maintenance

Weekly run of `maintain` skill. Our adaptation:

```json
{
  "schedule": "0 6 * * 1",
  "prompt": "Run brain health check: 1) List all person/company pages and check for stale compiled_truth (last timeline > compiled_truth date). 2) Find orphan pages (zero backlinks). 3) Check for dead links (links to non-existent pages). 4) Audit citations on last 50 updated pages. 5) Check filing violations (pages in sources/ that should be in people/ etc). 6) Calculate health score. 7) Fix what can be fixed automatically (backlinks, citation format, dead links). Save report to system_registry/brain-health-YYYY-MM-DD.md.",
  "skills": ["maintain"],
  "deliver": "local"
}
```

---

## Job: Email to Brain

Every 30 minutes:
```json
{
  "schedule": "*/30 * * * *",
  "prompt": "Fetch new emails from Gmail (use credentials from ~/openclaw-command-center/credentials.txt). For each email: extract sender → enrich person page; extract mentioned entities → enrich; save raw email to sources/.raw/; if meeting-related, create meeting page with attendees; if contains links, trigger idea-ingest. Send notifications only if high-priority sender.",
  "skills": ["email-collector", "enrich", "meeting-ingestion", "idea-ingest"],
  "deliver": "local"
}
```

---

## Job: X/Twitter to Brain

Every 30 minutes:
```json
{
  "schedule": "*/30 * * * *",
  "prompt": "Monitor X/Twitter for followed handles (list from brain pages people/ with twitter field). For each new tweet: create media page under media/x/; extract mentioned entities → enrich; add timeline entry to author page if in brain; detect deletions and mark. Save raw tweet JSON.",
  "skills": ["x-collector", "media-ingest", "enrich"],
  "deliver": "local"
}
```

---

## Job: Calendar Sync

Daily at 10 PM for tomorrow's calendar:
```json
{
  "schedule": "0 22 * * *",
  "prompt": "Fetch tomorrow's Google Calendar events. For each event: create meeting page in meetings/ (even without transcript); enrich all attendees; list companies discussed; add to daily briefing context. Save raw iCal data.",
  "skills": ["calendar-sync", "enrich"],
  "deliver": "local"
}
```

---

## Anti-Patterns to Avoid

- ❌ Scheduling all jobs at the same minute (:00) → causes collisions
- ❌ Inline 3000-word prompts in cron → use skill file references
- ❌ Running cron jobs without testing on 3-5 items first
- ❌ Jobs that produce different output on re-run (must be idempotent)
- ❌ Sending notifications during quiet hours → hold and fold into briefing
- ❌ Separate per-source sync entries when `sync --all --parallel` would replace them

---

## Idempotency Requirement

Every cron job MUST be idempotent:
- Running twice produces same result (no duplicate pages)
- Use checkpoint state files to track progress
- Check for existing output before creating new
- Use idempotency keys for recurring workloads

Our implementation: For each cron job, store last run timestamp in `system_state/cron_last_run.json` with `{job_name: ISO_timestamp}`. On start, check if already completed for that period.

---

## Multi-source Sync Pattern

When brain has 2+ active sources, use one consolidated cron line instead of N per-source entries:

```bash
*/5 * * * * gbrain sync --all --parallel 4 --workers 4 --skip-failed
```

Our equivalent: If we support multiple brain repos (current Brain + external repos), implement batch sync with concurrency control.

---

## Dream Cycle Phases in Detail

### Phase 1: Entity Sweep
- Get today's conversations from: Bot_Exchange/queue/ (processed), inter_agent_tasks/completed/, system_registry/OPENCLAW_WORKLOG.md (session logs), maybe Telegram messages export
- Run signal-detector on each message to extract entities
- For each entity: search brain; create if missing; enrich if thin; update timeline if existing

### Phase 2: Citation Hygiene
- Scan all pages updated in last 7 days
- Find timeline entries without `[Source: ...]` citations
- For tweets without x.com URLs, use X API to resolve and fix
- Create report of fixes applied

### Phase 3: Consolidate
- Run concept-synthesis on new concept stubs (from signal-detector)
- Identify patterns across recent originals/ and reflections
- Write pattern pages to patterns/<theme>
- Merge duplicate entities (fuzzy name matching + same-company cross-check)

### Phase 4: Embed Stale
- If we have vector DB: re-embed pages with stale embeddings (missing or old model)
- Could be heavy; run with nohup if > 1000 pages

### Phase 5: Backfill Graph
- `gbrain extract links` equivalent: scan all pages for `[[wiki/people/name]]` and `[Name](people/slug)` patterns, create typed links
- `gbrain extract timeline` equivalent: parse `- **YYYY-MM-DD** | entry` lines, add to structured timeline table

---

## State Persistence

Use `system_registry/` for cron state:
- `CRON_LAST_RUN.json` - last successful run per job
- `DREAM_CYCLE_STATE.json` - progress tracking for multi-phase jobs
- `BRAIN_HEALTH_SCORE.json` - historical health metrics

---

## Integration with n8n

We could alternatively implement cron jobs as n8n scheduled workflows, which gives:
- Visual editor
- Built-in error handling, retries
- Integration with our Telegram, email, etc.
- Execution logs in n8n UI

But Hermes cronjob tool is simpler for now. Keep n8n for complex multi-step workflows that involve external services.

---

## Next Files

- `03_ARCHITECTURE_GAPS.md` - What's missing technically
- `04_IMPLEMENTATION_PLAN.md` - Phased rollout
- `05_QUICK_WINS.md` - Easy early wins
- `06_SKILL_ADAPTATIONS.md` - Specific modifications for our system
- `07_INTEGRATION_POINTS.md` - Wiring into existing infra