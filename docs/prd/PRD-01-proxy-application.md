Objective: Create a small local application representing a legacy financial servicing system.

This is a proxy only. No real bank data, credentials, or PII may be used.

**Primary workflow**

Member Search
      ↓
Member Detail
      ↓
Savings Account
      ↓
Read Current Balance

Primary goal:

```
Look up member {{member_id}} and return
their current savings balance.
```

**Secondary workflow**

Where feasible:

Member Search
      ↓
Member Detail
      ↓
Open Sub-Account
      ↓
Enter Parameters
      ↓
Review
      ↓
Confirmation Boundary

**The automated system should reach the review/confirmation state without committing a simulated irreversible financial action unless explicitly permitted.**

Required members

Seed fake records such as:

10001
10002
10003

**All identities/data must be synthetic.**

Required exceptional states

The proxy application MUST support deterministic triggering of:

MEMBER_NOT_FOUND
VALIDATION_ERROR
PERMISSION_DENIED
SESSION_EXPIRED
TRANSIENT_LOAD_FAILURE
UNEXPECTED_DIALOG

**Legacy characteristics**

Include several deliberately awkward properties:

- nested tables;
- weak/non-semantic markup;
- limited stable IDs;
- iframe or frame boundary;
- ambiguous buttons;
- server-style navigation;
- modal confirmation;
- artificial loading delay.

Do not make the site impossible to automate.

The objective is to exercise locator design, not create a CAPTCHA.

Acceptance criteria

 Search workflow works manually.
 Successful member lookup exists.
 Not-found state exists.
 Validation failure exists.
 Permission-denied scenario exists.
 Timeout/session-expiry scenario can be simulated.
 Synthetic data only.
 Application can run locally with one documented command.