Objective

Make the evaluator able to reproduce the project without reading the source first.

Required commands

Target UX:

```Bash
cua proxy start
```

```bash
cua discover \
  --goal "Look up member 10001 and return their savings balance" \
  --target http://localhost:8000
```

EXPECTED:

Goal completed.
Artifact:
capabilities/member-get-savings-balance.yaml

Then:

```Bash
cua replay \
  capabilities/member-get-savings-balance.yaml \
  --input member_id=10002
```

Expected structured result:
```Json
{
  "status": "SUCCESS",
  "outputs": {
    "savings_balance": "..."
  }
}
```

Then:

```bash
cua replay \
  capabilities/member-get-savings-balance.yaml \
  --input member_id=99999
```

Expected:
```json
{
  "status": "BUSINESS_OUTCOME",
  "outcome": "MEMBER_NOT_FOUND"
}
```

The README is specifically required to provide exact commands for discovery followed by replay.

Acceptance criteria
 Proxy starts from documented command.
 Discovery works from CLI.
 Artifact path returned.
 Replay works from CLI.
 Inputs accepted.
 Outputs printed.
 Known outcome printed distinctly from failure.
 Exit codes are sensible.