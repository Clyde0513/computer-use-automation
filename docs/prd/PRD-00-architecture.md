Objective: 

Establish the architecture and core contracts for the computer-use automation system before implementation begins.

The system must support this lifecycle:

Natural-language goal
        │
        ▼
LLM Discovery
 observe → decide → act
        │
        ▼
Successful execution
        │
        ▼
Capability Artifact
        │
        ▼
Deterministic Replay
        │
        ├── SUCCESS
        ├── BUSINESS_OUTCOME
        ├── RECOVERABLE CONDITION
        ├── HARD FAILURE
        └── HUMAN INTERVENTION

The model discovers. The artifact becomes a reusable capability. Deterministic replay is how the AI agent invokes it in production.

Architectural principle

Discovery and production execution MUST be separate execution modes.

Discovery

LLM may:

- inspect observations;
- reason about the current UI;
- choose actions;
- determine whether the goal has been achieved.
- Replay

LLM MUST NOT determine normal execution steps.

Replay executes only the saved capability definition.

Required components

Implement clean boundaries for:
**Do not tightly couple these components.**

- DiscoveryAgent
- SurfaceAdapter
- CapabilityArtifact
- ArtifactRecorder
- ReplayEngine
- PolicyEngine
- OutcomeClassifier
- InterventionManager
- EvidenceRecorder

Surface boundary

Define a generic interface conceptually equivalent to:

```python
class SurfaceAdapter(Protocol):
    async def observe(self) -> Observation: ...
    async def execute(self, action: Action) -> ActionResult: ...
    async def capture_evidence(self) -> Evidence: ...
    async def get_session_reference(self) -> SessionReference: ...
```
**Browser-specific concepts MUST remain inside the browser adapter whenever possible.**


Control ownership
Every live session has exactly one owner:

**Automation MUST NOT issue actions while ownership is HUMAN.**

AUTOMATION
HUMAN

Non-goals

Do NOT implement:

- distributed queues;
- Kubernetes;
- production multi-tenancy;
- production authentication;
- desktop automation;
- elaborate operator dashboards.

**Acceptance criteria**
 Architecture boundaries documented.
 Discovery and replay are separate.
 Surface implementation is abstracted.
 Policy is independent of execution.
 Intervention ownership is represented.
 Observability can consume events from both discovery and replay.
 No unnecessary scaling infrastructure added.