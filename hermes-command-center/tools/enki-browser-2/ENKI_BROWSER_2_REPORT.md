# Enki Browser 2 – Implementation Report

**CLI Wrapper integration:** A lightweight `enki` script has been added to `/home/openclaw/openclaw-command-center/tools/enki-browser-2/enki` for convenient CLI access from the OC command‑center workflow.

**Date:** 2026-05-03  
**Version:** 1.0.0  
**Service Path:** `/home/openclaw/openclaw-command-center/tools/enki-browser-2`

---

## 1. Preserved Recovered Version
The recovered Enki Browser MVP (Enki Browser 1) remains **untouched** at:
```
/home/openclaw/openclaw-command-center/tools/enki-browser-recovered
```

## 2. Created Enki Browser 2
Enki Browser 2 was created fresh at:
```
/home/openclaw/openclaw-command-center/tools/enki-browser-2
```

## 3. Key Files Created

| File | Purpose |
|------|---------|
| `package.json` | Node.js project manifest (CommonJS, Express + Playwright) |
| `server.js` | Main Express + Playwright server implementation |
| `README.md` | Documentation (setup, endpoints, examples) |
| `ENKI_BROWSER_2_REPORT.md` | This report |
| `data/profile/` | Chromium persistent profile folder |
| `data/allowed_domains.json` | Approved domains list (empty by default) |
| `data/audit.log.jsonl` | Audit log (created at runtime) |
| `config/known_good_domains.json` | Known-good domains baseline |
| `runs/` | Timestamped run folders for task artifacts |

## 4. Architecture Summary

| Component | Implementation |
|-----------|----------------|
| Runtime | Node.js (CommonJS) |
| HTTP API | Express |
| Browser Automation | Playwright (chromium) |
| Profile | Persistent context at `data/profile` |
| Runs | `runs/` folder with timestamped run IDs |
| Open Mode | `ENKI_OPEN_MODE=true` (default) |
| Approval Gate | Available when `ENKI_OPEN_MODE=false` |

## 5. Endpoint Status

| Endpoint | Implemented | Notes |
|----------|-------------|-------|
| GET /health | ✅ | Returns ok, pid, port, openMode, paths |
| GET /policy | ✅ | Returns openMode, knownGoodCount, allowedCount, pendingCount |
| POST /navigate | ✅ | Navigates to URL (with domain check) |
| POST /open | ✅ | Alias for navigate |
| POST /screenshot | ✅ | Returns PNG |
| POST /screenshot/save | ✅ | Saves to run folder |
| GET /content | ✅ | Returns page HTML |
| GET /visible-text | ✅ | Returns text + saves to run folder |
| GET /dom-summary | ✅ | Returns summary + saves to run folder |
| GET /console | ✅ | Returns captured console events |
| GET /network-failures | ✅ | Returns failed network requests |
| POST /click | ✅ | Click by selector |
| POST /fill | ✅ | Fill input by selector |
| POST /press | ✅ | Press key on page |
| POST /run | ✅ | Execute structured task with artifacts |
| GET /runs | ✅ | List run folders |
| GET /runs/:id | ✅ | Inspect run and list files |

## 6. Logging Artifacts (Smoke Test Run)

**Run folder:** `/home/openclaw/openclaw-command-center/tools/enki-browser-2/runs/2026-05-03T21-57-44Z`

**Files generated:**
- `metadata.json` — run metadata
- `screenshot.png` — page screenshot
- `visible-text.txt` — visible text
- `dom-summary.json` — DOM summary
- `console.json` — console events (empty array)
- `network-failures.json` — failed requests (empty array)
- `run.json` — task input + results

## 7. Smoke Test Result

| Step | Command | Result |
|------|---------|--------|
| 1 | `GET /health` | ✅ 200 OK |
| 2 | `POST /navigate` → https://example.com | ✅ 200 OK |
| 3 | `GET /visible-text` | ✅ 200 OK |
| 4 | `GET /dom-summary` | ✅ 200 OK |
| 5 | `GET /console` | ✅ 200 OK (empty) |
| 6 | `GET /network-failures` | ✅ 200 OK (empty) |
| 7 | `POST /screenshot/save` | ✅ 200 OK, file saved |

**Port used:** 4318  
**ENKI_OPEN_MODE:** `true`  
**Console errors found:** None  
**Failed network requests:** None  

## 8. How to Run It

```bash
cd /home/openclaw/openclaw-command-center/tools/enki-browser-2
npm install
npx playwright install chromium
ENKI_OPEN_MODE=true PORT=4318 node server.js
```

PID is written to `.server.pid`.  
To stop: `kill $(cat .server.pid)`

## 9. Known Limitations

1. **Click/Fill/Press** are selector-only — no text/role-based fallback yet.  
2. **Run artifacts** are written lazily; some files may be missing until after their triggering endpoint is called.  
3. **Console/network logs** accumulate in memory and are flushed to disk on request.  
4. **Approval-gate mode** is implemented but not exercised during smoke test (open mode was `true`).  
5. No automatic browser/profile cleanup; manual intervention required for stale data.

## 10. Next Steps (Optional Enhancements)

- Add text/role-based click/fill/press support.  
- Add automatic run folder creation at service start or on `/run` invocation.  
- Add `/approvals/pending` and `/approvals/allow` endpoints for gated mode workflow.  
- Add `--with-deps` flag handling in install scripts.  
- Add health-check endpoint with deeper browser state verification.

---

**Build completed successfully.**  
Enki Browser 2 is ready for AI/backend browser automation tasks.