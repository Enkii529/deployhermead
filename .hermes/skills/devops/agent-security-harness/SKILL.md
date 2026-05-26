---
name: agent-security-harness
description: Audit Hermes skills for security vulnerabilities, misconfigurations, and dangerous patterns. Validate before installing or periodically review the skill library.
version: 1.0.0
author: Jason (via Hermes)
license: MIT
category: devops
tags:
  - security
  - audit
  - skills
  - validation
metadata:
  hermes:
    related_skills: [requesting-code-review, system-self-healing]
---

# Agent Security Harness

Use this skill to vet Hermes skills (your own or third‑party) before they enter your library. It performs static analysis on skill files and checks for common security pitfalls.

## When to Use

- Before installing a new skill from the Skills Hub or a custom source
- Periodically scan your existing skill library for regressions
- When a skill exhibits suspicious behavior (unexpected network calls, file writes, etc.)
- As part of a compliance or hardening process

## What the Harness Checks

- **Hardcoded secrets**: API keys, tokens, passwords in scripts or config examples
- **Dangerous shell patterns**: `rm -rf /`, `dd`, `chmod -R 777`, unbounded user input in commands
- **Privilege escalation**: use of `sudo`, `pkexec`, or setuid without explicit user consent
- **Network exposure**: outbound calls to suspicious domains, unauthenticated webhooks
- **File system overreach**: writes outside the workspace, deletion of non-temporary files
- **Toolset mismatches**: skill declares `["terminal", "file"]` but uses `browser` without declaring it
- **Missing user confirmation**: actions that modify system state without a `clarify` step
- **Embedded credentials in examples**: sample API keys or tokens in markdown

## Harness Procedure

### 1. Enumerate Skills

List all installed skills:

```bash
hermes skills list --json > /tmp/skills.json
```

Or directly inspect directories:

```bash
find ~/.hermes/skills -maxdepth 2 -type d -name "*" | sed 's|.*/||' | sort > /tmp/skill_names.txt
```

### 2. Static Scan Each Skill

For each skill directory (`~/.hermes/skills/<category>/<name>/`), check:

#### a) SKILL.md content
```bash
grep -Ei "(api[_-]?key|secret|token|password|http://|https://)" SKILL.md | highlight
```
Look for credentials in examples or auth flows.

#### b) Shell scripts in `scripts/`
```bash
grep -rE "(curl.*-H.*Authorization|wget.*--header|scp|rsync.*-e|sudo|rm.*-rf|dd|mkfs)" scripts/
```

#### c) Python scripts
```bash
grep -rE "(os\.system|subprocess\.call|eval\(|exec\(|pickle\.load|yaml\.load.*Loader=None)" scripts/
```

#### d) Credential files in `references/` or `assets/`
```bash
find references assets -type f -exec grep -l "BEGIN RSA PRIVATE KEY\|BEGIN OPENSSH\|-----BEGIN PGP" {} \;
```

#### e) Node.js files
```bash
grep -rE "require('child_process').exec|spawn.*shell" .
```

### 3. Validate Toolset Declarations

If the skill uses `delegate_task`, check that its `toolsets` argument matches the tools it actually calls. For example, if a skill uses `web_search` but declares only `["terminal"]`, that's a mismatch (the tool will fail at runtime).

Scan the skill content for tool calls (`browser_`, `terminal(`, `delegate_task(` etc.) and compare to the `toolsets` array in the `delegate_task` invocation if present. For top-level skills (not subagents), this check is less relevant.

### 4. Check for User Confirmation

Look for `clarify(` calls before actions that change state. If a skill performs `write_file`, `terminal` with `sudo`, or `mcp_n8n_update_workflow` without asking, flag it.

### 5. Generate Report

Summarize findings:

- **Critical**: hardcoded secrets, unconditional `sudo`, network exfiltration
- **Warning**: missing `clarify` for state‑changing ops, toolset mismatch
- **Info**: suggestions for improvement

Output as JSON or markdown.

### 6. Remediation

For critical issues, quarantine the skill (move its directory to `~/.hermes/skills/quarantine/`). For warnings, contact the skill author or patch it yourself with `skill_manage(action='patch')`.

## Example Harness Invocation

You can run the harness manually or wrap it into a skill. A typical run:

```bash
# Create a quarantine folder if needed
mkdir -p ~/.hermes/skills/quarantine

# Loop over skills
for skill in $(find ~/.hermes/skills -mindepth 2 -maxdepth 2 -type d); do
  name=$(basename "$skill")
  echo "Scanning $name..."

  # Hardcoded secrets in SKILL.md
  if grep -qiE "(api[_-]?key|secret|token|password)" "$skill/SKILL.md" 2>/dev/null; then
    echo "  WARNING: Possible secret in SKILL.md"
  fi

  # Dangerous scripts
  if grep -rE "(sudo|rm -rf|dd)" "$skill/scripts" 2>/dev/null; then
    echo "  CRITICAL: Dangerous pattern in script"
    mv "$skill" ~/.hermes/skills/quarantine/
  fi
  
  # ... more checks
done
```

## Integration with other skills

- **system-self-healing**: If the harness detects a compromised skill, self‑healing may restore a known‑good version from backup.
- **requesting-code-review**: Similar static patterns can be reused here; consider leveraging its security patterns.
- **honcho**: Log harness results to Honcho for long‑term trend analysis.

## Pitfalls

- **False positives**: Not every `curl` is malicious; consider context.
- **Missing scripts**: Some skills embed code directly in SKILL.md; those require a more sophisticated parser.
- **Encrypted secrets**: Sometimes examples include placeholders like `YOUR_API_KEY`; that's fine, but actual keys are not.
- **Large codebases**: Scanning all scripts may be slow; limit to suspicious skills first.

## Advanced: Automated Harness Skill

You can turn this harness into a reusable skill (`agent-security-harness`) that runs on demand:

```bash
hermes agent-security-harness --all   # scan everything
hermes agent-security-harness --skill <name>  # specific skill
```

The skill would output a structured report and optionally auto‑quarantine critical findings with user confirmation.
