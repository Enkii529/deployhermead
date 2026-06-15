# 06_SKILL_ADAPTATIONS.md

Specific modifications needed to gbrain skills to work with our OpenClaw/Hermes system.

---

## Key Differences Between Gbrain and Our System

| Aspect | Gbrain | Our System | Adaptation Needed |
|--------|--------|------------|-------------------|
| **Language** | TypeScript/Bun (Node) | Python/Hermes | Port skills to Python or call gbrain CLI via subprocess |
| **DB Backend** | PGLite (SQLite+pgvector) or Postgres | Currently files only; can add Postgres later | Implement equivalent DB schema in Python (SQLite) or install PGLite binary |
| **Job Queue** | Minions (Postgres-backed) | Hermes subagents, n8n, or custom | Use Hermes `delegate_task` or n8n for durable jobs |
| **MCP** | Built-in MCP server | Hermes has MCP support | Implement MCP tools in Hermes matching gbrain tool names |
| **Storage** | gbrain files upload-raw with TUS | Local FS or cloud | Implement `brain_upload_raw` with local `.raw/` first |
| **Auth** | ClawVisor (credential gateway) | credentials.txt per-service | Use our existing credential system; no need for ClawVisor |
| **Skills format** | Markdown with frontmatter | Hermes skills also markdown | Can reuse format directly! |
| **Cron** | Host crontab + Minions | Hermes `cronjob` tool | Map gbrain cron recipes to Hermes cronjobs |

---

## Adaptation Strategy: Two Paths

### Path A: Install gbrain binary and use it as service
If we can get `bun install -g github:garrytan/gbrain` working on our Ubuntu VM:
- Run `gbrain init --pglite` to set up DB
- gbrain provides CLI and MCP server
- Our Hermes skills call gbrain CLI via subprocess OR connect to its MCP
- We still write our own skills that invoke gbrain commands
- **Pros:** Leverage gbrain codebase directly, get upgrades automatically
- **Cons:** Bun/TypeScript dependency may be fragile; less control

### Path B: Reimplement core in Python
If gbrain binary won't install (likely due to Bun requirement):
- Reimplement needed functionality in Python:
  - Vector store: ChromaDB (simpler than pgvector)
  - Graph extraction: Python regex + SQLite
  - Indexing: Whoosh or SQLite FTS5 for keyword
- Port skill logic to Python (read gbrain skill files as recipes)
- Keep same tool names (`brain_search`, `brain_query`, etc.)
- **Pros:** Fully integrated, no foreign runtime, easier to debug
- **Cons:** More work, miss upstream improvements

**Recommendation:** Attempt Path A first. If `bun install` fails after 2 hours, switch to Path B.

---

## Skill File Porting

### Reusing Markdown Skills Directly

Gbrain skills are plain markdown with YAML frontmatter. We can use them AS-IS if:
1. Our Hermes skill loader understands the same frontmatter format (it does)
2. The tools they reference exist in our toolset

So for each skill we want, we can copy the `.md` file into `~/hermes/skills/brain/` and then implement the referenced tools.

**Example:** `skills/idea-ingest/SKILL.md` references tools: `search`, `query`, `get_page`, `put_page`, `add_link`, `add_timeline_entry`, `file_upload`.

We implement these tools in Python and register them in Hermes. The skill file remains untouched (except maybe minor tweaks to tool names: gbrain uses `gbrain__search` prefix in OpenClaw; we use plain names).

---

## Tool Mapping: gbrain → Our Implementation

| gbrain Tool | gbrain Behavior | Our Implementation |
|-------------|-----------------|-------------------|
| `search` | Keyword search over all pages | `brain_search(query, type=None, limit=10)` → ripgrep + parse JSON |
| `query` | Hybrid search (kw+vector) | `brain_query(question, limit=10)` → embed query + vector search + RRF |
| `get_page` | Read page by slug, returns frontmatter+body | `brain_get_page(slug)` → read YAML+markdown |
| `put_page` | Create/update page, auto-link post-hook | `brain_put_page(slug, content, frontmutter=None)` → atomic write + call `brain_extract_links(slug)` |
| `add_timeline_entry` | Add dated event to page timeline | `brain_add_timeline_entry(slug, date, summary, source_citation=None)` → parse existing timeline, insert in reverse-chron order, rewrite file |
| `add_link` | Create explicit relationship link | `brain_add_link(source, target, type)` → append to `links.jsonl` or DB |
| `get_backlinks` | Who references this entity | `brain_get_backlinks(slug)` → query links index for target=slug |
| `get_links` | Outgoing links from page | `brain_get_links(slug)` → query links index for source=slug |
| `list_pages` | List pages with filters | `brain_list_pages(type=None, tag=None, limit=100)` → walk directory, parse frontmatter |
| `get_timeline` | Get timeline entries for entity | `brain_get_timeline(slug, limit=50)` → parse page timeline section OR query timeline index |
| `sync_brain` | Sync files → index (for DB-backed) | No-op for pure files; if using DB, run extractors |
| `file_upload` | Upload raw source file | `brain_upload_raw(file_path, page_slug, type)` → store in `.raw/` or cloud |
| `submit_job` | Submit to Minions queue | Use Hermes `delegate_task` or n8n workflow trigger |
| `get_job` | Get job details | Query Hermes job registry or n8n execution DB |
| `list_jobs` | List jobs | Same |
| `doctor` | Health check | `brain_health_check()` → run all dimension checks |

---

## Specific Skill Modifications Needed

### 1. `brain-ops` skill

**Original intent:** Always-on ambient behavior, not invoked directly.

**Our adaptation:**
- Don't create a separate skill file; instead incorporate into Hermes core:
  - Before any external tool call (web_search, database query), call `brain_search` automatically.
  - After any brain page update, call `brain_sync` (extract links).
- Document as convention in Operation_Instructions.md.
- Optionally, create a Hermes middleware that intercepts tool calls and injects brain-check.

**Implementation location:** In Hermes gateway's `execute_tool` hook.

---

### 2. `signal-detector` skill

**Original:** Fires on every message, parallel, never blocks. Captures ideas and entities.

**Our adaptation:**
- Create `~/hermes/skills/brain/signal-detector/SKILL.md` copying gbrain version.
- Modify frontmatter: `triggers: ["every inbound message"]` but Hermes doesn't auto-trigger on every message yet. We'll need a gateway hook.
- Tools: use our `brain_search`, `brain_put_page`, `brain_add_timeline_entry`.
- Add in code: `gateway.py` -> `on_message(message)` -> `if not is_pure_operational(message): Hermes.delegate_task("signal-detector", context=last_k_messages, notify_on_complete=False)`
- The skill itself reads last N messages from session or from Bot_Exchange queue? We'll pass the message content in context.

**Special handling for idea capture:**
- Use LLM to detect original thinking vs noise. Prompt: "Does this message contain a novel idea, observation, or thesis expressed by the user? If yes, extract the exact phrasing (verbatim)."
- If yes: create page in `originals/YYYY-MM-DD-<slug>.md` with frontmatter `type: original`, content: executive summary + "## User's Words" blockquote + analysis.
- If concept reference: create/update `concepts/`.

---

### 3. `ingest` router

**Original:** Routes to idea-ingest, media-ingest, meeting-ingest based on context.

**Our adaptation:**
- Create skill file as-is.
- But Hermes doesn't have automatic dispatch based on content type. We'll need explicit user command or webhook trigger.
- For now, implement separate commands:
  - `/brain ingest idea <url>` → calls `idea-ingest`
  - `/brain ingest meeting <transcript>` → calls `meeting-ingestion`
  - `/brain ingest media <file>` → calls `media-ingest`
- Router skill remains useful for documentation but actual routing via CLI commands.

**Alternative:** If user says "I want to save this" with a link, the agent (via brain-ops) could call ingest route automatically.

---

### 4. `idea-ingest`

**Original:** Full pipeline: fetch → upload raw → author people page → file by primary subject → analyze → cross-link → sync.

**Our adaptation:**
- Copy skill file to `~/hermes/skills/brain/idea-ingest/SKILL.md`
- Implement missing tools:
  - `file_upload` → `brain_upload_raw`
  - `search`/`query` → our `brain_search`/`brain_query` (note: gbrain skill expects these to exist)
- Primary subject classification: Heuristic or LLM: read content, ask "What is the primary subject? (person/company/concept/sources)". If person → `people/slug`, company → `companies/slug`, concept → `concepts/slug`, else → `sources/` (but per filing rules should be rare).
- Analysis section must be genuine, not summary. Prompt: "Given what you know about Jason's work, what's interesting about this content? Flag contradictions, connections to existing brain pages, content opportunities."
- Cross-link: for each entity mentioned in content, ensure entity page exists (create/enrich stub) and add back-link from entity to this page (auto-link does this automatically on put_page if we use proper wikilinks). Ensure the page content includes `[[wiki/people/name]]` links for each entity.

**Implementation details:**
- When writing page, generate proper wikilinks: for entity "Jane Doe" with slug `people/jane-doe`, include `[[wiki/people/jane-doe]]` or `[Jane Doe](people/jane-doe.md)` in analysis section. Auto-link will create the graph edges.

---

### 5. `enrich`

**Original:** Tiered enrichment (Tier 1/2/3) with external APIs.

**Our adaptation:**
- Use our own external APIs: web_search (Brave/Perplexity), maybe Crustdata if we have API key.
- Tiering based on notability score: compute from existing page data (timeline entries, mentions in other pages).
  - Tier 1 (key): >10 timeline entries, or explicitly marked in frontmatter `tier: 1`, or inner circle people.
  - Tier 2 (notable): 3-10 entries, or frequent mentions.
  - Tier 3 (minor): stub just created.
- For Tier 1/2: call web research tool with prompt: "Find recent information about {name} relevant to {user_context}. Include current role, company, projects, recent news. Cite sources."
- Save raw responses: `brain_upload_raw(json_data, slug, type='enrich_raw')`
- Update page using templates (from gbrain person/company templates, adapted).

**Templates:** We'll need these in `templates/`:
- `person.md.j2`
- `company.md.j2`
- `concept.md.j2`
- `meeting.md.j2`
- `media.md.j2`

---

### 6. `meeting-ingestion`

**Original:** Transcript → meeting page → attendee enrichment → entity propagation → timeline merge.

**Our adaptation:**
- Trigger: when transcript file appears in `inbox/meetings/` or user command `/brain meeting <file>`
- Parse transcript: use LLM to extract attendees (names), date, decisions, action items, companies mentioned. Or use Circleback API if available.
- Create meeting page in `meetings/YYYY-MM-DD-<slug>.md`.
- For each attendee:
  - `brain_search(name)` → if none or stub, call `enrich` skill (light) to create/enrich people page.
  - Add timeline entry to attendee's page: `gbrain_add_timeline_entry(people/slug, date, "Attended <meeting title>")`.
  - Ensure meeting page links to each attendee with `[[wiki/people/slug]]`.
- For each mentioned company/concept: similar propagation (update timeline, cross-link).
- Auto-link will handle backlinks from attendee pages to meeting page if we use proper wikilinks.

**Important:** Meeting page should be a succinct summary, not raw transcript. Save raw transcript to `.raw/` with `brain_upload_raw`.

---

### 7. `media-ingest`

**Original:** Format detection (YouTube, audio, PDF, screenshot, GitHub) → raw upload → brain page with analysis → entity extraction → propagation.

**Our adaptation:**
- Build format handlers:
  - YouTube: `yt-dlp --write-subs --sub-format json3 <url>` gets transcript. Use that.
  - Audio: `faster-whisper` CLI or OpenAI Whisper API.
  - PDF: `pymupdf` to extract text; if fails, OCR with `tesseract` (may need image conversion).
  - Screenshot: vision model - could use `ollama run llava:13b` or OpenAI GPT-4o if available.
  - GitHub: `git clone <repo>` shallow, then read `README.md` and top-level `*.py`/`*.js` files with `tree` structure.
- Primary subject classification: LLM-based: "What is this media primarily about? (a person, a company, a software concept, a general topic)". Then file accordingly.
- Analysis: executive summary + highlights + significance to user's work.
- Entity extraction: LLM scan of content to list people/companies → feed into `enrich` (light).
- Raw: upload source file or transcript JSON to `.raw/`.

**Implementation:** Build as Python module `media_handlers.py` with functions `handle_youtube`, `handle_audio`, `handle_pdf`, etc. `media-ingest` skill calls appropriate handler.

---

### 8. `voice-note-ingest`

**Original:** STT → decision tree → route to originals/, concepts/, people/, etc. Verbatim preservation.

**Our adaptation:**
- Already have Telegram voice messages arriving as `.ogg` files.
- Transcribe: use `faster-whisper` (local) for privacy and no cost. Command: `whisper audio.ogg --model tiny --language en --output_format txt`
- Decision tree exactly as in skill:
  1. Is it the user's original thought (novel idea/thesis)? → `originals/`
  2. Is it referencing a concept someone else created? → `concepts/`
  3. About a specific person? → `people/` timeline entry
  4. About a specific company? → `companies/` timeline entry
  5. Product/business idea? → `ideas/` (create this directory)
  6. Personal reflection? → `personal/` (therapy-adjacent)
  7. Else → `voice-notes/` catch-all
- Page format: frontmatter with `type`, `tags: [voice-note]`, `sources.voice-note.storage_path` pointing to stored audio.
- Executive summary of what was said and why it matters.
- **"User's Words"** section: verbatim transcript in blockquote.
- **Analysis** section: interpretation.
- Link to audio file: if stored locally, relative path; if cloud, URL.
- Citation: `[Source: voice note, Telegram, YYYY-MM-DD]`

**Implementation:** Write script `voice_note_ingest.py` that takes audio file path, transcribes, classifies, writes page, uploads raw audio to `.raw/voice-notes/`, cross-links entities.

---

### 9. `briefing` (enhanced)

**Original:** Compile daily briefing with meeting context, active deals, citation tracking. Includes hot memory pulse from `gbrain recall`.

**Our adaptation:**
- We already have daily briefing cron. Enhance it:
  1. Add `brain_query` calls to gather context:
     - Active deals: `brain_query("active deals status")` (but we'd need deal pages with status field). Maybe too early; skip deals until we have CRM.
     - People in play: `brain_list_pages(type="person", sort="updated", limit=10)`
     - Recent changes: same but last 24h.
     - Stale pages: `maintain` dimension for stale pages.
  2. For today's meetings (from calendar), for each attendee, do `brain_get_page` and extract compiled truth + recent timeline. Summarize.
  3. Action items: parse timeline entries with TODO keywords or from `open_threads/` if we have that.
  4. Citations: every fact from brain must include `[Source: slug, updated DATE]`.
- Hot memory pulse: we don't have `gbrain recall` yet. Substitute: query recent timeline entries (last 7 days), group by entity, show top entities by mention count, list new facts. Use `brain_get_timeline` for top slugs.

**Implementation:** Modify existing briefing generation code (likely in `hermes/scripts/briefing.py` or similar) to call brain tools.

---

### 10. `maintain` (full)

**Original:** Multi-dimension health check with remediation.

**Our adaptation (Python version):**
- Implement each dimension check as function:
  - `check_stale()`: for all person/company pages, compare `compiled_truth` last updated vs latest timeline entry date. Flag if timeline newer than compiled_truth by >30 days.
  - `check_orphans()`: query `brain_get_backlinks(slug)`; if count=0 and page not in `sources/` (which may be intentionally orphan), flag.
  - `check_dead_links()`: parse all pages for wikilinks; verify target exists. Flag missing.
  - `check_missing_crossrefs()`: entity mentions in text without corresponding link (heuristic: proper noun not linked). Flag.
  - `check_backlink_violations()`: for each entity mentioned in a page, check that entity page has back-link to this page.
  - `check_citation_gaps()`: scan timeline entries for `[Source: ...]` presence. Count missing.
  - `check_filing_violations()`: pages in `sources/` that contain references to specific people/companies → misfiled.
  - `check_tag_consistency()`: collect all tags, find variants (e.g., "vc" vs "venture-capital"), suggest standard.
  - `check_embedding_staleness()`: if using Chroma, check if page's latest chunk is embedded with recent model version.
  - `check_open_threads()`: timeline entries with "TODO" or "follow up" language older than 30 days.
- Compute health score (weighted average).
- Output JSON with dimension scores and lists of affected pages.
- Add `--remediate` flag to auto-fix what we can: fix citation format, add missing backlinks (with conservative type inference), remove dead links.

**Implementation:** Write `hermes/skills/brain/maintain/SKILL.md` and Python implementation `hermes/skills/brain/maintain.py`.

---

## Cron Job Adaptations

From gbrain's reference schedule, adapt each to Hermes `cronjob`:

| gbrain Cron | Our Hermes Cron | Notes |
|-------------|----------------|-------|
| Email monitoring (30 min) | `cronjob(profile='default', schedule='*/30 * * * *', prompt='Run email-to-brain integration...', skills=['email-to-brain'])` | Need email-to-brain skill |
| X/Twitter collection (30 min) | similar | Need x-to-brain skill |
| Meeting sync (3x/day weekdays) | `schedule='0 10,16,21 * * 1-5'` | Use meeting-ingestion skill |
| Calendar sync (weekly) | `schedule='0 10 * * 0'` | calendar-to-brain skill |
| Morning briefing (daily AM) | existing cron, but skill changes to `briefing` | Enhance briefing skill |
| Brain maintenance (weekly) | `schedule='0 6 * * 1'`, skills=['maintain'] | Implement maintain skill |
| Dream cycle (nightly) | `schedule='0 2 * * *'`, skills=['dream-cycle'] | Implement dream-cycle orchestrator |

Important: Add quiet hours check at start of every notification-sending cron job. In Hermes, we can add `quiet_hours_gate=True` parameter to cronjob (new feature). Or just code it into the skill.

---

## Token Cost Tracking Adaptation

Gbrain tracks tokens and cost per job. Our Hermes already has some token accounting but not integrated with brain jobs.

**What to do:**
- In Hermes `delegate_task` calls, capture `tokens_in`, `tokens_out` from subagent result summary.
- Store in `system_registry/job_executions.jsonl` with fields:
  ```json
  {"job_id": "...", "timestamp": "...", "skill": "enrich", "tokens_in": 1234, "tokens_out": 5678, "cost_usd": 0.045, "duration_s": 45, "status": "success"}
  ```
- For manual LLM calls inside skills, use Hermes `llm_call` utility which already tracks tokens; add wrapper to accumulate.
- For openai models, compute cost via pricing table (in `config.yaml` or hardcoded dict).
- Report in maintain skill: total weekly cost, per-job breakdown.

---

## Raw Source Preservation Adaptation

Gbrain's `upload-raw` size routing:
- <100MB: store in git (`.raw/` sidecar)
- >=100MB: cloud upload with redirect

Our simpler version:
- Always store locally in Brain/ under `.raw/` subdirectory adjacent to page.
  - For page `people/jane.md`, raw files go in `people/.raw/jane/` (mkdir)
  - For page `meetings/2026-06-14.md`, raw in `meetings/.raw/2026-06-14/`
- Keep everything in the same NFS share (no cloud yet).
- If we later add cloud, implement redirect pointer format and `brain_files_signed_url` tool.

Implementation: `brain_upload_raw(file_path, page_slug, type)`:
1. Compute target dir: `(Brain_dir / page_slug).parent / ".raw" / page_slug.name`
2. Copy file there with timestamp prefix if needed to avoid collisions.
3. Return storage info: `{"storage": "local", "path": str(target_path)}`
4. Save metadata in page frontmutter `sources.{type}.storage_path`

---

## Filename and Slug Discipline

Gbrain enforces:
- Slug: lowercase alphanumeric and hyphens only, slash-separated. NO underscores, NO file extensions in slug (slug is directory path without `.md`).
- Example: `people/jane-doe` → file `people/jane-doe.md`

Our adaptation:
- In `brain_put_page(slug, ...)`:
  - Validate: `slug` matches `r'^[a-z0-9][a-z0-9_-]*(/[a-z0-9][a-z0-9_-]*)*$'`
  - Reject uppercase, spaces, underscores, file extensions.
- File path: `f"{slug}.md"`
- Create parent directories if needed.

Also for synthesized pages (dream cycle, concept-synthesis), use date prefixes: `YYYY-MM-DD-<slug>.md`.

---

## Dream Cycle Phase Details for Python

We need to implement these phases as skills:

1. **Entity Sweep**: use `signal-detector` but with a flag to only detect entities and enrich (skip idea capture to avoid duplicates). Could run signal-detector with `mode: entities-only`.
2. **Citation Hygiene**: `citation-fixer` skill.
3. **Consolidate**:
   - `concept-synthesis` for concept stubs
   - Pattern detection: query recent originals with `brain_query` using embeddings to find near-duplicates or clusters. Run LLM to synthesize into pattern pages under `patterns/`.
4. **Embed Stale**: `brain_embed --stale`
5. **Extract Graph**: `brain_extract all`
6. **Health Check**: `maintain`

Orchestrator: `dream-cycle` skill that runs phases in order, collects reports, writes summary to `dream-cycle-summaries/YYYY-MM-DD.md`.

---

## Command Reference for Our Implementation

We'll maintain a `docs/BRAIN_CLI.md` (or `gbrain-cli-equivalent.md`) mapping:

```
brain search <query>                # keyword search
brain query <question>              # hybrid search
brain get <slug>                    # read page
brain put <slug> <content> [--frontmatter key=value...]  # write page
brain timeline-add <slug> <date> "<summary>" [--source ...]  # add entry
brain link add <source> <target> <type>  # create link
brain links <slug>                  # list outgoing links
brain backlinks <slug>              # list incoming links
brain upload-raw <file> <slug> <type> # store raw source
brain extract links [--dir Brain/]   # backfill link graph
brain extract timeline [--dir Brain/] # backfill timeline entries
brain embed [--stale]               # generate embeddings
brain health                        # run health checks
brain doctor --remediate --target-score 90  # auto-fix (future)
brain dream                         # run full dream cycle
```

These can be either CLI commands or MCP tools. For cronjobs, we'll call Hermes skills directly (they call these tools internally).

---

## Testing Strategy

For each skill and tool:
1. Unit test the tool function (pure Python) with fixtures.
2. Integration test: run skill on small dataset, verify output.
3. Conformance test: skill frontmatter triggers match, output format matches spec.

We can adapt gbrain's test framework but simpler: use `pytest`.

---

## Migration Considerations

Existing Brain content lacks frontmatter and structured timeline. Our tools should tolerate that:
- `brain_get_page` should parse optional frontmatter; if missing, return empty dict.
- `brain_put_page` will add frontmatter on first write if not present.
- `brain_extract_links` and `timeline` will work even if no existing structured data.

Over time, as pages get updated, they'll acquire proper frontmatter and structured links.

We could also write one-time migration scripts:
- Add minimal frontmatter to all `.md` files: `---\ntitle: <filename>\ncreated: <mtime date>\n---`
- Extract existing wikilinks to links index.

But not necessary; incremental is fine.

---

## Summary

We will **copy gbrain skill files verbatim** (they are excellent documentation and specification). Then implement the missing tools in Python, adapting to our environment (storage, job queue, credentials). The heavy lifting is implementing the tools, not rewriting the skills.

Key files to create in `~/hermes/`:
- `tools/brain_*.py` (tool implementations)
- `skills/brain/*.SKILL.md` (adapted from gbrain)
- `scripts/brain_extract_all.py`, `brain_embed.py`, `brain_health.py`
- `docs/BRAIN_CLI.md`, `docs/BRAIN_SCHEMA.md`, `docs/_brain-filing-rules.md`
- Update `Operation_Instructions.md` with conventions

Start with the quick wins to get basic read/write/search working, then build up the advanced skills in Phase 1-3 of the implementation plan.