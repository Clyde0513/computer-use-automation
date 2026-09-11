# Computer-Use Automation System - Agent Instructions

## Project Purpose

This repository implements the Computer-Use Automation System.

The central lifecycle is:

Natural-language goal
→ LLM-driven discovery
→ successful run
→ structured capability artifact
→ deterministic replay
→ structured result / business outcome / failure
→ human intervention when required

The system is intended to demonstrate a focused end-to-end vertical slice rather than a production-scale distributed platform.

## Authoritative Requirements

The assignment requirements are represented by the PRDs under:

`/docs/prd/`

The PRDs are the primary implementation planning documents.

Before implementing a PRD:

1. Read the named PRD completely.
2. Read its referenced dependencies.
3. Inspect the existing implementation.
4. Preserve existing architectural contracts unless there is a strong reason to change them.
5. Identify contradictions or missing information before making a material architectural decision.

When the PRD does not prescribe a specific implementation, use engineering judgment and prefer the simplest design that satisfies the requirement.

**Do not silently replace or weaken a stated requirement.**

## Implementation Order

Implement PRDs in order unless explicitly instructed otherwise:

READ PRD-00 FIRST BEFORE IMPLEMENTING ANY OTHER PRDs
→ PRD-01
→ PRD-02
→ PRD-03
→ PRD-04
→ PRD-05
→ PRD-06
→ PRD-07
→ PRD-08
→ PRD-09
→ PRD-10
→ PRD-11
→ PRD-12
→ PRD-13
→ PRD-14
→ PRD-15

PRD-15 is optional and must NOT be allowed to compromise the core system.

## Scope Discipline

When asked to implement a specific PRD:

* Focus on that PRD.
* Do not proactively implement later PRDs.
* Do not add distributed infrastructure unless explicitly required.
* Do not add framework-heavy abstractions without a concrete need.
* Prefer a small working implementation over a broad incomplete implementation.
* Make necessary compatibility changes to earlier code when required by the current PRD, but document those changes.

Do not optimize for feature count.

## Core Architecture Rules

The following boundaries are fundamental:

* Discovery and replay are separate execution modes.
* The LLM may make decisions during discovery.
* Normal deterministic replay must not use an LLM to decide what to do next.
* Computer interaction must occur through the SurfaceAdapter abstraction.
* Policy checks must occur before automated actions are executed.
* Observability must cover both discovery and replay.
* Human intervention must preserve the existing live session.
* Session control must have an explicit owner.
* Business outcomes must be distinguished from technical failures.

Do not bypass these boundaries for convenience.

## Surface Abstraction

Do not allow core agent, artifact, replay, or policy logic to depend directly on Playwright or another specific computer-use framework.

Browser-specific implementation belongs behind the surface adapter.

The architecture should remain capable of supporting other surfaces in the future, including legacy web applications and desktop applications, without requiring a redesign of the capability model.

## Discovery

Discovery must be a genuine model-driven interaction with a live application surface.

The discovery system should follow:

OBSERVE
→ DECIDE
→ POLICY CHECK
→ ACT
→ OBSERVE

Model-generated actions must be represented as structured actions rather than arbitrary executable code.

Discovery should have explicit stopping conditions including:

* goal reached
* maximum steps
* timeout
* dead end
* policy block
* human intervention

## Capability Artifacts

Capability artifacts are the production contract.

They must be:

* typed
* serializable
* versioned
* reviewable
* parameterized
* independent of the raw LLM transcript

Artifacts must describe:

* ordered actions
* target identification strategies
* typed inputs
* typed outputs
* checkpoints / success conditions
* known outcomes
* compatibility information
* policy-relevant metadata where appropriate

Do not make replay dependent on model reasoning history.

Never embed credentials, session tokens, raw secrets, or unnecessary sensitive values in artifacts.

## Deterministic Replay

Replay is the production execution path.

Replay must:

1. Load and validate the artifact.
2. Validate invocation inputs.
3. Execute the declared steps deterministically.
4. Resolve targets using declared locator strategies.
5. Enforce policy before actions.
6. Detect runtime conditions.
7. Recover only according to bounded, explicit recovery rules.
8. Verify checkpoints.
9. Extract declared outputs.
10. Return a structured result.

Do not introduce open-ended model reasoning into normal replay.

If a future recovery mechanism uses an LLM, it must be explicitly bounded, policy-checked, and treated as a separate capability rather than silently becoming normal replay behavior.

## Outcome Taxonomy

Do not treat every non-success state as an exception.

Maintain explicit distinction between:

* successful execution
* expected business outcome
* recoverable runtime condition
* hard failure
* human intervention

For example, a record-not-found result is a legitimate business outcome when defined by the capability contract.

Failures should identify, where possible:

* run
* capability
* step
* expected state
* observed state
* failure code
* evidence reference

## Safety

Security is a cross-cutting concern.

Enforce explicit allowlists for:

* allowed targets/domains/routes
* allowed action types

Risky and irreversible actions must be handled conservatively.

Unknown actions and unknown targets should default to denial.

Never commit secrets.

Never use real financial credentials or real customer PII.

Synthetic/local data is the default for the project.

Sensitive information must be redacted from logs, artifacts, model context where unnecessary, and error messages.

## Human Intervention

Human handoff must operate on the same live session.

The automation must:

1. Detect the intervention condition.
2. Pause.
3. Create an intervention request containing useful context.
4. Transfer session ownership to a human.
5. Prevent concurrent automation actions.
6. Allow the human to act on the existing live session.
7. Record the handoff.
8. Accept an explicit return of control.
9. Resume automation.

Do not implement a fake workflow where the human receives a fresh session.

A minimal operator interface is sufficient.

## Observability

Important actions must generate structured evidence.

At minimum capture:

* run ID
* timestamps
* step IDs
* actions
* policy decisions
* action results
* checkpoints
* outcomes
* failures
* intervention events

Failures should include a richer diagnostic signal such as a screenshot, surface snapshot, DOM snapshot, accessibility snapshot, or equivalent evidence.

Do not leak sensitive information through observability.

## Testing

Every PRD implementation must include tests appropriate to its acceptance criteria.

Prioritize tests for:

* schemas
* policy enforcement
* deterministic replay
* checkpoint verification
* runtime outcome classification
* recovery limits
* human session ownership
* end-to-end vertical slice

Do not chase arbitrary test-count metrics.

## Dependency Changes

Before introducing a new dependency:

1. Check whether the existing stack already provides the functionality.
2. Prefer a mature, focused dependency.
3. Avoid adding infrastructure dependencies for convenience.
4. Keep the dependency justified by the current PRD.

Update dependency manifests and documentation when required.

## Code Quality

Prefer:

* strong typing
* small interfaces
* explicit data models
* deterministic behavior
* clear error handling
* readable naming
* focused modules
* testable boundaries

Avoid:

* giant classes
* hidden global state
* implicit coupling
* duplicated business logic
* speculative abstractions
* unnecessary metaprogramming

## Completion Protocol

After implementing a PRD:

1. Run the relevant tests.
2. Run formatting/lint/type checks used by the repository.
3. Review the implementation against every acceptance criterion.
4. Identify any unmet requirement.
5. Identify files changed.
6. Identify commands used to verify the implementation.
7. Explain any architectural trade-offs made.
8. Do not claim completion for an acceptance criterion that was not actually verified.

When asked to implement a PRD, report:

### Implementation

What was changed.

### Verification

Tests/checks run and their results.

### Acceptance Criteria

PASS/FAIL for each criterion.

### Remaining Issues

Anything unfinished or requiring a deliberate decision.

### Next PRD

State the next logical PRD, but do not implement it unless explicitly asked.

## Important Constraint

The goal is not to build an entire production automation platform.

The goal is to build a convincing, coherent, working vertical slice demonstrating:

goal
→ discovery
→ capability
→ deterministic replay
→ outcomes/errors
→ human handoff
→ evidence
→ safety

Depth matters more than breadth.
