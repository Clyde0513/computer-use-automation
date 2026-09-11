Objective: Implement an LLM-driven:

OBSERVE → DECIDE → ACT → OBSERVE

loop against the live proxy application.

**A real LLM discovery run is mandatory. It cannot be replaced with a scripted demonstration.**

Input:

```python
DiscoveryRequest(
    goal: str,
    target: Target,
    max_steps: int,
    timeout_seconds: int,
)
```

Loop: For EACH STEP:

```
1. Capture observation
2. Apply redaction
3. Give model:
   - goal
   - safe observation
   - allowed actions
   - previous relevant actions
4. Receive structured decision
5. Validate decision
6. Run policy check
7. Execute normalized action
8. Record result
9. Determine whether:
      continue
      success
      dead-end
      escalate
      timeout
```

**Structured model output**

Do not accept arbitrary executable code.

Example:

```JSON
{
  "reasoning_summary": "The member search form is visible.",
  "action": {
    "type": "TYPE",
    "target": {
      "semantic_name": "Member ID"
    },
    "value": "{{member_id}}"
  },
  "goal_status": "IN_PROGRESS"
}
```

Stopping conditions

Must include:

GOAL_REACHED
MAX_STEPS
TIMEOUT
DEAD_END
POLICY_BLOCK
HUMAN_INTERVENTION_REQUIRED

Security

LLM-proposed actions MUST pass through the same policy layer as replay actions.

The model is not trusted merely because it generated an action.

Evidence

Every discovery step must record:

- timestamp
- step number
- observation summary
- decision/reasoning summary
- proposed action
- policy decision
- action result
- checkpoint information

Acceptance criteria
 Genuine model API call occurs.
 Model observes live application.
 Model selects actions dynamically.
 Actions execute against real UI.
 Policy validates actions.
 Successful goal can be completed.
 Step limit works.
 Timeout works.
 Evidence exists.

 