# 01_SKILLS_MAPPING.md

All 43 gbrain skills organized by category with:
- Skill purpose
- Our current equivalent (if any)
- Adaptation strategy
- Priority for adoption

---

## Category 1: Core Brain Operations (Always-On)

### brain-ops
**Purpose:** The ambient context layer. Core read-write cycle: brain-first lookup, read-enrich-write, source attribution, back-linking.
**Contract:** Brain checked before external API; inbound signals trigger READ→ENRICH→WRITE; outbound responses pull context; user statements highest authority; back-links maintained.
**Our Status:** ❌ No equivalent
**Adaptation:** This is the fundamental pattern. Must implement as a Hermes skill that runs on every message (signal detector pattern). Use brain-context first.
**Priority:** **CRITICAL** - Foundation for everything else

### signal-detector
**Purpose:** Always-on ambient signal capture. Fires on every inbound message detecting original thinking AND entity mentions with equal priority. Runs in parallel, never blocks.
**Contract:** Fires on every message (except pure ops); captures ideas EXACT PHRASING; detects entities and creates/enriches pages; logs one-line summary; back-links; citations.
**Our Status:** ❌ No equivalent
**Adaptation:** Create Hermes skill with triggers on every message. Spawn sub-agent for parallel execution. Capture to `originals/` for user ideas, `concepts/` for frameworks, trigger entity detection.
**Priority:** **CRITICAL** - Makes brain compound automatically

### brain-first
**Purpose:** Convention (not a skill). Mandatory lookup order: search → query → get_page before ANY external API. Score > 0.5 = use it.
**Our Status:** ❌ Not enforced
**Adaptation:** Document as Hermes convention. Add to Operation_Instructions.md. Create wrapper skill that validates brain-first before any web_search or external call.
**Priority:** **HIGH** - Prevents redundant external calls

---

## Category 2: Ingestion Pipelines

### ingest (Router)
**Purpose:** Routes content to specialized ingestion skills. Detects input type and delegates. Enforces filing rules, citations, back-links, raw source preservation.
**Our Status:** ❌ No router
**Adaptation:** Create router skill that dispatches to specific ingest skills below based on content type.
**Priority:** HIGH - Single entry point for all data

### idea-ingest
**Purpose:** Ingest links, articles, tweets, ideas. Fetch, analyze, author people page, cross-link. File by primary subject.
**Contract:** Every item has genuine analysis (not summary); author gets people page; bidirectional cross-links; raw source preserved; inline citations; filing by primary subject.
**Our Status:** ⚠️ Partial: Can fetch links but no brain storage/analysis
**Adaptation:** Implement with: fetch content → upload raw → search/create author people page → classify primary subject → write brain page with analysis → cross-link entities → sync.
**Priority:** HIGH - Most common user action: "read this / save this"

### meeting-ingestion
**Purpose:** Ingest meeting transcripts with attendee enrichment and entity propagation. Meeting NOT fully ingested until enrich runs for every entity.
**Contract:** Meeting page created; EVERY attendee gets people page (create/update); EVERY company discussed gets entity propagation; timeline entries on ALL mentioned entities; back-links bidirectionally; Entity propagation MANDATORY.
**Our Status:** ❌ No meeting ingestion
**Adaptation:** Full pipeline: parse transcript → create meeting page → enrich each attendee (create people pages) → propagate companies/concepts → add timeline entries to all entities → back-link → sync. Note: auto-link handles links, timeline-add still needs explicit calls.
**Priority:** HIGH - Meetings are high-signal sources

### media-ingest
**Purpose:** Ingest video, audio, PDF, book, screenshot, GitHub repo. Multi-format handling with entity extraction and backlink propagation.
**Contract:** Every media item has brain page with analysis (not raw dump); transcripts saved raw + human-readable; entity extraction every person/company gets back-linked; raw source preserved; filing by primary subject.
**Our Status:** ❌ No media ingestion (TTS only, no STT)
**Adaptation:** Build format handlers: YouTube → transcript, audio → STT, PDF → text extraction, screenshot → OCR + vision. Then same pattern: upload raw → create page by primary subject → extract entities → enrich → back-link → sync.
**Priority:** MEDIUM - Useful but not daily for most

### voice-note-ingest
**Purpose:** Ingest voice notes with EXACT PHRASING preservation (never paraphrase). Routes content based on decision tree.
**Iron Law:** User's exact words ARE the insight. Preserve verbatim in block quotes. Analysis can interpret; transcript is sacred.
**Our Status:** ⚠️ We have TTS but not STT ingestion
**Adaptation:** Add STT capability (Groq Whisper or OpenAI). Implement decision tree: original idea → originals/, concept → concepts/, person → people/ timeline, company → companies/ timeline, product idea → ideas/, reflection → personal/, else → voice-notes/. Upload raw audio, preserve transcript verbatim, add citation `[Source: voice note, channel, YYYY-MM-DD]`.
**Priority:** MEDIUM - Voice is convenient but less frequent

### archive-crawler
**Purpose:** Bulk ingest from archives (past emails, tweets, etc.). Deterministic collector pattern.
**Our Status:** ❌ No archive crawling
**Adaptation:** Build crawlers for common archives: Gmail/Outlook export, Twitter archive, Notion export, etc. Follow test-before-bulk convention (3-5 items first). Save raw, file by primary subject, enrich entities.
**Priority:** MEDIUM - One-time / occasional cold-start

---

## Category 3: Enrichment & Quality

### enrich
**Purpose:** Enrich brain pages with tiered enrichment protocol. Creates/updates person/company pages with compiled truth, timeline, cross-links.
**Contract:** Every enriched page has compiled truth + citations; timeline; back-links; tiered effort (Tier 1=full, Tier 2=medium, Tier 3=light); no stubs.
**Our Status:** ❌ No enrichment
**Adaptation:** Implement tiering based on notability. For a given entity: check brain state → if new create page (with notability gate) → external lookups (brain cross-ref first, then web research, social, APIs) → save raw data → write page with template → cross-reference related pages. Use templates from skill for person/company page structure.
**Priority:** HIGH - Makes entity pages valuable

### citation-fixer
**Purpose:** Audit and fix citation formatting across brain pages. Ensures every fact has inline [Source: ...] citation. v0.25.1: resolves tweet references without URLs via X API.
**Contract:** Scans all pages; identifies missing/malformed citations; fixes format; resolves tweet links; reports counts.
**Our Status:** ❌ No citation audit
**Adaptation:** Cron job: iterate pages → regex find facts without citations → flag; fix format to standard; for tweet patterns use X API integration to find URLs → patch. Save state in ~/.hermes/citation-fixer-state.json for incremental runs.
**Priority:** MEDIUM - Quality maintenance

### maintain
**Purpose:** Brain health checks: back-link enforcement, citation audit, filing validation, stale info detection, orphan pages, benchmarks.
**Provides:** `gbrain doctor` equivalent - one-command remediation with target score and cost cap.
**Our Status:** ❌ No health checks
**Adaptation:** Implement comprehensive health check covering: stale pages, orphans, dead links, missing cross-refs, back-link violations, citation gaps, filing violations, tag consistency, embedding staleness, security (RLS), schema, file storage, open threads. Add `doctor --remediation-plan` and `doctor --remediate` with dependency ordering and cost caps.
**Priority:** HIGH - System health monitoring

---

## Category 4: Querying & Retrieval

### query
**Purpose:** Hybrid search (keyword + semantic + RRF fusion + source-tier boost + reranker). Returns synthesized answers with citations.
**Our Status:** ❌ No hybrid search
**Adaptation:** Need vector DB (PGLite/pgvector). Implement hybrid: keyword (tsvector) + vector (embeddings) + RRF (Reciprocal Rank Fusion) + reranker. Expose via MCP tool `brain_query`.
**Priority:** **CRITICAL** - Core retrieval capability

### search
**Purpose:** Keyword search (fast, always works). Should be first step in lookup chain.
**Our Status:** ✅ Basic file search exists but not optimized
**Adaptation:** Implement tsvector-based full-text search over markdown files. Prefer this over grep for speed. Expose via MCP tool `brain_search`.
**Priority:** HIGH - Fast path for lookups

### get_page
**Purpose:** Direct page read by slug. Returns full page with compiled truth, timeline, links, source_id.
**Our Status:** ✅ We can read files
**Adaptation:** Wrap file reads with standardized format: frontmatter + content + structured metadata. Cache in memory for frequent access.
**Priority:** MEDIUM - Straightforward wrapper

---

## Category 5: Automation & Orchestration

### cron-scheduler
**Purpose:** Schedule management with staggering, quiet hours, wake-up override. Validates schedules, prevents collisions, gates delivery during quiet hours.
**Contract:** Max 1 job per 5-minute slot; quiet hours gating; thin job prompts; idempotency; reports saved.
**Our Status:** ✅ We have cronjob tool
**Adaptation:** Enhance our cronjob tool with: stagger validation (reject same-minute collisions), quiet hours check, idempotency key enforcement, output routing to held queue during quiet hours. Reference `skills/conventions/cron-via-minions.md` for execution pattern.
**Priority:** MEDIUM - Quality of life improvement

### minion-orchestrator
**Purpose:** Unified Minions skill for both deterministic shell jobs and LLM subagent orchestration. Durable, observable, steerable queue interface.
**Guarantees:** Jobs survive restarts; structured progress + token accounting; steerable via inbox messages; pause/resume/cancel; parent-child DAGs.
**Our Status:** ❌ No durable job queue (Hermes has subagent but not Minions)
**Adaptation:** For our system, we can use n8n workflows as the durable queue, or implement a simple Postgres-backed job table. Key insight: cron jobs should submit Minion jobs, not call agentTurn directly. For PGLite, use `--follow` inline execution.
**Priority:** HIGH - Enables reliable background processing

### RESOLVER
**Purpose:** The dispatcher. Skills are implementations. Resolver reads all skill files and decides which to invoke. Read before any task.
**Our Status:** ❌ No resolver (Hermes loads skills differently)
**Adaptation:** Implement skill dispatcher: given user query, scan all skill frontmatter triggers → select top match → load skill → invoke. Cache resolver decisions. Document as `skills/RESOLVER.md` in our system.
**Priority:** HIGH - Core routing mechanism

---

## Category 6: Synthesis & Pattern Detection

### concept-synthesis
**Purpose:** Deduplicate and synthesize raw concept stubs into tiered intellectual map (T1 Canon to T4 Riff), tracing idea evolution across sources over time.
**Architecture:** Phase 1 dedup (Jaccard + substring + semantic) → Phase 2 tier (frequency/timespan/breadth) → Phase 3 synthesize (LLM on T1/T2) → Phase 4 cluster + map.
**Our Status:** ❌ No synthesis
**Adaptation:** Implement as heavy cron job (weekly). Run on all concept pages: dedup → tier → synthesize top tiers → generate concepts/README.md intellectual map. Use same template structure.
**Priority:** MEDIUM - Long-term intellectual organization

### daily-task-prep
**Purpose:** Morning preparation. Calendar lookahead, meeting context loading, open threads from yesterday, active task review. Extends briefing with actionable prep.
**Contract:** Calendar/meetings loaded with brain context per attendee; open threads from yesterday surfaced; active tasks reviewed with priority; briefing actionable.
**Our Status:** ❌ No daily prep
**Adaptation:** Cron job each morning: load calendar → for each meeting, load attendee brain pages → check yesterday's timeline for unresolved threads → review active tasks → compile prep briefing with per-meeting context cards. Send via Telegram.
**Priority:** MEDIUM - Productivity enhancement

### briefing
**Purpose:** Compile daily briefing with meeting context, active deals, and citation tracking.
**Hot memory pulse (v0.32):** Before anything, run `gbrain recall --since-last-run --supersessions --pending --rollup --json` and fold into briefing. Shows contradictions resolved overnight, top mentions, new facts, pending consolidation.
**Our Status:** ✅ We have daily briefing but without brain integration
**Adaptation:** Enhance our briefing to: 1) run recall pulse (once we have recall), 2) query brain for meeting attendees, active deals, time-sensitive threads, recent changes, people in play, stale alerts. Every fact must include `[Source: slug, updated DATE]` citations.
**Priority:** HIGH - Most visible user-facing feature

---

## Category 7: Maintenance & Health

### maintain (already covered)
See Category 3.

### citation-fixer (already covered)
See Category 3.

### dream cycle (multiple skills)
**Purpose:** The nightly consolidation cycle. Not a single skill but an orchestration of multiple phases:
- lint → backlinks → sync → synthesize → extract → patterns → embed → orphans
**Phases:**
- **Synthesize:** reads transcripts, filters routine ops with cheap model, fans out subagent per transcript → writes reflections/originals/people timelines
- **Patterns:** reads recent reflections, surfaces recurring themes → pattern pages when ≥3 reflections support
- **Consolidate:** memory consolidation from ephemeral to durable
- **Embed:** re-embed stale pages
- **Fix citations:** audit and repair
**Our Status:** ❌ No dream cycle
**Adaptation:** Implement as cron job at 2 AM. Orchestrate phases sequentially: 1) entity sweep (run signal-detector on today's conversations), 2) citation fix, 3) consolidate (run concept-synthesis), 4) patterns detection, 5) embed stale pages, 6) backfill graph. Report results.
**Priority:** **CRITICAL** - The self-maintaining brain

---

## Category 8: Meta & Development

### skill-creator
**Purpose:** Create new skills from specifications. Meta-skill for skill development.
**Our Status:** ❌ No skill creation automation
**Adaptation:** Could be useful for rapid skill prototyping. Lower priority now.
**Priority:** LOW

### skill-optimizer
**Purpose:** Improve existing skills via evals. `improve my X skill` runs optimizer, reports diff + score delta.
**Our Status:** ❌ No skill optimization
**Adaptation:** When we have more skills, add eval harness and optimization loop. Requires skill-optimizer skill and evals infrastructure.
**Priority:** LOW - Mature system optimization

### testing
**Purpose:** Skill conformance tests, E2E lifecycle.
**Our Status:** ❌ No skill testing framework
**Adaptation:** For each skill we write, add conformance test checking frontmatter, trigger matching, output format. Use `test/skills-conformance.test.ts` pattern.
**Priority:** MEDIUM - Quality assurance

### migrations
**Purpose:** Schema evolution handling. Migration files for each version (v0.5.0 through v0.41.11.0).
**Our Status:** ❌ No schema migrations
**Adaptation:** When we evolve brain directory structure or frontmatter schema, version and provide migration scripts. Store in `skills/migrations/`.
**Priority:** LOW - Future-proofing

---

## Category 9: Integration Recipes

### email-to-brain
**Purpose:** Gmail messages flow into entity pages via deterministic collector.
**Our Status:** Can we read Gmail? Need to check credentials.
**Adaptation:** Build email collector (every 30 min). Parse emails → extract entities/sender → enrich people pages → meeting notes if applicable. Respect quiet hours. Save raw email.
**Priority:** MEDIUM - Email is common communication channel

### x-to-brain
**Purpose:** Twitter/X monitoring with deletion detection + engagement velocity.
**Our Status:** ❌ No Twitter integration
**Adaptation:** Build X collector (every 30 min). Watch handles → fetch tweets → create media pages → enrich mentioned people/companies. Detect deletions and mark accordingly.
**Priority:** LOW-MEDIUM - Depends on user's Twitter use

### calendar-to-brain
**Purpose:** Google Calendar events become searchable daily brain pages.
**Our Status:** Can we read Google Calendar? Check credentials.
**Adaptation:** Build calendar sync (daily). Fetch today's events → create meeting pages (even if no transcript) with attendee list → enrich attendees → add to daily briefing.
**Priority:** HIGH - Calendar is essential for context

### meeting-sync
**Purpose:** Circleback transcripts auto-import with attendee propagation.
**Our Status:** ❌ No meeting sync service
**Adaptation:** Integrate with meeting providers (Circleback, Grain, Otter). On transcript ready → trigger meeting-ingestion skill. Ensure attendees enriched.
**Priority:** HIGH - Automates meeting ingest

---

## Skills We Can Skip for Now

- `academic-verify` (specialized)
- `book-mirror` (book synthesis, niche)
- `cross-modal-review` (multimodal eval, advanced)
- `data-research` (heavy API usage)
- `eiirp` (proprietary integration)
- `functional-area-resolver` (internal routing)
- `gbrain-upgrade` (we're not running gbrain binary)
- `install` (we're not installing gbrain)
- `perplexity-research` (specific tool)
- `publish` (output generation, not core)
- `schema-author` / `schema-unify` (Schema-specific)
- `setup` (one-time)
- `smoke-test` (testing only)
- `soul-audit` (alignment check, periodic)
- `strategic-reading` (reading assistant)
- `voice-note-ingest` (we'll adapt but not use their exact implementation)
- `webhook-transforms` (specific webhook handling)
- `archive-crawler` (build our own if needed)

---

## Skill Development Cycle (Reference)

From `GBRAIN_SKILLPACK.md`:

1. **Concept** - Identify need, define contract, triggers, tools
2. **Prototype** - Build prompt, test on 3-5 items
3. **Evaluate** - Run benchmark queries, check quality
4. **Codify** - Write formal SKILL.md, add to skills/ directory
5. **Cron** - Schedule if recurring

Apply this cycle for each new skill we create.

---

## Next Steps

1. Start with **brain-ops** and **signal-detector** as foundational skills
2. Implement **brain-first** convention enforcement
3. Build ingestion router + idea-ingest + meeting-ingestion
4. Set up PGLite + hybrid search (query skill)
5. Create maintain/dream cycle
6. Add integrations: calendar-to-brain, email-to-brain as needed

See `04_IMPLEMENTATION_PLAN.md` for phased rollout.