Objective - Create the central reusable capability contract.

Spend disproportionate care here.

Top-level model

Recommended conceptual structure:

```YAML
schema_version: "1.0"

capability:
  id: "member.get_savings_balance"
  name: "Get Savings Balance"
  version: "1.0.0"
  description: "..."

compatibility:
  application_family: "mock-core-banking"
  application_versions:
    - "1.x"

inputs: {}

outputs: {}

policy: {}

steps: []

outcomes: []

success_condition: {}

metadata: {}
```

Inputs

Example:
```YAML
inputs:
  member_id:
    type: string
    required: true
    description: "Synthetic member identifier"
    sensitive: true
```

Outputs:
```YAML
outputs:
  savings_balance:
    type: decimal
    description: "Current savings balance"
    sensitive: true
```

Steps: Every step needs an ID.
```YAML
- id: search-member
  action: type

  target:
    semantic_name: "Member ID"
    locators:
      - strategy: label
        value: "Member ID"
      - strategy: css
        value: "input[name='memberId']"

  value:
    input_ref: member_id

  preconditions: []

  postconditions:
    - type: visible
      target: "Search"

  timeout_ms: 5000
```

Checkpoints

A step may define expectations such as:
```YAML
checkpoint:
  all:
    - page_contains: "Member Details"
    - element_visible: "Savings"
```

Outcomes

Represent known business outcomes explicitly.

Example:
```YAML
outcomes:
  - code: MEMBER_NOT_FOUND
    kind: BUSINESS_OUTCOME

    detection:
      text_visible: "Member not found"

    outputs:
      member_found: false
```

**"no such member" is a legitimate result rather than a system crash.**

Versioning

**Artifacts MUST contain:**

schema_version
capability version
created timestamp
application compatibility information

**Prohibited contents**

Artifact MUST NOT contain:

credentials
API tokens
session cookies
raw screenshots
real PII
literal sensitive invocation values

Acceptance criteria
 Pydantic models exist.
 JSON serialization works.
 YAML serialization works if chosen.
 Inputs are typed.
 Outputs are typed.
 Steps are typed.
 Targets support fallback locators.
 Outcomes are typed.
 Checkpoints are represented.
 Schema is versioned.
 Invalid artifacts fail validation.