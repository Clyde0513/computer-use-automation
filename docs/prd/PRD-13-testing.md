Objective

Test the architecture where correctness matters instead of maximizing test count.

Required test categories

**Schema**

valid artifact
invalid action
invalid input schema
missing checkpoint
unknown schema version

**Policy**

allowed target
blocked target
allowed action
blocked action
risky action
redaction

**Replay**

successful replay
locator fallback
checkpoint failure
business outcome
transient recovery
hard failure

**Handoff**

automation pauses
ownership becomes HUMAN
automation cannot act while HUMAN
ownership returns
automation resumes
End-to-end

**At least:**

Discovery success
        ↓
Artifact
        ↓
Replay success

and:

Artifact
        ↓
Replay
        ↓
MEMBER_NOT_FOUND

and:

Artifact
        ↓
Unexpected/risky state
        ↓
Human intervention
        ↓
Resume

Acceptance criteria
 Evaluation-critical components tested.
 Tests don't depend on external production sites.
 Error taxonomy exercised.
 Handoff ownership tested.
 Core end-to-end workflow tested.