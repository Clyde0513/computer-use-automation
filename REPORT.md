# Architecture Decisions

## PRD-02: Surface abstraction

### Locator ordering

Targets retain an ordered collection of locator candidates rather than a single
selector. Adapters try candidates in artifact order, and recorders should emit
them in this preference order:

1. semantic and accessibility relationships (`label`, then `role`);
2. text and text-proximity relationships;
3. structural relationships within a named container;
4. DOM CSS selectors;
5. visual coordinates as a final fallback.

The order favors user-visible meaning over implementation detail, making
artifacts more resilient to markup changes. CSS remains representable because
legacy pages sometimes expose no stronger relationship. Coordinates are allowed
only as a locator fallback; no desktop action types are introduced in PRD-02.

### Dependency boundary

Core models and the `SurfaceAdapter` protocol do not import Playwright. The
browser adapter owns Playwright-shaped page, frame, locator, and mouse calls
behind a small internal protocol. This permits the same actions and results to
be implemented later by accessibility or desktop adapters without changing the
capability contract.

Embedded surface context is represented generically by a named context rather
than an iframe-specific field. The browser adapter maps it to a frame; a future
adapter may map the same concept to a pane or child accessibility surface.
