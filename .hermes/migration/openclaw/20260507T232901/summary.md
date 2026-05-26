# OpenClaw -> Hermes Migration Report

- Timestamp: 20260507T232901
- Mode: execute
- Source: `/home/openclaw/.openclaw`
- Target: `/home/openclaw/.hermes`

## Summary

- migrated: 4
- archived: 3
- skipped: 33
- conflict: 2
- error: 0

## Warnings

- Conflicts were found. Re-run with --overwrite to replace conflicting targets after item-level backups.
- A config.yaml write hit a conflict or error mid-apply; later config items were skipped to avoid a partial write.

## What Was Not Fully Brought Over

- `/home/openclaw/.openclaw/workspace/AGENTS.md` -> `(n/a)`: No workspace target was provided
- `(n/a)` -> `/home/openclaw/.hermes/memories/MEMORY.md`: Source file not found
- `/home/openclaw/.openclaw/openclaw.json` -> `/home/openclaw/.hermes/.env`: No Discord settings found
- `/home/openclaw/.openclaw/openclaw.json` -> `/home/openclaw/.hermes/.env`: No Slack settings found
- `/home/openclaw/.openclaw/openclaw.json` -> `/home/openclaw/.hermes/.env`: No WhatsApp settings found
- `/home/openclaw/.openclaw/openclaw.json` -> `/home/openclaw/.hermes/.env`: No Signal settings found
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `/home/openclaw/.hermes/skills/openclaw-imports`: No OpenClaw skills directory found
- `(n/a)` -> `/home/openclaw/.hermes/skills/openclaw-imports`: No shared OpenClaw skills directories found
- `(n/a)` -> `/home/openclaw/.hermes/memories/MEMORY.md`: No workspace/memory/ directory found
- `(n/a)` -> `/home/openclaw/.hermes/tts`: Source directory not found
- `/home/openclaw/.openclaw/openclaw.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw OpenClaw config was not copied.
- `/home/openclaw/.openclaw/credentials/telegram-default-allowFrom.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw credentials file was not copied.
- `/home/openclaw/.openclaw/credentials` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/home/openclaw/.openclaw/devices` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/home/openclaw/.openclaw/identity` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `(n/a)` -> `(n/a)`: blocked by earlier apply conflict
- `/home/openclaw/.openclaw/workspace/SOUL.md` -> `/home/openclaw/.hermes/SOUL.md`: Target exists and overwrite is disabled
- `/home/openclaw/.openclaw/openclaw.json` -> `/home/openclaw/.hermes/config.yaml`: Model already set and overwrite is disabled

## Next Steps

- Review the migration report at /home/openclaw/.hermes/migration/openclaw/20260507T232901/summary.md
- Start a new Hermes session (or /reset) to pick up the imported config.
- Re-run with --overwrite to apply items that were blocked by conflicts.
