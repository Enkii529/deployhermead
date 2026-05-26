---
name: n8n-workflow-automation
description: Design robust n8n workflows with retries, logging, error handling, idempotency, and human-in-the-loop review queues. Use for auditable automations that won't silently fail.
triggers:
  - workflow_design
  - automation_request
  - n8n_workflow
  - error_handling_needed
  - idempotency_required
  - audit_trail_needed
---

# n8n Workflow Automation

Designs and outputs n8n workflow JSON with production-grade robustness: triggers, idempotency, error handling, logging, retries, and human-in-the-loop review queues.

## When to Use

Trigger this skill when:
- User asks to create an n8n workflow
- User wants automation with retries and error handling
- User needs idempotent workflows (avoid duplicates on retries)
- User requests audit logging or review queues
- User mentions "auditable", "won't silently fail", "human review"
- User wants to add error handling to existing n8n flows

Do NOT use when:
- Code-only automation is needed (use a scripting/CI skill)
- Security bypass or hidden audit trails are requested

## Input Requirements

Gather from user:
- **Trigger type**: cron, webhook, manual, schedule
- **Schedule/timezone** if cron
- **Success criteria**: what should happen on success
- **Targets**: where to write results (email, Drive, Sheet, DB, etc.)
- **Data contract**: input schema and required fields
- **Deduplication key**: what makes a record unique (for idempotency)
- **Credential strategy**: env var names or credential references
- **Error notification destination**: who to alert on failures

If any of these are unclear, STOP and ASK the user.

## Workflow Design Steps

1. **Design trigger node** with appropriate type and parameters
2. **Define input validation** with clear error messages
3. **Implement idempotency**: add dedup lookup using chosen key(s)
4. **Add observability**: generate run_id, log start/end, store status row
5. **Build main logic** nodes with proper data flow
6. **Add error handling**:
   - Per-node retry with exponential backoff (3 attempts)
   - Error branches that capture failure details
   - Final failure notification + write to review queue
7. **Add human-in-the-loop review queue**:
   - Write failed items to a tracking Sheet/DB table
   - Include: run_id, error, payload, timestamp, reprocess action
8. **Add "no silent failure" gates**:
   - Check counts/thresholds; if unmet, stop and alert
9. **Output**:
   - If user requested JSON: produce importable n8n workflow JSON + runbook.md
   - Otherwise: provide design spec (node map, data contracts, failure modes)

## Output Format (when JSON requested)

n8n workflow JSON structure (simplified):

```json
{
  "name": "Automated Compliance Summary",
  "nodes": [
    {
      "name": "Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": { "interval": [ { "field": "cronExpression", "value": "0 8 * * 1" } ] },
        "timezone": "America/New_York"
      },
      "position": [240, 300]
    },
    {
      "name": "Validate Input",
      "type": "n8n-nodes-base.if",
      "parameters": { "conditions": { "options": { "caseSensitive": true, "leftValue": "", "typeValidation": "strict" }, "conditions": [ { "leftValue": "={{ $json }}", "rightValue": 1, "operator": { "type": "number", "operation": "eq" } } ], "combinator": "and" } },
      "position": [460, 300]
    },
    // ... more nodes
  ],
  "connections": {
    "Trigger": { "main": [ [ { "node": "Validate Input", "type": "main", "index": 0 } ] ] }
  },
  "settings": { "executionOrder": "v1" },
  "active": false
}
```

Also provide a `runbook.md` with:
- Workflow purpose and schedule
- Success/failure criteria
- Idempotency key definition
- Error handling and retry policy
- Review queue location and reprocess procedure
- Monitoring/alerting contacts

## Safety & Best Practices

- **Never include secrets** in JSON; reference env vars/credential names only.
- **Idempotency is mandatory** unless user explicitly says it's okay to duplicate.
- **Always log runs**: write a status row with `run_id`, `status`, `timestamp`, `records_processed`.
- **Retry with backoff**: 3 attempts, exponential delays (1s, 4s, 9s).
- **Route all unhandled errors** to review queue and notify.
- **Prefer least privilege**: only call APIs that are necessary.
- **Validate inputs** early and fail fast with clear messages.
- **Include timeouts** on HTTP/database operations.
- **Do not disable error output** on any node.

## Example Output for User Request

**User says:** "Create an n8n workflow that runs every Monday at 8am, generates a compliance summary, emails it, and saves to Drive. Add error handling and a review queue."

**Response contains:**
1. Node map description
2. workflow.json (importable)
3. runbook.md with procedures
4. Notes on required credentials (n8n Gmail/Drive credentials)
5. Instructions to set env vars for retry delays and timeouts

## Prompts to User (when info missing)

- "What should trigger this workflow? Cron, webhook, or manual?"
- "What makes a record unique? I need a deduplication key."
- "Where should failures be queued for human review? A Google Sheet or database table?"
- "What credentials are available? (Gmail, Drive, etc.)"
- "Who should be notified on workflow failure? Email or Slack?"

## Limitations

- This skill designs workflows for n8n Cloud or self-hosted n8n.
- It assumes n8n's node types and parameters (uses `n8n-nodes-base.*`).
- It does not generate custom n8n nodes or TypeScript code.
- It does not handle n8n's execution mode (queue, worker) — that's operational.
