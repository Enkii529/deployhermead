# 04_IMPLEMENTATION_PLAN.md

Phased adoption of gbrain patterns into our Brain over 8-12 weeks.

---

## Phase 0: Preparation (Week 0)

**Goal:** Set up analysis workspace, evaluate gbrain CLI compatibility, decide on vector DB.

### Tasks

1. **Explore gbrain CLI** (if Bun/TypeScript install feasible)
   - Try installing: `bun install -g github:garrytan/gbrain`
   - Run `gbrain init --pglite` to test PGLite
   - If fails due to Bun/TypeScript deps, fall back to **reimplement in Python**

2. **Evaluate Python alternatives** for vector search:
   - `chromadb` (embedded, easy)
   - ` LanceDB` (embedded, fast)
   - `pgvector` via Supabase (external but robust)
   - Custom SQLite + `sentence-transformers` + `numpy`

   **Recommendation:** Start with ChromaDB for simplicity, can migrate later.

3. **Create analysis workspace**
   - Done: `~/hermes-command-center/gbrain_analysis/`
   - Add these files: 00_OVERVIEW.md, 01_SKILLS_MAPPING.md, 02_CRON_JOBS_MAPPING.md, 03_ARCHITECTURE_GAPS.md, 04_IMPLEMENTATION_PLAN.md, 05_QUICK_WINS.md, 06_SKILL_ADAPTATIONS.md, 07_INTEGRATION_POINTS.md

4. **Update Operation_Instructions.md** (draft additions)
   - Add section: "Brain-First Convention" - always check brain before external APIs
   - Add section: "Signal Detection" - ambient capture on every message
   - Add section: "Filing Rules" - primary subject, notability gate, raw source preservation
   - Add section: "Citation Standard" - `[Source: ...]` format, source precedence

5. **Set up experimental vector DB** in `~/brain-experiment/`
   - Initialize ChromaDB collection for brain pages
   - Write script to embed pages using `sentence-transformers/all-MiniLM-L6-v2`
   - Test hybrid search prototype (keyword + vector + RRF)

**Deliverables:**
- Decision memo: PGLite vs Python vector store
- ChromaDB prototype with 100 page samples
- Updated Operation_Instructions.md draft

---

## Phase 1: Foundation (Weeks 1-2)

**Goal:** Implement core brain operations, signal detection, file-based retrieval, basic filing.

### Week 1: Brain-First & Signal Detection

**Skill 1: brain-first (convention enforcement)**
- Path: `~/hermes/skills/devops/brain-first/SKILL.md`
- Purpose: Validate that any skill making external API calls has performed brain-first lookup first.
- Implementation: Wrapper skill that logs warning if `web_search` or similar called without preceding `brain_search` for the same entity.
- Not a full skill; instead add to Operation_Instructions.md and implement as Python decorator in Hermes core? For now, document and rely on developer discipline.

**Skill 2: signal-detector**
- Path: `~/hermes/skills/brain/signal-detector/SKILL.md`
- Triggers: every inbound message (Hermes gateway hook)
- Tools: `brain_search`, `brain_put_page`, `brain_add_timeline_entry`
- Mutating: true
- Writes to: `originals/`, `concepts/`, `people/`, `companies/`
- Implementation steps:
  1. Hook: Add to Hermes gateway message processor to spawn subagent with this skill for every user message (except pure ops like "ok", "thanks").
  2. In skill: parse message for original thinking (LLM call: "Is there a novel idea, observation, or thesis in this? Extract verbatim.")
  3. If original: create page in `originals/YYYY-MM-DD-<slug>.md` with exact quote, analysis, cross-links to entities.
  4. Extract entities (LLM call or regex for proper nouns).
  5. For each entity: `brain_search` existing page; if none and notable → create stub (enrich later); if exists but thin → enrich.
  6. Log summary: `Signals: 1 idea (originals/x), 2 entities (enriched people/y, companies/z)`.
  7. Run as subagent with `notify_on_complete=false` (fire-and-forget).

**Skill 3: brain-ops (ambient layer)**
- Path: `~/hermes/skills/brain/brain-ops/SKILL.md`
- This skill is not directly invoked; it's a convention. But we need the operations it describes:
  - `brain_search(query)` - keyword search over markdown files
  - `brain_query(question)` - hybrid search (Phase 2)
  - `brain_get_page(slug)` - read file
  - `brain_put_page(slug, content, frontmutter)` - write file with auto-links
  - `brain_add_timeline_entry(slug, date, summary)` - append to timeline
  - `brain_sync()` - update index (for DB-backed, not needed for pure files)
- Implementation: Initially implement as file operations. `brain_search` uses `ripgrep` over Brain/. `brain_get_page` reads file. `brain_put_page` writes with atomic replace.
- Add auto-link extraction: parse content for `[[wiki/people/name]]` and `[Name](people/slug)` patterns; update `links` table later (deferred to Phase 2).

**Schema definition:**
- Create `docs/BRAIN_SCHEMA.md` documenting frontmatter fields per type.
- Create templates: `templates/person.md.j2`, `templates/company.md.j2`, `templates/concept.md.j2`.

**Deliverables:**
- `brain-first` convention documented
- `signal-detector` skill deployed and running (subagent)
- `brain-ops` tools available to Hermes
- Basic filing: originals/, concepts/ directories created in Brain/
- Test: send message with idea + person mention → see originals/ page and people/ page created

---

### Week 2: Ingestion Router + Idea Ingest + Basic Enrich

**Skill 4: ingest (router)**
- Path: `~/hermes/skills/brain/ingest/SKILL.md`
- Detects content type from context (user says "read this", provides link, meeting transcript, etc.)
- Dispatches to: `idea-ingest`, `meeting-ingestion`, `media-ingest`
- Enforcement: calls `_brain-filing-rules.md` before any write

**Skill 5: idea-ingest**
- Path: `~/hermes/skills/brain/idea-ingest/SKILL.md`
- When user shares URL or says "save this / read this / think about this"
- Steps:
  1. Fetch content (web_extract)
  2. Upload raw: `brain_upload_raw(content, page_slug, type='article')` → store in `sources/.raw/`
  3. Identify author: `brain_search(author_name)` → create/update people page with author role
  4. Determine primary subject: if article about person → `people/`; about company → `companies/`; about framework → `concepts/`
  5. Write brain page with analysis (not summary). Include: Context, Summary, Key Data/Claims, Analysis connecting to existing brain.
  6. Cross-link: all mentioned entities → enrich (light) and add back-link
  7. `brain_add_timeline_entry(page_slug, date, "Ingested article")`
  8. Sync (if DB-backed)

**Skill 6: enrich (tiered)**
- Path: `~/hermes/skills/brain/enrich/SKILL.md`
- For creating/updating person/company pages with external data.
- Tiers:
  - Tier 1 (key): full pipeline (web research, social, APIs like Crustdata/Crunchbase)
  - Tier 2 (notable): web + social
  - Tier 3 (minor): brain cross-ref + social if handle known
- Template: use person/company templates from gbrain (adapt to our data sources)
- Notability gate: implement as function `is_notable_entity(type, name, context)` using heuristics (frequency, relationship strength)
- For now, skip expensive API keys (Crunchbase etc). Use web search only.

**Deliverables:**
- `ingest` router skill
- `idea-ingest` skill (can fetch articles, save to brain)
- `enrich` skill (light version with web search)
- Upload raw working (local `.raw/` storage)
- Test: User shares article → brain page created with analysis, author people page updated, entities cross-linked

---

### Week 2 also: File-Based Graph Extraction

**Skill 7: brain-extract (links + timeline)**
- Path: `~/hermes/skills/brain/brain-extract/SKILL.md`
- Two subcommands:
  - `extract links --dir Brain/` - scans all markdown for entity references, populates links table (or JSON file if no DB yet)
  - `extract timeline --dir Brain/` - parses `- **YYYY-MM-DD** | entry` lines, populates structured timeline
- Idempotent: can run repeatedly without duplication.
- Run as cron weekly or after bulk imports.

**Implementation without DB:**
- Create `brain_data/links.jsonl` and `brain_data/timeline.jsonl` files
- Each line: `{"source": "people/jane.md", "target": "companies/acme.md", "type": "works_at", "confidence": 1.0}`
- Query tools read these JSONL files and cache in memory.

**Later (with DB):** Migrate to SQLite/PGLite tables.

**Deliverable:** Extraction scripts working, producing JSONL index files. `brain_get_backlinks(slug)` reads from these files.

---

## Phase 2: Hybrid Search & Graph Queries (Weeks 3-4)

**Goal:** Add vector embeddings and hybrid search; implement auto-linking; make brain queryable like a knowledge graph.

### Week 3: Vector Database Integration

**Task 8: Choose and set up vector store**
- If using PGLite: install gbrain binary, run `gbrain init --pglite`, let it create schema. Then our Hermes skills call the `gbrain` CLI via subprocess or we bind to its TypeScript library (harder).
- If using Python: set up ChromaDB at `~/brain/.chroma/` with collections: `pages`, `chunks`, `entities`.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (local, no API cost) or OpenAI `text-embedding-3-small` (better quality, cost ~$0.02/1k tokens)
- Chunker: split pages into ~500 token chunks with 10% overlap. Store mapping: chunk → page_slug → offset.

**Task 9: brain_query (hybrid search)**
- Path: add tool to `brain-ops` skill
- Algorithm:
  1. Keyword search: `rg --json "query" Brain/` → collect matching pages with scores (filename matches, term frequency)
  2. Vector search: embed query, search ChromaDB for top-50 chunks, aggregate by page → page-level vector scores
  3. RRF fusion: `score_rrf = 1/(k + rank_keyword) + 1/(k + rank_vector)` where k=60 (typical). Combine scores.
  4. Optional reranker: take top 20, use cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` to re-rank.
  5. Return top 10 pages with `{slug, title, snippet, score}`.
- Store in `brain_data/search_cache.jsonl` for debugging.

**Task 10: brain_embed (refresh embeddings)**
- Skill: `brain-embed` - re-embeds pages that are stale or missing embeddings.
- Determine stale: compare `mtime` of markdown file vs entry in embedding index.
- Process: read page, chunk, embed each chunk, upsert to vector DB.
- Report: pages embedded, chunks added, cost (if using OpenAI).
- Can run as cron weekly.

**Deliverables:**
- Vector DB set up and indexing initial 1000 pages
- `brain_query` tool available, returns relevant results
- `brain_embed` skill working (test on 10 pages)
- Benchmark: compare keyword-only vs hybrid on known queries

---

### Week 4: Auto-Linking + Graph API

**Task 11: Auto-link post-hook**
- Modify `brain_put_page` to automatically:
  1. Parse page content after write for entity links (wikilinks `[[...]]`, md links `[name](people/slug)`)
  2. Load existing links for this page from links table/index
  3. Compute diff: new links, removed links
  4. Upsert links with confidence 1.0, type inference heuristics:
     - If source page type=meeting and target type=person → `attended`
     - If source page type=person and target type=company → `works_at` (if `company` frontmatter matches)
     - Default: `mentions`
  5. Remove dead links
- Log: `auto_links: {created: 5, removed: 0, errors: []}`

**Task 12: Graph query tools**
- `brain_get_backlinks(slug)` - return pages that link to this entity (from links index)
- `brain_traverse_graph(slug, depth=2, link_types=None)` - BFS from slug, return subgraph JSON
- `brain_resolve_slugs(query)` - fuzzy slug resolution (Levenshtein distance or embeddings)

**Task 13: Maintain skill (basic)**
- Implement first phase: back-link enforcement check
  - For each page, extract entity mentions; verify corresponding backlink exists from those entities to this page.
  - Report violations count; optionally fix by adding missing backlinks.
- Run as weekly cron.

**Deliverables:**
- Auto-link active on every `brain_put_page`
- Graph tools working
- Basic maintain skill with backlink check

---

## Phase 3: Ingestion at Scale (Weeks 5-6)

**Goal:** Full meeting ingestion, media ingestion, voice note ingestion, enrichment with external APIs.

### Week 5: Meeting Ingestion

**Skill 14: meeting-ingestion**
- Path: `~/hermes/skills/brain/meeting-ingestion/SKILL.md`
- Triggers: "meeting transcript", transcript file received, calendar event with notes
- Pipeline:
  1. Parse transcript (from Circleback/Grain/Otter). Extract: attendees (names), date, topics, decisions, action items, companies mentioned.
  2. Create meeting page in `meetings/YYYY-MM-DD-<slug>.md` using template.
  3. For each attendee:
     - `brain_search(name)` → if exists, update timeline with "Attended <meeting>" and add new insights from meeting to compiled truth if material
     - If not exists: create stub person page (enrich later in dream cycle) with basic info from meeting context
  4. For each company/concept mentioned: propagate timeline entries
  5. Back-links: auto-link handles most; verify
  6. Sync/embed
- Quality: meeting page must have compelling summary, key decisions, action items with owners. Not a raw transcript dump.

**Task 15: Calendar sync integration**
- Cron job daily 10 PM: fetch tomorrow's Google Calendar events via Gmail/Calendar API (credentials already in `credentials.txt`).
- For each event with >=2 attendees: create placeholder meeting page (title, attendees, time) even without transcript.
- Enrich attendees immediately (call `enrich` lightly).
- Add to `brain_data/tomorrow_meetings.json` for briefing.

**Deliverable:** Meeting ingestion end-to-end: transcript → meeting page + attendee enrichment + entity propagation. Calendar integration populates meeting pages ahead of time.

---

### Week 6: Media & Voice Ingestion

**Skill 16: media-ingest**
- Handle YouTube, podcasts, PDFs, screenshots, GitHub repos.
- Subroutines:
  - YouTube: fetch transcript via `youtube-transcript-api` or `yt-dlp --sub`. Save raw transcript JSON + TXT. Create page under `media/videos/` with summary, highlights, timestamps, people/company entities extracted.
  - Podcast/audio: transcribe with Whisper (local `openai/whisper` via `faster-whisper`). Same as video.
  - PDF: extract text with `pymupdf` or `pdfminer`. If scanned, OCR via `tesseract`.
  - Screenshot: vision model (CLIP or LLaVA) to extract text + entities.
  - GitHub: clone repo, read README + key files (package.json, src/*.py), summarize architecture.
- Primary subject filing: if video about a person → `people/`; about a company → `companies/`; about a concept → `concepts/`; general content → `media/videos/` (format-based fallback only if no clear subject)
- Entity extraction: run LLM on content to extract people/companies → enrich.
- Raw file: upload to `.raw/` or cloud.

**Skill 17: voice-note-ingest**
- When user sends voice note via Telegram (we already receive audio).
- Transcribe: use `faster-whisper` local or OpenAI Whisper API.
- Apply decision tree (from skill):
  - Original idea → `originals/`
  - Concept reference → `concepts/`
  - About person → `people/` timeline
  - About company → `companies/` timeline
  - Product idea → `ideas/`
  - Reflection → `personal/`
- Preserve verbatim transcript in blockquote. Analysis section.
- Upload raw audio to storage.
- Citation: `[Source: voice note, Telegram, YYYY-MM-DD]`

**Deliverables:**
- `media-ingest` handling YouTube and PDFs
- `voice-note-ingest` handling Telegram audio
- Both produce proper brain pages with entity cross-links

---

## Phase 4: Dream Cycle & Maintenance (Weeks 7-8)

**Goal:** Nightly orchestrated maintenance; health monitoring; automated fixes.

### Week 7: Dream Cycle Implementation

**Skill 18: dream-cycle (orchestrator)**
- Path: `~/hermes/skills/brain/dream-cycle/SKILL.md`
- Triggered by cron at 2 AM.
- Phases:

1. **Entity Sweep** (signal-detector on today's sessions):
   - Gather all conversation logs from: Bot_Exchange/queue/processed/, inter_agent_tasks/completed/, system_registry/OPENCLAW_WORKLOG.md, Telegram DM export (if available).
   - For each message, run signal-detector (but only entity detection, not full idea capture to avoid duplication). Actually could just call `signal-detector` with a flag to skip idea capture? Or run full and rely on idempotency.
   - For entities found: if page missing create stub; if thin (few timeline entries, no compiled truth) run `enrich` (Tier 3 light).
   - Log: `N entities processed: M created, K enriched`.

2. **Citation Hygiene**:
   - Run `citation-fixer` on pages updated in last 7 days.
   - Focus on timeline entries missing `[Source: ...]`.
   - For tweet patterns, resolve via X API if configured.

3. **Consolidate** (memory):
   - Run `concept-synthesis` on new concept stubs from last week.
   - Identify patterns: script runs `brain_query("recurring themes in originals/")` or manual detection via clustering embeddings of recent originals.
   - Write pattern pages to `patterns/<theme>` if ≥3 reflections support.

4. **Embed Stale**:
   - Run `brain_embed --stale` to refresh embeddings for pages changed since last embed.
   - If using OpenAI, respect rate limits; if local, no cost but CPU/GPU heavy.

5. **Extract Graph**:
   - Run `brain-extract links` and `brain-extract timeline` to backfill structured data from markdown changes.
   - This syncs the JSONL files or DB with latest content.

6. **Health Check & Report**:
   - Run `maintain` (full health check with all dimensions)
   - Save report to `system_registry/dream-cycle-YYYY-MM-DD.md` with before/after scores, issues fixed, remaining gaps.
   - Update `brain_data/health_history.jsonl`.

**Idempotency & cooldown:**
- Use `system_registry/dream_cycle_last_run.json` with completed phases and timestamps.
- If a phase fails, log error but continue to next; final report notes failures.
- Cooldown: don't run if last run was < 24h ago (cron ensures nightly but guard against manual runs).

**Deliverable:** Dream cycle cron job working end-to-end, producing morning report.

---

### Week 8: Maintain Skill + Citation Fixer

**Skill 19: maintain** (full)
- Full 12-dimension health check:
  1. Stale pages: compiled_truth older than latest timeline entry (use timeline index)
  2. Orphan pages: pages with zero backlinks (query links index)
  3. Dead links: links in content to non-existent pages
  4. Missing cross-refs: entity mentions without formal link
  5. Back-link violations: entity mentions missing reciprocal link
  6. Citation gaps: facts without `[Source: ...]`
  7. Filing violations: pages in `sources/` that have primary subject elsewhere
  8. Tag inconsistencies: variant tags (e.g., "vc" vs "venture-capital")
  9. Embedding staleness: chunks without embeddings or old model
  10. Security: RLS (if using Postgres) - skip for now
  11. Schema health: frontmatter required fields present
  12. File storage: orphan `.redirect.yaml`, large files in git
  13. Open threads: timeline entries >30d with unresolved action items
- For each dimension, produce count and optionally fix (auto where safe).
- Return health score (0-100) with weighted sum (weights TBD).

**Skill 20: citation-fixer**
- Batch scan pages for citation compliance.
- Format standardization: ensure all citations match `[Source: provider, YYYY-MM-DD]` or `[Source: User, context, YYYY-MM-DD]` or `[Source: X/@handle, YYYY-MM-DD](URL)`.
- For tweets without URLs, use X API to search and fix (if credentials available).
- Save state in `~/.hermes/citation-fixer-state.json` for incremental runs.
- Output: `Pages scanned: N, Citations fixed: M, Remaining gaps: K`.

**Weekly cron:**
```json
{
  "schedule": "0 6 * * 1",
  "prompt": "Run brain health check and citation audit. Generate report in system_registry/brain-health-YYYY-MM-DD.md. Auto-fix: backlinks, citation format, dead links. Do not modify page content without user approval.",
  "skills": ["maintain", "citation-fixer"],
  "deliver": "local"
}
```

**Deliverables:**
- `maintain` skill covers all dimensions
- `citation-fixer` skill batch processes
- Weekly health report automatic
- Initial health baseline established

---

## Phase 5: Enhancements & Integrations (Weeks 9-10)

**Goal:** Add briefing integration, cost tracking, more integrations.

### Week 9: Briefing + Daily Prep Enhancement

**Skill 21: briefing (brain-integrated)**
- Enhance existing briefing skill:
  1. Hot memory pulse: run `gbrain recall` equivalent: fetch all timeline entries from last 7 days, group by entity, identify top mentions, new facts, contradictions.
  2. Today's meetings: for each meeting on calendar, load attendee brain pages (compiled truth + recent timeline). Summarize: who they are, relationship, open threads.
  3. Active deals: query `deals/` pages with status=active, deadline in next 7 days.
  4. Threads: timeline entries with TODO keywords and due date in next 48h.
  5. Recent changes: pages updated in last 24h.
  6. People in play: person pages updated in last 7d sorted by recency.
  7. Stale alerts: pages flagged as stale that are relevant to today's meetings.
- Every fact in briefing includes `[Source: slug, updated DATE]`.
- Output format: markdown sent as Telegram message or voice memo.

**Skill 22: daily-task-prep**
- Morning prep skill: similar to briefing but more actionable.
- Load today's meetings → per-attendee context cards with what to know.
- Check yesterday's threads → unresolved items.
- Review active tasks from `ops/tasks/` (if we use that system).
- Compile into bullet list: "Before meeting X: Y is working on Z, watch for A".

**Cron:**
- `daily-briefing` at 7 AM (existing) now calls enhanced `briefing` skill.
- `daily-prep` at 6:30 AM (new) calls `daily-task-prep`.

**Deliverable:** Morning briefing includes brain-derived context; actionable prep cards.

---

### Week 10: Email & Twitter Integrations

**Skill 23: email-to-brain**
- Email collector: every 30 min, connect to Gmail via IMAP (or Gmail API).
- For each unread email (or all since last run):
  - Parse: sender, recipients, subject, body, date.
  - Save raw email to `sources/.raw/emails/YYYY-MM-DD-<id>.eml`
  - Sender → enrich person page (light Tier 2: web + brain cross-ref)
  - Identify mentioned entities (people, companies, concepts) → enrich lightly
  - If email is meeting notes or contains meeting details → create meeting page (with attendees extracted)
  - If email contains links → trigger `idea-ingest` for each link
  - Add timeline entry to sender's page: "Emailed you about <topic>"
- Use idempotency: store processed email IDs in `system_registry/email_ids.jsonl` to avoid duplicates.
- Notifications: only if sender is high-priority (from priority_senders list in config). Otherwise just log.

**Skill 24: x-to-brain**
- Twitter/X monitor: every 30 min, use X API (v2) to fetch tweets from home timeline or specific list of followed accounts (from brain people pages with twitter field).
- For each tweet:
  - Save raw JSON to `sources/.raw/tweets/`
  - If author has brain page → update their timeline: "Tweeted: <snippet>"
  - Extract mentioned entities (including author) → enrich
  - Create media page under `media/x/YYYY-MM-DD-<tweet-id>.md` with author link, content, metrics (likes, RTs)
  - Detect deletions: periodically check stored tweets; if gone, mark as deleted in timeline (`[DELETED]`)
- Use since_id to avoid re-fetching.

**Credential check:** Ensure `credentials.txt` has Twitter API bearer token and Gmail credentials (OAuth2 or app password). Use ClawVisor pattern if available.

**Deliverables:**
- Email and Twitter pipelines operational
- Raw sources preserved
- Entity propagation working
- Notifications only for high-priority senders (respect quiet hours)

---

## Phase 6: Optimization & Advanced (Weeks 11-12+)

**Goal:** Cost tracking, skill optimization, pattern detection, soul audit, migration readiness.

### Week 11: Cost Tracking & Health Automation

**Skill 25: doctor_remediate** (automated remediation)
- Orchestrator that:
  1. Runs `maintain` to get current health score and dimension issues
  2. Plans fixes in dependency order (extract links → extract timeline → fix backlinks → fix citations → embed stale)
  3. Estimates cost per step (DB operations cheap, LLM calls expensive)
  4. Respects `--max-usd` cap (configurable, default $5/night)
  5. Submits each fix as Minion job (or Hermes subagent) and waits
  6. Re-checks health after each fix; stops if target score reached or cost cap hit
  7. Generates remediation report

**Task 26: Token & cost accounting**
- Modify Hermes cron execution to aggregate token counts from subagent jobs.
- Store in `system_regrain/cron_executions.jsonl`.
- For each LLM call, record model, tokens_in, tokens_out, cache_hits, cost_usd (using pricing table).
- Weekly summary: total cost per job, trending.

**Task 27: Health dashboard**
- Update Command Center Panel (`command_center_panel/`) to show:
  - Current health score (0-100) from last `maintain`
  - Pages count, entities count, links count, timeline entries count
  - Last sync time, last embed, last dream cycle
  - Cost report (last 7 days)
- This gives Jason visibility into brain health.

**Deliverable:** Automated health remediation with cost awareness; dashboard metrics.

---

### Week 12: Advanced Skills

**Skill 28: concept-synthesis** (heavy)
- Run weekly (maybe weekends) to consolidate concept stubs.
- Dedup: Jaccard similarity on titles + first paragraphs → cluster; LLM to verify semantic duplicates.
- Tier: score each concept on mention frequency, distinct months, timeline activity.
- Synthesize T1/T2 concepts: write synthesis narrative using timeline and linked pages.
- Generate `concepts/README.md` intellectual map with clusters.
- This is expensive (many LLM calls). Run during off-peak, with `--max-tokens` limits.

**Skill 29: soul-audit** (quarterly)
- Alignment check: "Is this brain still serving my goals?"
- LLM reads recent reflections, originals, pattern pages; asks: "What themes emerged? Are you happy with your focus?"
- Produces audited report with recommendations to adjust filing rules, skill priorities, integration scope.
- Not for faint of heart; runs every 90 days.

**Skill 30: skill-optimizer** (on demand)
- When user says "improve my X skill", runs:
  1. `--bootstrap-from-skill X` - read existing skill file
  2. Strengthen judges (create eval cases)
  3. Dry-run on 5 examples to get baseline score
  4. Run optimizer (LLM proposes improvements, test, iterate)
  5. Report diff + score delta
- Requires skill-optimizer infra (reference implementation in gbrain docs).

**Deliverables:** Advanced skills scaffolded; may not fully implement depending on time.

---

## Parallel Track: Integration with Existing Hermes

Throughout all phases, ensure new skills integrate cleanly with:
- Existing Hermes agent catalog (`~/.hermes/agent_catalog.json`)
- Operation_Instructions.md governance
- inter_agent_tasks protocol (we could offload some batch jobs to @hemesmsibot on Windows)
- Command Center Panel status updates
- n8n workflows (some cron jobs could be n8n scheduled triggers)

**Strategy:** Keep brain skills in `~/hermes/skills/brain/` subdirectory. Register them in agent catalog. Document triggers and tools in `docs/Skills_Catalog.md` (Brain section).

**Testing:** For each skill, write conformance test:
- Skill loads correctly
- Triggers match expected patterns
- Output conforms to format
- Side effects (files written) follow filing rules

Use gbrain's `test/skills-conformance.test.ts` as model; implement in Python using pytest.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PGLite install fails (Bun/TS) | Fall back to Python vector store (Chroma) and reimplement needed features. gbrain patterns still apply, just different backend. |
| Vector search quality poor | Experiment with embedding models; add reranker; tune chunk size; use hybrid weights. |
| Brain corruption from bugs | All writes go through `brain_put_page` which writes to temp file then atomic rename. Keep backups: `brain_backups/` daily incremental. |
| Cost runaway | Implement cost caps in all automated jobs. Use local embedding models where possible. Approve API keys manually. |
| Data loss from mis-enrichment | Keep raw source preserved; every fact has citation; can rebuild from sources if needed. |
| Skill proliferation without quality | Enforce convention linting; require tests before merging new skills; peer review (Jason approval). |
| Interference with existing Brain content | Maintain dual-write during transition? Or start fresh `brain_v2/` and migrate selectively. Prefer migration: write scripts to convert existing Brain content to new schema gradually. |

---

## Migration Plan from Current Brain

Our current Brain at `/media/sf_ClawdbotShared/Brain` contains:
- Mixed content: some wiki pages, some notes, some system files
- Skills in `Skills/` (capital S) - we'll move these to Hermes skills directory
- No structured graph, no vector index

**Approach:** Don't rewrite existing files yet. Build new infrastructure alongside. As we adopt skills, they will read existing pages and gradually enrich them (compiled truth, timeline, backlinks). The dream cycle will consolidate over time.

Steps:
1. Leave existing content as-is; new pages go in proper directories following filing rules.
2. Implement `brain-extract links` and `timeline` on entire corpus to bootstrap graph.
3. Run `enrich` on thin entity pages (people, companies) in background via dream cycle.
4. Over 3-6 months, brain self-organizes into canonical form.

If we want faster migration: write a one-time script that applies heuristics to existing markdown to generate frontmatter and extract links/timeline. But maybe not needed - organic growth is fine.

---

## Success Metrics

- **Coverage:** % of person/company pages with >1 timeline entry, compiled truth non-empty, >5 backlinks.
- **Health score:** Target >85 after 3 months.
- **Signal capture:** Daily average ideas captured (from signal-detector) > 5.
- **Entity growth:** New people/company pages created per week > 10.
- **Citation compliance:** >95% of timeline entries have proper source citation.
- **Graph connectivity:** Average link count per page > 3.
- **Self-maintenance:** Dream cycle runs without manual intervention >95% of nights.

---

## Rollout Schedule (Calendar View)

| Week | Phase | Key Milestones |
|------|-------|----------------|
| 0 | Preparation | PGLite/Chroma decision; prototype ready |
| 1 | Foundation | signal-detector live; brain-ops tools available |
| 2 | Ingestion | idea-ingest working; enrich Tier 3 |
| 3 | Vector DB | Chroma set up; brain_query functional |
| 4 | Graph | Auto-linking; backlinks API; maintain basic |
| 5 | Meetings | Meeting ingestion end-to-end |
| 6 | Media/Voice | YouTube/PDF/voice pipelines |
| 7 | Dream Cycle | Nightly orchestration working |
| 8 | Maintenance | Full maintain skill; weekly health report |
| 9 | Briefing | Brain-integrated morning briefing |
|10 | Integrations | Email & Twitter auto-ingest |
|11 | Optimization | doctor_remediate; cost accounting; dashboard |
|12+ | Advanced | concept-synthesis; skill-optimizer; soul-audit |

---

## Conclusion

This plan adopts gbrain's proven patterns while fitting our Hermes/OpenClaw stack. Start with Phase 1 immediately after this analysis is approved.

Next: Begin **Phase 0** - explore gbrain CLI compatibility, set up ChromaDB prototype, update Operation_Instructions.md.
