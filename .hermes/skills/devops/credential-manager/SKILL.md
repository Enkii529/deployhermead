---
name: credential-manager
description: Provide scoped credential access to subagents via namespace isolation. Delegated tasks receive only the credentials they need, with full audit trails.
version: 1.0.0
author: Jason (via Hermes)
license: MIT
category: devops
tags:
  - credentials
  - isolation
  - subagents
  - delegation
  - security
metadata:
  hermes:
    related_skills: [1password-bitwarden-vault, subagent-driven-development]
---

# Credential Manager for Subagents

This skill defines a policy and protocol for safely delegating credentials to subagents during `delegate_task` calls. It prevents over-privileged access and ensures every secret use is auditable.

## Core Principles

- **Least privilege**: A subagent may only access credentials within its declared scope.
- **Explicit allowlist**: The parent agent defines the allowed credential scopes before delegation.
- **No direct vault access**: Subagents must request credentials through the parent or a controlled interface; they never call the vault CLI directly.
- **Audit trail**: All access attempts (granted and denied) are recorded in Honcho with `peer="ai"`.

## When to Use

- You are delegating a task to a subagent that requires secrets (API keys, passwords, tokens).
- You want to ensure the subagent cannot leak or misuse credentials beyond what it needs.
- You need an audit log of which agent accessed which secret and why.

## Delegation with Scoped Credentials

When calling `delegate_task`, include a `credential_scopes` field in the `context` or as a separate parameter (convention). For example:

```python
delegate_task(
    goal="Deploy the web app to production",
    context="You may need the AWS credentials and the Docker Hub token.\n\nAllowed credential scopes: aws:prod, dockerhub:ci",
    toolsets=["terminal", "file"]
)
```

Alternatively, structure the context with a clear section:

```
CREDENTIAL SCOPES (allowed):
- aws:prod
- dockerhub:ci

Do NOT request any other credentials. All requests outside these scopes will be denied.
```

## Subagent Behavior: Requesting a Credential

A subagent that needs a secret must:

1. **Declare intent** – State which credential scope it needs and why.
2. **Call back to the parent** – Since subagents cannot directly call other skills, they must output a message requesting the secret. The parent agent (you) will then use `1password-bitwarden-vault` to fetch it and pass it securely.

Example subagent output:
```
I need the AWS prod credentials to run `terraform apply`. Scope: aws:prod.
Please provide these as environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
```

The parent agent, upon receiving such a request, must:

- Verify the requested scope is within the allowed list.
- Use the vault skill to retrieve the secret(s).
- Pass them to the subagent via environment variables in its execution environment (if using subagent processes that support env) or via a temporary file with restricted permissions.
- Log the disclosure in Honcho.

## Parent Agent Pre-Delegation Checklist

- [ ] Identify all credential needs for the task.
- [ ] Define the minimal set of scopes (e.g., `github:repo-name`, `aws:env`, `sendgrid:marketing`).
- [ ] Include them clearly in the delegation context.
- [ ] Ensure the subagent understands it must request credentials rather than trying to fetch them itself.
- [ ] Plan to monitor the subagent's requests against the scope.

## Credential Scope Naming Convention

Use a `type:identifier` format to make scopes unambiguous:

- `1password:item-title` or `bitwarden:item-id`
- `aws:prod` (implies IAM role/credentials for production)
- `github:org/repo`
- `sendgrid:marketing`
- `supabase:project-id`

Document the available scopes in your user profile for reference.

## Auditing

After any credential access:

```bash
# Record that you disclosed a secret to a specific subagent
her honcho conclude conclusion="Disclosed AWS_PROD credentials to subagent 'deploy-bot' at 2025-06-18 14:30" peer="ai"
```

For subagents, also note the scope provided in the delegation record.

Periodically review Honcho conclusions for unusual patterns (e.g., many different scopes in a short time).

## Pitfalls

- **Scope too broad**: If the subagent requests a scope that is partially broader than allowed (e.g., `aws:*` vs `aws:prod`), deny or refine the scope.
- **Subagent ignoring policy**: If a subagent tries to run vault commands directly, terminate it and report a policy violation.
- **Secret leakage via logs**: Ensure the subagent's output does not echo the secret. If it does, rotate the credential immediately.
- **Environment persistence**: Clear environment variables after subagent completes; they may persist in the parent's shell if not careful.

## Integration with other skills

- **1password-bitwarden-vault**: Used by the parent to retrieve secrets.
- **subagent-driven-development**: This credential policy applies to every subagent spawned in a two-stage development workflow.
- **honcho**: Provides encrypted audit logging of all credential events.
