# OC_TOOL_NOTE

## Enki Browser 2 – Active Browser‑Control Tool

Enki Browser 2 is the default browser‑control tool for the OpenClaw command‑center.  
It is used for any back‑end automation, UI testing, or browser inspection tasks.

**Key facts:**
- Installed at `/home/openclaw/openclaw-command-center/tools/enki-browser-2`
- Service listens on **port 4318** (base URL `http://127.0.0.1:4318`)
- CLI wrapper: `/home/openclaw/openclaw-command-center/tools/enki-browser-2/enki`
- Persistent profile: `data/profile`
- Run artifacts stored in `runs/`

**Recovered MVP:**  
The older Enkii Browser MVP is preserved at `/home/openclaw/openclaw-command-center/tools/enki-browser-recovered` and should be used **only as a reference**. Do not use it for active automation.

**When to use Enki Browser 2:**
- Navigating pages, taking screenshots, extracting visible text or DOM summaries.
- Capturing console messages, page errors, or failed network requests.
- Performing click, fill, or key‑press actions on a page.
- Running structured browser tasks with artifact logging.

**Safety notes:**
- Do not kill the MVP on port 4317 unless explicitly approved.
- Do not use personal browser profiles.
- Do not expose arbitrary shell execution through the Enki endpoints.
- Do not delete run artifacts unless explicitly approved for cleanup.
