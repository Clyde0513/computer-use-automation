Objective

Create a deliberate runtime taxonomy rather than treating every unexpected screen as an exception.

SUCCESS
│
├── BUSINESS_OUTCOME
│   ├── MEMBER_NOT_FOUND
│   └── ACTION_NOT_AVAILABLE
│
├── RECOVERABLE
│   ├── TRANSIENT_LOAD_FAILURE
│   ├── KNOWN_INTERSTITIAL
│   └── RETRYABLE_TIMEOUT
│
└── FAILURE
    ├── LOCATOR_NOT_FOUND
    ├── CHECKPOINT_FAILED
    ├── PERMISSION_DENIED
    ├── SESSION_EXPIRED
    ├── POLICY_VIOLATION
    └── UNKNOWN_STATE

The precise mapping of permission/session errors into recovery vs failure can be refined during implementation; what matters is that classification and response are explicit.

*Failure contract*

Example:
```JSON
{
  "status": "FAILURE",
  "error": {
    "code": "CHECKPOINT_FAILED",
    "step_id": "open-savings",
    "expected": "Savings account detail visible",
    "observed": "Permission denied dialog",
    "evidence_ref": "..."
  }
}
```

Recovery policy

Each recoverable condition defines:

maximum attempts
backoff
recovery action
checkpoint after recovery

Retries MUST be bounded.


Acceptance criteria
 Not-found returns business outcome.
 Transient load can recover.
 Retries have limits.
 Hard failures stop replay.
 Failure identifies step.
 Expected and observed states are recorded.
 Evidence reference returned.