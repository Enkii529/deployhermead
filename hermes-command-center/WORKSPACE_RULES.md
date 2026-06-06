# Workspace Rules - OpenClaw Command Center

## Workspace Location
All project files, logs, and configuration reside in:
~/openclaw-command-center

## Core Principles
1. **Direct & Practical** – Communicate clearly, avoid filler.
2. **Highest Priority First** – Focus on rebuilding OpenClaw, then business tasks.
3. **Beginner‑Friendly Documentation** – Keep notes understandable for new contributors.
4. **Safety First** – No destructive actions without explicit approval.
5. **Auditability** – Every risky or admin action must be logged before execution.
6. **Guided by Operation_Instructions.md** – All operations follow /home/openclaw/openclaw-command-center/user_preferences/Operation_Instructions.md, the top-level behavior guide.

## Permission Boundaries
- **Package Installation** – Requires prior user approval.
- **Docker Operations** – Requires approval; containers must be documented.
- **Port Exposure** – Approval needed before publishing any port.
- **File & Volume Deletion** – Must be approved; confirm target and backup if needed.
- **Service Modification** – Requires approval; include rationale and rollback plan.
- **Admin Actions** – Explain impact, affected directory, and reversal steps.

## Logging Requirements
- Every approved change is recorded in `SETUP_LOG.md`.
- Log format: `YYYY-MM-DD HH:MM EDT - Action - Details - Result`.
- Include command run, path changed, and any reversal info.

## Review & Approval Process
1. Propose the change.
2. Explain what it modifies (file, folder, service, etc.).
3. State risk level (low/medium/high).
4. Provide rollback instructions where applicable.
5. Wait for user confirmation before proceeding.

## Example Workflow
- **Task:** Rebuild OpenClaw core.
- **Step:** Edit `AGENTS.md` to add new service definitions.
- **Log Entry:** `2026-04-29 19:20 EDT - Updated - AGENTS.md - Added placeholder section for agent manifests - Success`.

---

*These rules are meant to keep the command center organized, safe, and traceable.*