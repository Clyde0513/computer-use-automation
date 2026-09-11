Objective

Enforce guardrails independently from both the LLM and artifact.

Policy model
Example:
```YAML
allowed_targets:
  - "http://localhost:*"

allowed_actions:
  - NAVIGATE
  - CLICK
  - TYPE
  - READ
  - WAIT
  - ASSERT

risk_policy:
  SAFE: allow
  REVERSIBLE: allow
  RISKY: require_human
  IRREVERSIBLE: block
```

**Enforcement points**

Policy MUST run during:

discovery action
replay action
human-resume boundary
Redaction

Redact sensitive values from:

logs
model context where unnecessary
exception messages
artifact generation
screenshots where practical

Default-deny

Unknown action type:

DENY

Unknown domain:

DENY


Acceptance criteria
 Domain/target allowlist enforced.
 Action allowlist enforced.
 Risk classifications exist.
 Risky action can trigger intervention.
 Irreversible action can be blocked.
 Sensitive input isn't emitted into ordinary logs.
 Unknown actions default to deny.