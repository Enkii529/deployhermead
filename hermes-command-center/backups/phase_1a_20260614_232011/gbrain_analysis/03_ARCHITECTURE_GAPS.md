# 03_ARCHITECTURE_GAPS.md

Critical architectural components gbrain has that our Brain lacks.

---

## Gap 1: Vector Database + Hybrid Search

**What gbrain has:** PGLite (embedded SQLite + pgvector) or Postgres + pgvector extension. Enables:
- Hybrid search: keyword (tsvector) + vector (embeddings) + RRF (Reciprocal Rank Fusion) + reranker
- `gbrain query` returns semantic results
- `gbrain embed` generates and manages embeddings

**Our status:** Only basic file-based markdown storage. No vector search, no embeddings.

**What we need:**
1. **PGLite binary** (download from gbrain releases) OR Postgres + pgvector
2. **Embedding model** (OpenAI `text-embedding-3-small`, or local via Ollama `nomic-embed-text`)
3. **Chunker** to split pages into chunks for embedding
4. **Embedding index** that maps chunk vectors to markdown locations
5. **Hybrid search engine** that combines:
   - Keyword: PostgreSQL tsvector or sqlite FTS5
   - Vector: pgvector cosine similarity
   - RRF fusion: rank aggregation algorithm
   - Reranker: optional cross-encoder for top-K refinement

**Implementation approach:**
- Option A: Install PGLite binary, initialize brain DB, let gbrain CLI manage schema. Our Hermes skills call `gbrain` binary via MCP or subprocess.
- Option B: Build our own minimal vector store: use `chromadb` or `lance` in Python. Simpler but less integrated.
- Option C: Use Pinecone/Weaviate cloud (external dependency, cost)

**Recommended:** Option A - use gbrain's PGLite if possible. But gbrain is written in TypeScript/Bun. We may need to adapt the concepts rather than reuse code directly.

**Priority:** **CRITICAL** - Without hybrid search, brain is just a file system.

---

## Gap 2: Structured Graph Layer (Links + Timeline)

**What gbrain has:** Database tables `links` and `timeline_entries` structured graph.
- Links: typed edges (`attended`, `works_at`, `invested_in`, `founded`, `advises`, `mentions`, `source`) between entities
- Timeline entries: dated events associated with an entity, with source citation

**Our status:** We have markdown files only. No structured graph. Links are implicit via `[[wiki/people/name]]` wikilinks, but not extracted to queryable structure.

**What we need:**
1. **Extractor** that parses markdown files for:
   - Wikilinks `[[path]]` → create link relation
   - `[Name](people/slug)` style links
   - Timeline entries: lines matching `- **YYYY-MM-DD** | description [Source: ...]`
   - Frontmatter fields: `relationships`, `company`, etc.
2. **Database** (could be same PGLite) with `links` and `timeline_entries` tables
3. **Populate** command: `gbrain extract links --source db` and `gbrain extract timeline --source db`
4. **Query** tools: `gbrain get_backlinks`, `gbrain traverse_graph`, `gbrain graph-query`

**Implementation:**
- Write Python script that walks Brain/, parses markdown with frontmatter, regex for wikilinks and timeline entries, inserts into SQLite DB (or Postgres)
- Expose via Hermes tools: `brain_get_backlinks`, `brain_traverse_graph`
- Run periodically as cron job (after major imports)

**Priority:** **HIGH** - Enables graph queries and relationship navigation

---

## Gap 3: Auto-Linking Post-Hook

**What gbrain has:** Every `put_page` call automatically extracts entity references and writes them to the `links` table with inferred relationship types. Stale links (refs no longer in page) are removed automatically. Config `auto_link` (default on).

**Our status:** No automatic linking. Manual.

**What we need:**
- After each brain page write (via our skill), run link extraction on that page
- Compare with existing links for that page; add new ones; remove missing ones
- Periodically run full extraction for all pages

**Implementation:**
- In our `brain-ops` skill, after `put_page` call, invoke `extract_links_for_page(page_slug)` which:
  - Read page content
  - Find all entity references (wikilinks, markdown links to people/companies)
  - Determine relationship type (heuristic: if page is meeting and links to person → `attended`; if person page links to company → `works_at`; default `mentions`)
  - Upsert links to DB; delete links that are no longer present
- Also run `gbrain extract all --source db` equivalent as nightly cron

**Priority:** HIGH - Keeps graph in sync automatically

---

## Gap 4: Compiled Truth + Timeline Model

**What gbrain has per page:**
- **Compiled Truth** (above the line): synthesized understanding, current state, with inline citations. Rewritten on updates, not appended.
- **Timeline** (below the line): append-only chronological events with `[Source: ...]` citations. Reverse-chronological order.

**Our status:** Our markdown files lack enforced structure. Some have dates but no standardized format.

**What we need:**
1. **Page schema** (frontmatter fields):
   - `title`, `type` (person|company|concept|meeting|idea|original|media...), `created`, `updated`, `tags`, `source_id` (for multi-source brains)
   - For people: `company`, `relationship`, `email`, `twitter`, `linkedin`, `location`
   - For companies: optional fields
2. **Template enforcement** for each type (see enrich skill templates)
3. **Validation** on write: ensure timeline entries have dates and citations; compiled truth sections exist
4. **Rewrite semantics**: when updating a page, the "State" section should be REPLACED with current best understanding, not appended. Use LLM to synthesize if needed.

**Implementation:**
- Define templates in our skills (person.md.j2, company.md.j2, concept.md.j2)
- In `put_page` operation: read existing page, merge new timeline entries, rewrite compiled truth if signal warrants, preserve history
- Add validation tool that checks page structure

**Priority:** HIGH - Consistent data model is essential

---

## Gap 5: Source Attribution & Cross-Source Citations

**What gbrain has:** Multi-source brains (wiki, gstack, yc-media, etc.). Citations include source ID: `[wiki:topics/resilience]` or `[gstack:plans/retry-policy]`. Source precedence: User statements > Compiled truth > Timeline > External sources.

**Our status:** Single-source Brain. Citations are ad hoc if present.

**What we need:**
1. **Source registry**: map each brain subdirectory to a source ID (e.g., `people/` → source_id `brain`, or more granular: `meetings/` → `meetings`, `media/` → `media`)
2. **Citation format standard**: `[source_id:slug]` or `[Source: User, context, YYYY-MM-DD]`
3. **Cross-source linking**: when writing a fact from source A, cite the exact page slug with source prefix

**Priority:** MEDIUM - Adds clarity, useful if we have multiple data sources

---

## Gap 6: Notability Gate & Filing Rules

**What gbrain has:** `_brain-filing-rules.md` mandates:
- File by PRIMARY SUBJECT, not format or source
- Notability check before creating new entity pages
- Iron Law back-linking
- Raw source preservation via `gbrain files upload-raw` with size routing (<100MB git, >=100MB cloud)
- `sources/` only for bulk data imports, not raw ingest

**Our status:** Ad hoc filing. No notability check. No raw source preservation.

**What we need:**
1. **Filing decision tree** in every ingest skill:
   - Identify primary subject (person/company/concept/policy/...)
   - Route to appropriate directory
   - Cross-link to other relevant directories
2. **Notability gate function**:
   - People: Will we interact again? Relevant to work?
   - Companies: Relevant to work/interests?
   - Concepts: Reusable mental model worth referencing?
   - If uncertain, skip; can create later
3. **Raw source upload**:
   - For <100MB text: store in `.raw/` sidecar dir next to brain page
   - For >=100MB or media: upload to cloud storage (Supabase/S3) and create `.redirect.yaml` pointer
   - Include `sources:` frontmatter with storage info

**Implementation:** Create utilities `upload_raw(file, page_slug, type)` and `get_storage_url(path)`; integrate into ingest skills.

**Priority:** HIGH - Prevents brain pollution and maintains provenance

---

## Gap 7: MCP Tools Expose

**What gbrain has:** MCP server exposing tools:
- `gbrain_search`, `gbrain_query`, `gbrain_get_page`, `gbrain_put_page`
- `gbrain_add_timeline_entry`, `gbrain_add_link`
- `gbrain_sync`, `gbrain_embed`, `gbrain_doctor`
- `gbrain_jobs_submit`, `gbrain_jobs_list`, etc.

**Our status:** Hermes has MCP support but no brain-specific tools defined.

**What we need:**
1. **Define MCP tool schema** for our brain operations (could reuse gbrain's tool definitions if we implement the backend)
2. **Implement tool handlers** in Hermes that call our brain backend (file operations + DB queries)
3. **Register tools** in Hermes MCP server config

**Example tool spec:**
```json
{
  "name": "brain_search",
  "description": "Keyword search across brain pages",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "type": {"type": "string", "enum": ["person", "company", "concept", "meeting", "all"]},
      "limit": {"type": "number"}
    }
  }
}
```

**Priority:** HIGH - Enables agents to use brain tools

---

## Gap 8: Signal Detection Loop

**What gbrain has:** `signal-detector` skill fires on EVERY inbound message (parallel, non-blocking) to capture:
1. Original thinking (user's exact phrasing) → `originals/` or `concepts/`
2. Entity mentions → create/enrich people/companies

**Our status:** No ambient signal detection. Brain updates only when explicitly invoked.

**What we need:**
- In Hermes gateway, hook into message processing pipeline
- Spawn parallel subagent running `signal-detector` skill on each user message
- Ensure it never blocks main response (fire-and-forget with `notify_on_complete=false`)
- Log one-line summary to system_registry/signal_log.jsonl

**Implementation:**
- Modify Hermes gateway to call `delegate_task` with `signal-detector` on every message
- Or implement as always-on subagent in background that reads from a queue

**Priority:** **CRITICAL** - Makes brain compound continuously

---

## Gap 9: Dream Cycle Orchestration

**What gbrain has:** `gbrain dream` command runs 8-phase cycle:
1. lint (schemalint? type-check)
2. backlinks (enforce iron law)
3. sync (files → DB)
4. synthesize (process transcripts → reflections/originals)
5. extract (links + timeline from markdown)
6. patterns (cluster recent reflections into themes)
7. embed (refresh embeddings)
8. orphans (detect and report)

**Our status:** No orchestrated maintenance cycle.

**What we need:**
- Cron job at 2 AM that runs phases sequentially
- Each phase as a separate Hermes skill (`maintain-lint`, `maintain-backlinks`, `brain-sync`, `brain-synthesize`, `brain-extract`, `brain-patterns`, `brain-embed`, `brain-orphans`)
- Dependency ordering: sync before extract, extract before embed, embed before synthesize? Check gbrain order
- Report generation after completion
- Cooldown and error handling

**Priority:** **CRITICAL** - Self-maintaining system

---

## Gap 10: Token & Cost Tracking

**What gbrain has:** All jobs track `tokens_input`, `tokens_output`, `tokens_cache_read`. Child tokens roll up to parent. `gbrain doctor --remediate` estimates `est_usd_cost` per step and respects `--max-usd` cap.

**Our status:** Hermes has token accounting but not per-job cost tracking integrated with brain maintenance.

**What we need:**
- In job execution, accumulate token counts from all LLM calls
- Store in job record: `tokens_in`, `tokens_out`, `estimated_cost_usd`
- For multi-phase jobs, break down cost per phase
- Enforce cost caps for automated jobs (dream cycle should have max $X per night)

**Implementation:**
- Extend Hermes cron execution to capture token usage from subagent runs
- Store in `system_registry/cron_executions.jsonl` with fields: `job_id`, `timestamp`, `tokens_in`, `tokens_out`, `cost_usd`, `duration_s`, `status`
- Add cost estimation function based on model pricing
- For maintain/dream, check total cost against cap before starting

**Priority:** MEDIUM - Prevent runaway costs

---

## Gap 11: Health Score & Automated Remediation

**What gbrain has:** `gbrain doctor` returns health score (0-100) across dimensions. `gbrain doctor --remediate --target-score 90 --max-usd 5` walks dependency-ordered fixes, re-checking score between steps, refusing to exceed cost cap.

**Our status:** No health scoring.

**What we need:**
- Define health dimensions (same as maintain skill): stale%, orphan%, dead_links%, backlink_violations%, citation_gaps%, filing_violations%, tag_consistency%, embedding_staleness%, security_status, schema_version, file_storage_health, open_threads_count
- Weight and combine into total score (0-100)
- Automated remediation: for each dimension, have a fix skill that can be invoked automatically
- Dependency ordering: sync before extract, embed after consolidate, etc.
- Cost estimation per fix

**Implementation:**
- Create `brain_health_check` Hermes skill that returns JSON with dimension scores and overall
- Create fix skills: `fix_backlinks`, `fix_citations`, `fix_dead_links`, `extract_links`, `extract_timeline`, etc.
- Create orchestrator skill: `doctor_remediate` that plans, executes, re-checks
- Store health history in `system_registry/brain_health_history.jsonl`

**Priority:** HIGH - Automated maintenance

---

## Gap 12: Raw Source Preservation & Size Routing

**What gbrain has:** `gbrain files upload-raw` with automatic size routing:
- <100 MB text/PDF: stays in git (brain repo `.raw/` sidecar)
- >=100 MB or media (video, audio, images): upload to cloud storage (Supabase/S3) via TUS resumable upload, leave `.redirect.yaml` pointer
- Pointer format includes `target`, `bucket`, `storage_path`, `size`, `hash`, `mime`, `uploaded`, `type`

**Our status:** We could save files locally but no size-based routing, no cloud upload, no pointer system.

**What we need:**
- Storage backend abstraction: local filesystem vs cloud (Supabase Storage, S3, Azure Blob)
- Upload service with resumable TUS protocol for large files
- `.redirect.yaml` format and resolver
- `put_raw_data` for JSON metadata (saved in DB or separate file)
- `gbrain files signed-url` equivalent for sharing
- `gbrain files restore` to download back from cloud

**Implementation:**
- Python module `brain_storage.py` with `upload_raw(path, page_slug, type) -> storage_info`
- For local: copy to `.raw/` next to page (e.g., `people/slug.md.raw/` or `sources/.raw/`)
- For cloud: implement TUS upload or simple multipart; create pointer YAML in brain repo
- Add config `storage.backend` = `local` or `supabase` with credentials

**Priority:** MEDIUM - Important for provenance but can start with local-only

---

## Gap 13: Convention Enforcement

**What gbrain has:** Convention files (`brain-first.md`, `quality.md`, `_brain-filing-rules.md`) plus doctor checks that flag violations. Skills can declare `brain_first: exempt` if truly exempt.

**Our status:** Conventions exist in memory but not enforced automatically.

**What we need:**
- Linter that runs on skill development and on brain pages
- Checks:
  - Skills: Does this skill call external APIs without brain-first lookup? Flag.
  - Brain pages: Missing citations? Flag. Missing backlinks? Flag. Stale compiled truth? Flag. Misfiled? Flag.
- CI integration: fail builds if violations
- `doctor` command that aggregates all checks

**Implementation:**
- `hermes brain lint` command that runs all checks
- Pre-commit hook that lints changed pages
- In skill loading, parse frontmatter and verify `brain_first` compliance

**Priority:** MEDIUM - Quality gate

---

## Gap 14: Two-Repo Architecture

**What gbrain has:** Agent repo (skills, CLI, code) separate from brain repo (markdown content). Clear boundary rules.

**Our status:** Currently using single Brain repository at `/media/sf_ClawdbotShared/Brain` which contains both: skills are in `Skills/` (capital S) and content in various folders. Not clean separation.

**What we need (optionally):**
- Decide if we want to separate agent code from brain content.
- gbrain pattern: agent repo = `~/hermes` (or a fork), brain repo = `~/brain` (pure markdown + .raw/ + .redirect.yaml files)
- Agent repo contains skills, CLI, tests, integration recipes
- Brain repo contains only knowledge content and raw source pointers

**Our adaptation:** Could adopt this pattern. Move all skills out of Brain/Skills into a dedicated `~/hermes-command-center/skills/` and keep Brain as pure content repo. This aligns with our current structure already: Brain is content, Hermes-command-center is code.

**Priority:** LOW - Our current split is fine; just formalize boundary

---

## Gap 15: Cold Start & migrations

**What gbrain has:** `cold-start` skill sequences highest-leverage data sources: contacts, calendar, email, conversations, social, archives. Uses ClawVisor for safe credential handling. Migration files for schema evolution.

**Our status:** No cold-start process. Brain grows organically.

**What we need:**
- Cold-start skill that:
  1. Checks for existing brain pages (skip if already populated)
  2. Asks user which sources to import (ask-user skill for choices)
  3. Runs integrations in order: contacts → calendar → email → meetings → social → archives
  4. Saves progress checkpoint
  5. Generates cold-start report

- Migration system: When we change directory structure or frontmatter schema, write migration scripts that transform existing files. Track version in `brain/.meta/version`. Run migrations on startup if version outdated.

**Priority:** LOW-MEDIUM - Useful for new installations, not urgent for our ongoing Brain

---

## Gap 16: Session Continuity & Open Threads

**What gbrain has:** `open_threads` detection: timeline items older than 30 days with unresolved action items. Open threads surface in daily briefing and maintenance.

**Our status:** No structured tracking of open threads.

**What we need:**
- Define "open thread": a timeline entry with an action item that is not marked done/closed
- Extract from all pages: look for `- [ ]` unchecked items, or phrases like "follow up", "pending", "waiting on"
- Store in `system_registry/open_threads.json` with fields: `entity_slug`, `date`, `description`, `due_date`, `status`
- Update when action completed (either manually or by signal detector if user mentions resolution)
- Include in daily briefing and prep

**Implementation:**
- Script that scans timeline entries with TODO keywords
- Or explicit metadata in timeline: `{status: open, type: followup, due: YYYY-MM-DD}`
- Could use dedicated `open_threads/` directory for one-page-per-thread tracking

**Priority:** MEDIUM - Action item tracking is valuable

---

## Summary of Priorities

### Must Have (Foundation)
1. Vector DB + hybrid search (Gap 1)
2. MCP tools expose (Gap 7)
3. Signal detection loop (Gap 8)
4. Compiled truth + timeline model (Gap 4)
5. Graph layer (links + timeline tables) (Gap 2)

### High Priority (Core Value)
6. Auto-linking post-hook (Gap 3)
7. Ingestion skills (idea, meeting, media) — need filing rules (Gap 6)
8. Enrich skill (tiered)
9. Dream cycle orchestration (Gap 9)
10. Health score + remediation (Gap 11)
11. Maintain skill
12. Briefing enhancement with brain pulse

### Medium Priority (Polish)
13. Cron job infrastructure improvements (quiet hours, idempotency, minions pattern)
14. Token/cost tracking (Gap 10)
15. Raw source preservation (Gap 12)
16. Convention enforcement (Gap 13)
17. Citation fixer
18. Concept synthesis
19. Integration recipes (email, calendar, x)

### Low Priority (Nice-to-have)
20. Cold start
21. Two-repo formalization (already okay)
22. Skill optimizer, soul audit, etc.

---

## Architecture Decision Records (ADRs) Needed

- ADR-001: Choose vector DB (PGLite vs Chroma vs Lance)
- ADR-002: Separate brain content repo vs monolithic (likely keep as-is)
- ADR-003: MCP vs direct tool calls (MCP for agent access, direct for Hermes internal)
- ADR-004: Storage backend (local-only vs Supabase cloud for large files)
- ADR-005: Graph DB vs relational (use same PGLite/Postgres)

---

## Next Steps (Immediate)

1. Set up PGLite binary in our environment (test gbrain CLI directly)
2. Draft Hermes skill for `brain_search` / `brain_query` (simple wrapper around PGLite full-text search first)
3. Implement markdown page schema validation (frontmatter + content structure)
4. Build link/timeline extractor as Python script
5. Create basic maintain skill with health check dimensions
6. Build signal-detector skeleton that logs to `system_registry/signals.jsonl`

See `04_IMPLEMENTATION_PLAN.md` for phased rollout.