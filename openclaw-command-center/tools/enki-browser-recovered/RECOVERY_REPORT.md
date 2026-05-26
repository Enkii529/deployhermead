# Enkii Browser Service MVP — Recovery Report

**Report Date:** 2026-05-03  
**Destination:** /home/openclaw/openclaw-command-center/tools/enki-browser-recovered

---

## 1. Source Backup Path
```
/media/sf_ClawdbotShared/Backups/vm-enkii/enkii_vm_workspace_20260210_204730Z/clawd/enkii-browser-service
```

## 2. Recovered Destination
```
/home/openclaw/openclaw-command-center/tools/enki-browser-recovered
```

## 3. Files Copied
- `package.json`
- `package-lock.json`
- `src/server.js`
- `config/known_good_domains.json`
- `data/audit.log.jsonl` — **not copied** (file was not present in source at copy time; audit log is generated at runtime)

## 4. Dependency Results
- **npm install** — completed successfully; all dependencies installed to `node_modules/`.
- **npx playwright install chromium** — completed successfully; Playwright browser binaries installed.
- **Playwright browser cache path** — `/home/openclaw/.cache/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-linux64/`

## 5. Service Status
- **Port used:** 4317
- **PID (at time of report):** 30381
- **Start command:** `cd /home/openclaw/openclaw-command-center/tools/enki-browser-recovered && node src/server.js > /tmp/enki-server.log 2>&1 &`
- **Port conflict on restart:** Yes — previous service instance was still running on port 4317; required `pkill` to stop it before restarting.

## 6. Smoke Test Results
- **GET /health** — HTTP 200, response: `{"ok":true}`
- **POST /navigate** (to https://example.com) — HTTP 200, response: `{"ok":true,"url":"https://example.com/"}`
- **POST /content** — HTTP 200, response: `{"ok":true,"url":"https://example.com/","html":"<!DOCTYPE html>..."}`
- **POST /screenshot** — HTTP 200, PNG image returned, size 18964 bytes, dimensions 1280×720, format PNG/RGB/non-interlaced

## 7. Domain Approval Result
- **First navigation blocked?** No — `example.com` is covered by the known-good / base-domain logic in the MVP, so it was auto-approved (no explicit approval step required).
- **Domain added to allowed_domains.json?** No — not required for example.com.
- **Path to allowed_domains.json:** `data/allowed_domains.json` (created at runtime if/when manual approvals are added).

## 8. Final Verdict
- **Recovered MVP works** — health, navigation, content retrieval, and screenshot endpoints all function after Playwright browser installation.
- **Recovered MVP should remain untouched** — do not modify the recovered project; preserve it as-is for reference and reproducibility.
- **Enki Browser 2 should be created separately** — new development should occur in a separate codebase:
  ```
  /home/openclaw/openclaw-command-center/tools/enki-browser-2
  ```

## 9. Known Limitations of Recovered MVP
- No click/fill/press endpoints (only goto/content/screenshot).
- No visible-text extraction endpoint.
- No DOM summary endpoint.
- No console/page error capture endpoint.
- No failed network request capture endpoint.
- No structured per-run folders (artifacts/log aggregation).
- Domain approval gate restricts unknown sites unless explicitly approved via `/approvals/allow`.

---