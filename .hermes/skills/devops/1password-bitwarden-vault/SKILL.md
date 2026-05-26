---
name: 1password-bitwarden-vault
description: Integrate with 1Password and Bitwarden to securely retrieve and use credentials. Access vaults via CLI, store access patterns in encrypted memory.
version: 1.0.0
author: Jason (via Hermes)
license: MIT
category: devops
tags:
  - credentials
  - vault
  - 1password
  - bitwarden
  - security
  - key-management
prerequisites:
  - 1password-cli or bitwarden-cli installed and logged in
metadata:
  hermes:
    related_skills: [honcho]
---

# 1Password / Bitwarden Vault Integration

Use this skill when tasks require accessing stored secrets (API keys, passwords, certificates) from a password manager. Secrets never appear in logs; only access patterns are recorded in Honcho.

## Prerequisites

- **1Password**: `op` CLI installed and signed in (`op signin`). Requires `OP_SESSION_<account>` env var.
- **Bitwarden**: `bw` CLI installed and logged in (`bw login`). Requires `BW_SESSION` env var.
- Honcho memory enabled with encrypted backend (cloud or self-hosted).

## When to Use

- User asks for an API key, database password, or other stored credential
- A subagent needs a secret to complete a delegated task
- Configuring services that require tokens/secrets
- Rotating or updating credentials in scripts

## Safety Rules

- Never echo full secrets to stdout; use environment variables or temporary files with restrictive permissions (0600)
- After using a secret, clear it from shell history and memory (`unset VAR`)
- Record only metadata (vault name, item title, timestamp) in Honcho; never store the secret itself
- Prefer `op read` or `bw get` with `--raw` to extract just the secret field
- If a secret must be passed to a subprocess, pipe it via stdin or env var, never through command-line arguments (visible in `ps`)

## 1Password Usage

List available vaults:
```bash
op vault list --format=json
```

List items in a vault:
```bash
op item list --vault="Personal" --format=json
```

Retrieve a specific field from an item:
```bash
op read "item-id-or-name" --field="password"  # prints password
op read "item-id-or-name" --field="username"
op read "item-id-or-name" --field="api-key"
```

You can also use `op item get <id> --fields fieldName` with `-- revealing` disabled in session.

## Bitwarden Usage

Log in (interactive):
```bash
bw login
```

Unlock vault (creates session):
```bash
bw unlock
# stores BW_SESSION env var
```

List items:
```bash
bw list item --format=json
```

Get a specific field:
```bash
bw get item "item-id-or-name" --field=password  # with --raw for just the value
```

Sync before reading to ensure latest:
```bash
bw sync
```

## Access Pattern with Honcho

After retrieving a credential, write a conclusion to Honcho (AI peer) to record the access pattern:

```bash
# Example: accessed GitHub token from 1Password
her honcho conclude conclusion="Fetched GitHub PAT for repo work on 2025-06-18" peer="ai"
```

Do NOT include the secret in the conclusion. Only note what was accessed, when, and for what purpose.

## Example Task

**Goal:** Set up a GitHub Actions secret in a repository.

1. Retrieve the GitHub token from the vault:
   ```bash
   export GH_TOKEN=$(op read "GitHub PAT" --field=password)
   ```
2. Use `gh` CLI to set secret:
   ```bash
   echo "$GH_TOKEN" | gh secret set ACTIONS_TOKEN --body -
   ```
3. Clear the environment variable:
   ```bash
   unset GH_TOKEN
   ```
4. Log the action:
   ```bash
   her honcho conclude conclusion="Set GitHub Actions secret ACTIONS_TOKEN for repo x" peer="ai"
   ```

## Integration with credential-manager

When a subagent requests a credential, the parent agent must:
- Verify the request is within the allowed scope (defined in delegation)
- Use this skill to fetch the secret
- Provide it to the subagent via environment variable or a secure temporary file
- Ensure the subagent does not leak the secret

The parent agent remains responsible for auditing all credential disclosures.

## Pitfalls

- **Session expiry**: Password manager sessions expire. If `op` or `bw` returns auth errors, re-authenticate.
- **CLI not found**: Ensure the CLI is in PATH. Use absolute path if necessary (`/usr/local/bin/op`).
- **Wrong vault/item**: Double-check names with `op vault list` or `bw list item`.
- **Secret in logs**: Avoid printing the secret; use `--silent` flags when possible.
- **Shell history**: Use `set +o history` before commands that contain the secret in plain text, then `set -o history` after.

## Reference

- 1Password CLI docs: https://developer.1password.com/docs/cli
- Bitwarden CLI docs: https://bitwarden.com/help/article/cli/
- Honcho memory: see `honcho` skill
