**Do this only after PRD-14 passes and every PRD before PRD-14 is fully functional.**

I recommend choosing canonicalization / cross-tenant reuse.

Why? Because it reinforces one of the company's actual problems instead of adding decorative functionality.

Demonstrate:

Base Vendor Application
         │
         ├──────────────┐
         ▼              ▼
Tenant A Variant    Tenant B Variant
         │              │
         └──────┬───────┘
                ▼
      Same Capability

Introduce a slightly altered proxy variant.

Change things such as:

- button label
- container structure
- route prefix
- one locator
- branding

Then demonstrate the same logical artifact operating using compatibility metadata and/or controlled locator overrides.

Do not create two separate recordings.

Acceptance criteria
 Second application variant exists.
 Same capability identity used.
 Differences represented as overrides/fallbacks.
 No duplicate hand-built capability.
 REPORT explains implications for tenant reuse.