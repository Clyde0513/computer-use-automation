Objective

Transform a successful discovery run into a reusable capability rather than storing the raw LLM conversation.

The artifact must be decoupled from the raw model transcript.

Requirements

Recorder must:

- consume discovery trace
- identify successful actions
- normalize actions
- parameterize invocation-specific values
- construct robust locator candidates
- attach checkpoints
- declare outputs
- produce valid artifact

Parameterization

Discovery:

TYPE "10001" into member ID

Artifact:
```YAML
value:
  input_ref: member_id
```

Never save the discovery input as though it were part of the capability.

Transcript separation

Store separately:

Discovery evidence
Capability artifact

Do not make replay depend on:

LLM conversation
reasoning text
prompt
model response history

Acceptance criteria
 Successful discovery creates an artifact.
 Invocation data becomes parameter references.
 Artifact validates against PRD-04.
 Artifact can be inspected without understanding the LLM transcript.
 Sensitive values aren't embedded.