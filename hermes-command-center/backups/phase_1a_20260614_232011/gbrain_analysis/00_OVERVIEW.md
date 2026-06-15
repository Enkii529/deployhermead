# Gbrain → Our Brain: Comprehensive Mapping Worksheet

**Generated:** 2026-06-14
**Source:** garrytan/gbrain (cloned at /home/openclaw/gbrain)
**Target:** Our Brain at /media/sf_ClawdbotShared/Brain

---

## Executive Summary

Gbrain is a production-grade AI agent memory system with:
- **43 curated skills** (markdown workflows)
- **66+ cron jobs** running autonomously
- **Hybrid search** (keyword + vector + RRF + reranker)
- **MCP layer** exposing `gbrain search`, `gbrain get`, `gbrain query`
- **Dream cycle** (nightly consolidation, enrichment, citation repair)
- **PGLite** (embedded SQLite + pgvector, 2-sec startup, no server)
- **Minions** (Postgres-native job queue for durable background work)
- **Thin Harness / Fat Skills** architecture

Our Brain already has:
- ✅ Markdown storage at `/media/sf_ClawdbotShared/Brain`
- ✅ Wiki folder, docs, active_projects, system_registry
- ✅ Inter-agent file protocol (Bot_Exchange, inter_agent_tasks)
- ✅ Command Center Panel (Flask on 8787)
- ✅ n8n for workflow automation
- ✅ Hermes skills system
- ❌ Hybrid search / vector embeddings
- ❌ Dream cycle / autonomous consolidation
- ❌ Entity enrichment pipeline
- ❌ Citation audit / auto-linking
- ❌ Knowledge graph (structured links/timeline)
- ❌ MCP tools for brain access
- ❌ PGLite / pgvector backend

---

## File Structure

```
gbrain_analysis/
├── 00_OVERVIEW.md              # This file
├── 01_SKILLS_MAPPING.md        # All 43 skills mapped to our needs
├── 02_CRON_JOBS_MAPPING.md     # All cron jobs mapped to our needs
├── 03_ARCHITECTURE_GAPS.md     # What we're missing architecturally
├── 04_IMPLEMENTATION_PLAN.md   # Phase-by-phase adoption plan
├── 05_QUICK_WINS.md            # Things we can do today
├── 06_SKILL_ADAPTATIONS.md     # Specific skill modifications for our system
└── 07_INTEGRATION_POINTS.md    # How to wire into our existing infra
```