---
name: clawaudit
description: Audit a codebase for security vulnerabilities and generate a custom security review skill tailored to the project's patterns.
version: 1.0.0
author: Jason (via Hermes)
license: MIT
category: software-development
tags:
  - security
  - code-audit
  - skill-generation
  - custom
metadata:
  hermes:
    related_skills: [requesting-code-review, agent-security-harness]
---

# Clawaudit – Code Auditing + Custom Skill Generation

Clawaudit combines deep code scanning with Hermes skill synthesis. It analyzes a codebase for security issues, then generates a reusable, project‑specific security review skill that codifies the patterns found. Over time, you build a library of custom security skills tuned to each project.

## When to Use

- You want to baseline the security posture of a codebase
- You need a custom security checklist that evolves with the project
- You are setting up a new project and want to bake in security gates
- You want to automate security reviews for future changes using a tailored skill

## High‑Level Workflow

1. **Collect codebase** – clone or locate the repository
2. **Static analysis** – run a battery of scanners (grep, bandit, semgrep if available, patterns from `requesting-code-review`)
3. **Pattern extraction** – identify the most common vulnerability categories (SQLi, XSS, path traversal, hardcoded secrets, etc.)
4. **Skill synthesis** – generate a new SKILL.md that contains a pre‑configured security review process for this project
5. **Install skill** – place the generated skill under `~/.hermes/skills/custom/` with a meaningful name
6. **Handbook** – optionally create a reference doc with examples of issues found

## Step‑by‑Step

### Step 1: Prepare the codebase

Ensure you have a clean working copy:

```bash
git clone <repo-url> /tmp/audit-repo
cd /tmp/audit-repo
git checkout main   # or the branch you want to audit
```

If the repo is local, just `cd` to it.

### Step 2: Run the scanners

Create a temporary directory for artifacts:

```bash
mkdir -p /tmp/audit-results
```

#### a) Common insecure patterns (grep)

```bash
# Hardcoded secrets
grep -rE "(api[_-]?key|secret|password|token|passwd)\s*=\s*['\"][^'\"]{6,}['\"]" --include="*.py" --include="*.js" --include="*.ts" --include="*.java" --include="*.go" --include="*.rb" --include="*.php" . > /tmp/audit-results/hardcoded-secrets.txt

# SQL injection via string formatting
grep -rE "(execute\(f\"|\.format\(.*SELECT|\.format\(.*INSERT|\.format\(.*UPDATE|\.format\(.*DELETE)" --include="*.py" --include="*.js" . > /tmp/audit-results/sql-injection.txt

# Shell/command injection
grep -rE "(os\.system|subprocess\.(call|run|Popen).*shell=True|eval\(|exec\()" --include="*.py" . > /tmp/audit-results/command-injection.txt

# Path traversal
grep -rE "(open\(.*\+.*os\.path\.join|\.\.\/|\.\.\\\\\\\|path traversal)" --include="*.py" -i . > /tmp/audit-results/path-traversal.txt

# Unsafe deserialization
grep -rE "(pickle\.loads?|yaml\.load\(.*Loader=None|marshal\.loads)" --include="*.py" . > /tmp/audit-results/unsafe-deserialization.txt

# Insecure direct object reference (numeric IDs without auth checks)
grep -rE "(SELECT.*FROM.*WHERE.*id\s*=\s*[0-9]+|user_id\s*=\s*request\.)" --include="*.py" . > /tmp/audit-results/idor.txt
```

#### b) Language‑specific tools (if installed)

- **Python** – `bandit -r . -f json -o /tmp/audit-results/bandit.json`
- **JavaScript/TypeScript** – `npx eslint . --rule 'security/detect-object-injection: error'` or `npm audit`
- **Java** – `spotbugs`
- **Go** – `gosec`

If a tool is not installed, skip it; the harness will note its absence.

#### c) Requesting‑code‑review patterns

You can mimic the static scan from `requesting-code-review`:

```bash
git diff --cached  # if reviewing uncommitted changes; otherwise diff HEAD~1
# Apply the same greps as in that skill’s Step 2
```

Since this is an audit of the whole repo, just grep the entire tree.

### Step 3: Summarize findings

Parse the result files to count occurrences by category and list top files:

```python
import json, os, collections

categories = {
    'hardcoded_secrets': '/tmp/audit-results/hardcoded-secrets.txt',
    'sql_injection': '/tmp/audit-results/sql-injection.txt',
    'command_injection': '/tmp/audit-results/command-injection.txt',
    'path_traversal': '/tmp/audit-results/path-traversal.txt',
    'unsafe_deserialization': '/tmp/audit-results/unsafe-deserialization.txt',
    'idor': '/tmp/audit-results/idor.txt'
}

summary = {}
for cat, path in categories.items():
    if os.path.exists(path):
        with open(path) as f:
            lines = f.readlines()
        # Extract filenames
        files = [line.split(':')[0] for line in lines]
        summary[cat] = {
            'count': len(lines),
            'files': list(set(files))
        }
    else:
        summary[cat] = {'count': 0, 'files': []}

print(json.dumps(summary, indent=2))
```

This summary will guide the custom skill content.

### Step 4: Generate the custom skill

Based on the top categories, create a SKILL.md that focuses the review on those areas. Use a template:

```markdown
---
name: <project>-security-review
description: Automated security review for the <Project> codebase. Focus: <top categories>.
version: 1.0.0
author: Generated by clawaudit
license: MIT
category: software-development
tags:
  - security
  - <project>
metadata:
  hermes:
    related_skills: [requesting-code-review]
---

# <Project> Security Review

This skill is custom‑generated for the <Project> repository. It encodes the security patterns that matter most for this codebase, based on a comprehensive audit.

## When to Use

- Before committing changes to <Project>
- In CI/CD pipeline as a gate
- When reviewing pull requests

## Triggers

Run automatically on `git commit`, or manually:
```bash
hermes <project>-security-review
```

## Scan Process

1. **Collect diff** (reviewing changes) or full repo snapshot.
2. **Run project‑specific checks** (see below).
3. **Report findings** with severity.

### Custom Checks (derived from audit)

<For each high‑count category, insert a specific check section. Example:>

#### Hardcoded Secrets

```bash
grep -rE "(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]" --include="*.py" --include="*.js" .
```

Any match is a **critical** issue.

#### SQL Injection

Look for string interpolation in queries:

```bash
grep -rE "(execute\(f\"|\.format\(.*SELECT|\.format\(.*INSERT)" --include="*.py" .
```

Prefer parameterized queries.

< Repeat for each category with appropriate command and explanation. >

## Integration with requesting-code-review

This skill is complementary. The requesting code review pipeline runs generic checks; this project‑specific skill adds deeper, domain‑focused scrutiny.

## Pitfalls

- Scans only cover known patterns; new vulnerability classes require manual review.
- Large repos may slow down; consider scanning only changed files in CI.

## Generated By

Clawaudit on 2025‑06‑18. Source repo: /path/to/repo.

```

Save this as `~/.hermes/skills/custom/<project>-security-review/SKILL.md`.

### Step 5: Install the skill

```bash
mkdir -p ~/.hermes/skills/custom/<project>-security-review
cp /tmp/generated_skill.md ~/.hermes/skills/custom/<project>-security-review/SKILL.md
```

Then test it:

```bash
hermes <project>-security-review --help   # if you added help section
```

### Step 6: Keep it updated

Re‑run clawaudit periodically (e.g., quarterly) to refresh the skill as the codebase evolves. If new categories emerge, augment the skill.

## Full‑Automation Script (Optional)

You can wrap the above into a script `scripts/clawaudit.sh`:

```bash
#!/usr/bin/env bash
set -e

REPO_PATH="${1:-.}"
PROJECT_NAME="$(basename "$REPO_PATH")"
OUT_DIR="$HOME/.hermes/skills/custom/${PROJECT_NAME}-security-review"
mkdir -p "$OUT_DIR"

# Run all scans (the steps above)
# ... (omitted for brevity)

# Generate SKILL.md from a template, substituting findings
python3 generate_skill.py --summary /tmp/audit-summary.json --output "$OUT_DIR/SKILL.md"

echo "Installed skill: ${PROJECT_NAME}-security-review"
```

Then invoke `clawaudit` by running that script.

## Integration with Other Skills

- **requesting-code-review**: Copy its security patterns as a baseline; this skill specializes them.
- **agent-security-harness**: The generated skill can later be audited by the harness to ensure it doesn't introduce new risks.
- **honcho**: Record the audit run and skill creation in Honcho for traceability.

## Pitfalls

- **Over‑fitting**: A custom skill might become too narrow; continue to include generic checks occasionally.
- **Toolchain gaps**: If a scanner (e.g., bandit) is missing, the skill will rely only on grep; consider adding those tools to the environment.
- **False positives**: Grep patterns are crude; the skill should include instructions to triage findings.
- **Skill sprawl**: One skill per project can multiply; maintain a catalog or use generic skill with per‑project config.

## Advanced: Continuous Learning

After each use of the custom skill, capture its false positives/negatives and refine the grep patterns. Consider storing these refinements in the skill's `tuning/` directory so the skill improves over time.
