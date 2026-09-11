Objective

Make discovery and replay understandable to an evaluator.

Event model

Emit structured events such as:

RUN_STARTED
OBSERVATION_CAPTURED
ACTION_PROPOSED
POLICY_CHECKED
ACTION_STARTED
ACTION_COMPLETED
CHECKPOINT_VERIFIED
OUTCOME_DETECTED
INTERVENTION_REQUESTED
CONTROL_TRANSFERRED
RUN_COMPLETED
RUN_FAILED

**Evidence hierarchy**

Do not screenshot everything unnecessarily.

**Normal execution:**

structured JSONL trace

**Important checkpoints:**

structured event + optional snapshot

Failure:

structured event + screenshot + useful surface snapshot/DOM/accessibility data

The requirement asks for structured logging plus at least one richer failure signal.

Evidence directory

Example:

evidence/
├── discovery/
│   ├── run.jsonl
│   └── ...
├── replay-success/
│   ├── run.jsonl
│   └── ...
├── replay-not-found/
│   ├── run.jsonl
│   └── ...
└── artifacts/
    └── member-get-savings-balance.yaml

Acceptance criteria
 Discovery emits trace.
 Replay emits trace.
 Failures create richer evidence.
 Events share a consistent schema.
 Secrets aren't logged.
 Evidence can be committed safely to public repository.