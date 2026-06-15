# 05_QUICK_WINS.md

High-impact, low-effort changes we can implement THIS WEEK.

---

## 1. Add Brain-First Convention to Operation_Instructions.md (1 hour)

**Change:** Add section:

```markdown
## Brain-First Lookup (MANDATORY)

Before making ANY external API call (web_search, database lookup, etc.), the agent MUST:
1. Check the Brain first using `brain_search` or `brain_query`
2. Only if the Brain lacks the information, proceed to external sources

This prevents redundant external calls and ensures the Brain compounds.
```

**Impact:** Establishes core discipline. Zero cost.

---

## 2. Implement `brain_search` as ripgrep wrapper (2 hours)

**Code:** New Hermes tool in `~/hermes/tools/brain_search.py`:

```python
import subprocess, json, os
def brain_search(query: str, limit: int = 10):
    # Use rg to search Brain/ for query
    cmd = ["rg", "--json", "--max-count", str(limit), query, "/media/sf_ClawdbotShared/Brain"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Parse rg JSON output to return {matches: [{file, line, ...}]}
    # Return top K results
    return {"matches": parsed}
```

Register in Hermes MCP server: `tools/brain_search`.

**Impact:** Fast keyword search available to all agents. Foundation for brain-first.

---

## 3. Create `originals/` and `concepts/` directories (5 min)

```bash
mkdir -p /media/sf_ClawdbotShared/Brain/originals
mkdir -p /media/sf_ClawdbotShared/Brain/concepts
```

Add to `_brain-filing-rules.md` (create that file with minimal rules):

```markdown
# Brain Filing Rules (Draft)

- `originals/`: the user's original thinking, ideas, theses, frameworks. Exact phrasing, verbatim.
- `concepts/`: reusable mental models, frameworks (not necessarily original to the user).
- `people/`: person pages (existing)
- `companies/`: company pages (existing)
- `meetings/`: meeting pages (existing)
- `media/`: content ingested from external sources (articles, videos, podcasts)
- `sources/`: ONLY for raw data dumps (API exports, CSVs). Not for regular ingest.
```

**Impact:** Provides destinations for signal-detector output.

---

## 4. Draft `signal-detector` skill as simple HTML-trigger (after tool above)

We can't run on every message yet (requires gateway hook), but we can create the skill file and invoke manually or via `/brain capture` command.

Create `~/hermes/skills/brain/signal-detector/SKILL.md` with:

- Triggers: `"capture signals"`, `"what did I just say"`
- Tools: `brain_search`, `write_file` (to originals/ or concepts/)
- Mutating: true

Initially implement as: when user says "capture that", agent reads last N messages from session, finds original thinking and entities, writes pages.

**Impact:** Proto-signal capture; will become always-on later.

---

## 5. Add `brain_get_page` tool (1 hour)

Wrapper around `read_file` that returns frontmatter + body.

```python
def brain_get_page(slug: str):
    path = f"/media/sf_ClawdbotShared/Brain/{slug}.md"
    content = read_file(path)
    # Parse frontmatter (YAML between --- lines)
    # Return {"frontmatter": dict, "body": str}
```

Register as MCP tool.

**Impact:** Agents can read brain pages easily.

---

## 6. Add `brain_put_page` with auto-link (3 hours)

Write tool that:
- Takes `slug`, `content`, optional `frontmatter` dict
- Writes to `{slug}.md` with atomic replace (write to temp then mv)
- After write, calls `brain_extract_links_for_page(slug)` to update links index
- Returns `{auto_links: {created: [...], removed: [...]}}`

**Impact:** Writes keep graph in sync automatically.

---

## 7. Create `brain_extract_links` utility (2 hours)

Python script that:
- Reads markdown file
- Regex finds `[[path]]` and `[text](path)` where path starts with `people/`, `companies/`, `concepts/`
- For each found, determine relationship type (heuristic)
- Append to `brain_data/links.jsonl`

Can be called standalone or as post-hook.

**Impact:** Populates graph index incrementally.

---

## 8. Set up basic `brain_extract` cron (weekly) (30 min)

In Hermes cron:

```json
{
  "schedule": "0 6 * * 1",
  "prompt": "Extract links and timeline from all brain pages to keep graph current. Run: python3 ~/hermes/scripts/brain_extract_all.py. Save report to system_registry/extract-YYYY-MM-DD.md.",
  "deliver": "local"
}
```

Script runs both extractors.

**Impact:** Graph stays up-to-date.

---

## 9. Enable `signal-detector` as always-on subagent (4 hours)

Modify Hermes gateway (`gateway.py` or message processor) to:
- On every user message, spawn subagent with `signal-detector` skill
- Use `delegate_task(..., notify_on_complete=False)`
- Subagent uses `brain_search` + `brain_put_page` to capture ideas and entities

Test with a few sessions to ensure no blocking and proper logging.

**Impact:** Brain starts compounding automatically. This is the single most valuable quick win because it makes the brain self-building.

---

## 10. Implement `brain_query` prototype with ChromaDB (8 hours)

Set up ChromaDB in `~/brain/.chroma/`. Write embedding script:

```python
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="~/brain/.chroma")
collection = client.get_or_create_collection("pages")

def embed_page(slug):
    content = read_brain_page(slug)
    chunks = chunk(content, size=500, overlap=50)
    embeddings = model.encode(chunks)
    # Upsert chunks with metadata {slug, chunk_index}
```

Then implement `brain_query(query)`:
- Embed query
- Search collection for top-50 chunks
- Aggregate scores by page (max chunk score per page)
- Return top-10 pages

Test with sample queries.

**Impact:** Hybrid search (vector) dramatically improves recall for semantic queries.

---

## 11. Add citation format check to `maintain` skill (2 hours)

In maintain's citation audit phase:
- For each timeline entry, verify it ends with `[Source: ...]` citation.
- Count violations.
- Optionally fix by inserting placeholder `[Source: TODO]` or flag for manual review.
- Also check for tweet patterns without x.com URLs.

**Impact:** Improves data quality gradually.

---

## 12. Create health dashboard widget (3 hours)

Modify Command Center Panel Flask app (`command_center_panel/app.py`) to add `/brain-health` endpoint that:
- Runs `maintain` in dry-run mode to get dimension counts
- Returns JSON: `{score: 72, dimensions: {stale: 2, orphans: 5, ...}}`
- Display on dashboard UI.

**Impact:** Visibility into brain health; motivates maintenance.

---

## Quick Wins Summary Table

| # | Task | Effort | Impact | Dependencies |
|---|------|--------|--------|--------------|
| 1 | Add brain-first to docs | 1h | High | None |
| 2 | brain_search tool (rg) | 2h | High | None |
| 3 | Create originals/, concepts/ | 5m | High | None |
| 4 | Draft filing rules | 1h | High | None |
| 5 | brain_get_page tool | 1h | High | #2 |
| 6 | brain_put_page + auto-link | 3h | High | #5, #7 |
| 7 | brain_extract_links utility | 2h | High | None |
| 8 | Weekly extract cron | 30m | Medium | #7 |
| 9 | Always-on signal-detector | 4h | **Critical** | #2, #5, #6 |
|10 | ChromaDB prototype | 8h | High | None |
|11 | Citation audit in maintain | 2h | Medium | #5 |
|12 | Health dashboard widget | 3h | Medium | #11 |

**Total effort:** ~33 hours (1 week full-time, or 2-3 weeks part-time).

**Start with #2 and #3 immediately** - they enable everything else.

---

## Immediate Next Action

1. Create `originals/` and `concepts/` directories now.
2. Write minimal `_brain-filing-rules.md` (copy from gbrain, adapt).
3. Implement `brain_search` tool this afternoon.
4. Test: from Python REPL, call `brain_search("test")` and see results.
5. Commit to git and push.

Then proceed to #5 and #6 to get write capability.

Once we can write pages, turn on signal-detector as always-on.

---

## Risk: Over-engineering

Quick wins are deliberately small and reversible:
- Directories can be removed if unwanted (just move files)
- Tools are additive, don't modify existing Brain content
- Signal-detector can be disabled by removing gateway hook
- ChromaDB is optional; we can fall back to rg-only search

Start small, validate, then build out.

---

## Expected Outcome After 1 Week

- `brain_search` and `brain_get_page` available to all agents
- Signal-detector running on every message; originals/ and entities growing daily
- Auto-links being created (check backlinks on people pages)
- Graph extraction starting weekly
- Health dashboard showing page count, link count, last run times

**This alone makes the Brain significantly more valuable** - it's now capturing the user's original thinking automatically and maintaining cross-references.

---

## Why These Are "Quick Wins"

- They reuse existing patterns (Hermes tools, cronjobs)
- Minimal new dependencies (just `ripgrep` which we already have, optional ChromaDB)
- No database migrations or complex setup
- Immediate visible feedback: new pages appear, links form
- Low risk: additive, can be rolled back by disabling
- High learning: we'll discover real-world challenges early (filing decisions, duplicate detection, signal quality)

Implement in order. Stop after each to validate. Adjust based on what we learn.

---

## Quick Wins Checklist

- [ ] Directories created (`originals/`, `concepts/`)
- [ ] `_brain-filing-rules.md` in Brain root
- [ ] `brain_search` tool implemented and registered
- [ ] `brain_get_page` tool implemented and registered
- [ ] Test call `brain_search("anything")` returns results
- [ ] `brain_put_page` tool implemented
- [ ] `brain_extract_links` script working
- [ ] Test write a page: `brain_put_page("test-page", "# Test\ncontent", {"type":"concept"})` succeeds
- [ ] Verify auto-link created if page references `[[wiki/people/xyz]]`
- [ ] Gateway hook for signal-detector added
- [ ] Send test message with idea + person → pages created
- [ ] Weekly extract cron job scheduled
- [ ] ChromaDB installed and indexing 100 pages
- [ ] `brain_query` returns hybrid results
- [ ] Maintain citation audit runs without error
- [ ] Command Center Panel shows brain health widget

---

**Let's start now.** Drop everything and do items #1-3 in the next hour.