Objective - Prevent capability artifacts from becoming Playwright scripts disguised as JSON.

Core models

Create typed representations for:

Observation
ElementCandidate
Action
ActionResult
Evidence
SessionReference

Actions

Initial normalized actions:

CLICK
TYPE
SELECT
NAVIGATE
READ
WAIT
ASSERT

Potential future actions can include (but only after we reach PRD-15-strech.md):

KEYPRESS
SCROLL
FOCUS
DESKTOP_CLICK
Element targeting

A target MUST support multiple locator candidates.

Example:
```YAML
target:
  semantic_name: "Member ID input"

  strategies:
    - kind: label
      value: "Member ID"

    - kind: role
      role: textbox
      name: "Member ID"

    - kind: text_proximity
      anchor: "Member ID"

    - kind: css
      value: "input[name='memberId']"
```

**Do NOT reduce recorded controls to one CSS selector.**

**Locator preference**

Recommended order:

semantic/accessibility
        ↓
label/text relationship
        ↓
structural relationship
        ↓
DOM selector
        ↓
visual/coordinate fallback

This ordering is an implementation decision toexplain in REPORT.md

Acceptance criteria
 Browser adapter implements SurfaceAdapter.
 Agent code doesn't directly call Playwright.
 Replay engine doesn't directly call Playwright.
 Actions are surface-neutral.
 Multiple locator strategies are representable.
 Architecture can plausibly accommodate desktop/accessibility adapters later.