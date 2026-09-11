Objective

Implement a minimal but real:

AUTOMATION
    ↓
PAUSED
    ↓
HUMAN
    ↓
RESUME
    ↓
AUTOMATION

handoff on the same live session.

THIS IS EXPLICITLY REQUIRED; merely opening a fresh browser for the human would not satisfy the requested control-transfer model.

**Intervention request**
```Python
InterventionRequest(
    id,
    run_id,
    capability_id,
    goal,
    step_id,
    reason,
    evidence_ref,
    session_ref,
    status,
)
```

**Ownership model**
```Python
class SessionOwner(Enum):
    AUTOMATION = "automation"
    HUMAN = "human"
```

**When human owns session:**

automation MUST pause
automation MUST NOT issue UI actions

**Minimal operator surface**
A sophisticated co-browsing product is explicitly unnecessary.

Acceptable implementation:

terminal command or minimal local web page

**Operator must be able to:**

- view intervention
- take ownership
- interact with existing browser/session
- mark intervention resolved
- return ownership
- resume run

**Human action evidence**
Record manual actions when practical.

At minimum record:

- handoff timestamp
- operator claimed control
- manual phase started
- manual phase ended
- operator note
- control returned

Acceptance criteria
 Automation can pause.
 Intervention request created.
 Human accesses same live session.
 Ownership prevents concurrent automation actions.
 Human can return control.
 Automation can resume.
 Handoff appears in evidence.