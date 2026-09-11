Objective
Execute a saved capability with supplied arguments without LLM decision-making.

This is the production execution path required

Interface

Conceptually:

```python
result = await replay_engine.execute(
    artifact=artifact,
    inputs={
        "member_id": "10002"
    }
)
```

**Execution**
For every step:

validate preconditions
        ↓
resolve target
        ↓
policy check
        ↓
execute action
        ↓
wait
        ↓
detect exceptional state
        ↓
verify postcondition/checkpoint
        ↓
record evidence

**Absolutely prohibited**
Normal replay MUST NOT call an LLM to decide:

- which element to click
- what step comes next
- whether to improvise navigation

**Locator resolution**
Attempt declared locators in deterministic order.

Record:

- which locator succeeded
- how long resolution took
- which candidates failed

Result contract
```python
ReplayResult(
    status=...,
    outputs=...,
    outcome=...,
    failure=...,
    evidence_ref=...,
)
```

Acceptance criteria
 Replay uses saved artifact.
 No LLM decision call occurs.
 Different member input works.
 Output is extracted.
 Success checkpoint is verified.
 Locator fallback works.
 Structured result returned.