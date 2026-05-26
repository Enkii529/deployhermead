---
name: self-improvement
description: Log learnings, errors, and corrections to enable continuous improvement. Use after failures, corrections, or discovering better approaches.
triggers:
  - command_failure
  - user_correction
  - missing_feature
  - api_failure
  - knowledge_gap
  - better_approach
---

# Self-Improvement Skill

Captures learnings and errors to enable continuous improvement for Hermes agents.

## When to Use

Trigger this skill when:
- A command or operation fails unexpectedly
- User corrects you ("No, that's wrong...", "Actually...")
- User requests a capability that doesn't exist
- An external API or tool fails
- You realize your knowledge is outdated or incorrect
- You discover a better approach for a recurring task

## Initialization

Before logging anything, ensure the `.learnings/` directory exists in the current working directory or project root. Create if missing:

```bash
mkdir -p .learnings
[ -f .learnings/LEARNINGS.md ] || printf "# Learnings\n\nCorrections, insights, and knowledge gaps.\n\n**Categories**: correction | insight | knowledge_gap | best_practice\n\n---\n" > .learnings/LEARNINGS.md
[ -f .learnings/ERRORS.md ] || printf "# Errors\n\nCommand failures and integration errors.\n\n---\n" > .learnings/ERRORS.md
[ -f .learnings/FEATURE_REQUESTS.md ] || printf "# Feature Requests\n\nCapabilities requested by the user.\n\n---\n" > .learnings/FEATURE_REQUESTS.md
```

**Never overwrite existing files.**

Do not log secrets, tokens, private keys, environment variables, or full source/config files. Prefer short summaries or redacted excerpts.

## Logging Formats

### Learning Entry (append to .learnings/LEARNINGS.md)

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-YYYYMMDD-XXX (if related)
- Recurrence-Count: 1 (optional)
```

### Error Entry (append to .learnings/ERRORS.md)

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
Actual error message or output

### Context
- Command/operation attempted
- Input or parameters used
- Environment details if relevant
- Summary or redacted excerpt of relevant output

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-YYYYMMDD-XXX (if recurring)
```

### Feature Request Entry (append to .learnings/FEATURE_REQUESTS.md)

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name
```

### ID Generation

Format: `TYPE-YYYYMMDD-XXX`
- TYPE: `LRN` (learning), `ERR` (error), `FEAT` (feature)
- YYYYMMDD: Current date
- XXX: Sequential number (001, 002...) or random 3 chars

## Resolving Entries

When an issue is fixed, update the entry:
- Change `**Status**: pending` → `**Status**: resolved`
- Add after Metadata:

```markdown
### Resolution
- **Resolved**: ISO-8601 timestamp
- **Notes**: Brief description of what was done
```

Other status values: `in_progress`, `wont_fix` (add reason), `promoted`.

## Promotion to Memory

When a learning is broadly applicable, promote it to Hermes persistent memory:

1. Distill into a concise fact or rule
2. Save via `memory` tool with appropriate target (`user` for preferences, `memory` for environment facts)
3. Update original entry: change `**Status**: pending` → `**Status**: promoted` and add `**Promoted**: memory`

**Promotion criteria:**
- Applies across multiple files/features
- Knowledge any contributor should know
- Prevents recurring mistakes
- Documents Hermes-specific conventions

## Best Practices

- **Log immediately** - context is freshest right after the issue
- **Be specific** - future agents need to understand quickly
- **Include reproduction steps** - especially for errors
- **Link related files** - makes fixes easier
- **Suggest concrete fixes** - not just "investigate"
- **Use consistent categories** - enables filtering
- **Promote aggressively** - if in doubt, add to memory
- **Review regularly** - check `.learnings/` at natural breakpoints

## Quick Status Check

```bash
# Count pending items
grep -h "Status\*\*: pending" .learnings/*.md | wc -l

# List pending high-priority items
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["

# Find learnings for a specific area
grep -l "Area\*\*: backend" .learnings/*.md
```

## Integration with Hermes

This skill works automatically:
- No hook configuration needed
- Use `memory()` to promote valuable learnings
- Review `.learnings/` before major tasks
- Hermes session memory provides cross-session context
