"""Playwright-backed browser implementation of the surface boundary.

Only this module contains browser-driver-shaped calls. The core contracts do
not import Playwright, and the page object is accepted structurally so importing
the contract package does not launch or initialize a browser.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID, uuid4

from .base import SurfaceAdapter
from .models import (
    Action,
    ActionResult,
    ActionStatus,
    AssertAction,
    AssertionCondition,
    ClickAction,
    CoordinateLocator,
    CssLocator,
    ElementCandidate,
    Evidence,
    EvidenceEncoding,
    EvidenceKind,
    LabelLocator,
    LocatorStrategy,
    NavigateAction,
    Observation,
    ReadAction,
    ReadProperty,
    RoleLocator,
    SelectAction,
    SessionOwner,
    SessionReference,
    StructuralLocator,
    SurfaceError,
    SurfaceKind,
    Target,
    TextLocator,
    TextProximityLocator,
    TypeAction,
    WaitAction,
    utc_now,
)


class _Locator(Protocol):
    @property
    def first(self) -> _Locator: ...

    async def count(self) -> int: ...

    async def click(self, **kwargs: Any) -> None: ...

    async def fill(self, value: str, **kwargs: Any) -> None: ...

    async def type(self, value: str, **kwargs: Any) -> None: ...

    async def select_option(self, value: str, **kwargs: Any) -> None: ...

    async def inner_text(self, **kwargs: Any) -> str: ...

    async def input_value(self, **kwargs: Any) -> str: ...

    async def get_attribute(self, name: str, **kwargs: Any) -> str | None: ...

    async def is_visible(self) -> bool: ...

    async def wait_for(self, **kwargs: Any) -> None: ...

    async def evaluate_all(self, script: str) -> list[Mapping[str, Any]]: ...

    def locator(self, selector: str) -> _Locator: ...

    def get_by_role(self, role: str, **kwargs: Any) -> _Locator: ...


class _BrowserRoot(Protocol):
    def locator(self, selector: str) -> _Locator: ...

    def get_by_label(self, value: str, **kwargs: Any) -> _Locator: ...

    def get_by_role(self, role: str, **kwargs: Any) -> _Locator: ...

    def get_by_text(self, value: str, **kwargs: Any) -> _Locator: ...


class _Mouse(Protocol):
    async def click(self, x: float, y: float) -> None: ...


class _BrowserPage(_BrowserRoot, Protocol):
    url: str
    mouse: _Mouse

    async def title(self) -> str: ...

    async def goto(self, destination: str, **kwargs: Any) -> None: ...

    async def wait_for_timeout(self, duration_ms: int) -> None: ...

    async def screenshot(self, **kwargs: Any) -> bytes: ...

    def frame(self, *, name: str) -> _BrowserRoot | None: ...


class BrowserSurfaceAdapter(SurfaceAdapter):
    """Translate surface-neutral actions into calls on an async Playwright page."""

    def __init__(self, page: _BrowserPage, session_id: UUID | None = None) -> None:
        self._page = page
        self._session_id = session_id or uuid4()

    async def get_session_reference(self) -> SessionReference:
        return SessionReference(
            session_id=self._session_id,
            surface_kind=SurfaceKind.BROWSER,
            adapter_name=type(self).__name__,
            owner=SessionOwner.AUTOMATION,
            location=str(self._page.url),
        )

    async def observe(self) -> Observation:
        session = await self.get_session_reference()
        title = await self._page.title()
        visible_text = await self._page.locator("body").inner_text()
        raw_elements = await self._page.locator(
            "a,button,input,select,textarea,[role]"
        ).evaluate_all(_ELEMENT_SNAPSHOT_SCRIPT)
        elements = tuple(self._element_candidate(item) for item in raw_elements)
        return Observation(
            session=session,
            location=str(self._page.url),
            title=title,
            visible_text=visible_text,
            elements=elements,
            metadata={"adapter": "playwright", "element_count": len(elements)},
        )

    async def execute(self, action: Action) -> ActionResult:
        started_at = utc_now()
        try:
            value = await self._execute_action(action)
        except Exception as exc:
            return ActionResult(
                action_id=action.action_id,
                status=ActionStatus.FAILED,
                started_at=started_at,
                completed_at=utc_now(),
                error=SurfaceError(
                    code=type(exc).__name__.upper(),
                    message=str(exc) or "Browser action failed",
                    retryable=type(exc).__name__ in {"TimeoutError", "TargetClosedError"},
                ),
            )
        return ActionResult(
            action_id=action.action_id,
            status=ActionStatus.SUCCEEDED,
            started_at=started_at,
            completed_at=utc_now(),
            value=value,
        )

    async def capture_evidence(self) -> Evidence:
        screenshot = await self._page.screenshot(full_page=True)
        return Evidence(
            session=await self.get_session_reference(),
            kind=EvidenceKind.SCREENSHOT,
            media_type="image/png",
            encoding=EvidenceEncoding.BASE64,
            content=base64.b64encode(screenshot).decode("ascii"),
            metadata={"full_page": True},
        )

    async def _execute_action(self, action: Action) -> str | None:
        if isinstance(action, NavigateAction):
            await self._page.goto(
                action.destination,
                wait_until="domcontentloaded",
                timeout=action.timeout_ms,
            )
            return str(self._page.url)
        if isinstance(action, WaitAction):
            if action.duration_ms is not None:
                await self._page.wait_for_timeout(action.duration_ms)
            else:
                assert action.target is not None and action.state is not None
                locator = await self._resolve(action.target)
                await locator.wait_for(state=action.state.value, timeout=action.timeout_ms)
            return None
        if isinstance(action, ClickAction):
            await self._click(action)
            return None

        locator = await self._resolve(action.target)
        if isinstance(action, TypeAction):
            if action.clear_first:
                await locator.fill(action.text, timeout=action.timeout_ms)
            else:
                await locator.type(action.text, timeout=action.timeout_ms)
            return None
        if isinstance(action, SelectAction):
            await locator.select_option(action.value, timeout=action.timeout_ms)
            return None
        if isinstance(action, ReadAction):
            if action.property is ReadProperty.TEXT:
                text = await locator.inner_text(timeout=action.timeout_ms)
                return str(text)
            if action.property is ReadProperty.VALUE:
                value = await locator.input_value(timeout=action.timeout_ms)
                return str(value)
            assert action.attribute_name is not None
            attribute = await locator.get_attribute(
                action.attribute_name,
                timeout=action.timeout_ms,
            )
            return None if attribute is None else str(attribute)
        if isinstance(action, AssertAction):
            await self._assert(locator, action)
            return None
        raise TypeError(f"Unsupported normalized action: {type(action).__name__}")

    async def _click(self, action: ClickAction) -> None:
        root = self._root_for(action.target)
        errors: list[str] = []
        for strategy in action.target.strategies:
            if isinstance(strategy, CoordinateLocator):
                try:
                    await self._page.mouse.click(strategy.x, strategy.y)
                    return
                except Exception as exc:
                    errors.append(str(exc))
                    continue
            try:
                locator = self._locator_for(root, strategy)
                if await locator.count() > 0:
                    await locator.first.click(timeout=action.timeout_ms)
                    return
            except Exception as exc:
                errors.append(str(exc))
        raise LookupError(self._not_found_message(action.target, errors))

    async def _resolve(self, target: Target) -> _Locator:
        root = self._root_for(target)
        errors: list[str] = []
        for strategy in target.strategies:
            if isinstance(strategy, CoordinateLocator):
                continue
            try:
                locator = self._locator_for(root, strategy)
                if await locator.count() > 0:
                    return locator.first
            except Exception as exc:
                errors.append(str(exc))
        raise LookupError(self._not_found_message(target, errors))

    def _root_for(self, target: Target) -> _BrowserRoot:
        if target.context is None:
            return self._page
        frame = self._page.frame(name=target.context.name)
        if frame is None:
            raise LookupError(f"Embedded surface not found: {target.context.name}")
        return frame

    @staticmethod
    def _locator_for(root: _BrowserRoot, strategy: LocatorStrategy) -> _Locator:
        if isinstance(strategy, LabelLocator):
            return root.get_by_label(strategy.value, exact=strategy.exact)
        if isinstance(strategy, RoleLocator):
            return root.get_by_role(
                strategy.role,
                name=strategy.name,
                exact=strategy.exact,
            )
        if isinstance(strategy, TextLocator):
            return root.get_by_text(strategy.value, exact=strategy.exact)
        if isinstance(strategy, TextProximityLocator):
            anchor = root.get_by_text(strategy.anchor, exact=False)
            container = anchor.locator(
                "xpath=ancestor::*[self::tr or self::form or self::section or self::div][1]"
            )
            if strategy.element_role:
                return container.get_by_role(strategy.element_role)
            return container.locator("input,button,select,a")
        if isinstance(strategy, StructuralLocator):
            container = root.get_by_text(strategy.container_text, exact=False).locator(
                "xpath=ancestor::*[self::tr or self::form or self::section or self::div][1]"
            )
            return container.get_by_role(
                strategy.descendant_role,
                name=strategy.descendant_name,
            )
        if isinstance(strategy, CssLocator):
            return root.locator(strategy.value)
        raise TypeError(f"Unsupported locator strategy: {type(strategy).__name__}")

    @staticmethod
    async def _assert(locator: _Locator, action: AssertAction) -> None:
        if action.condition is AssertionCondition.VISIBLE:
            matched = await locator.is_visible()
        elif action.condition is AssertionCondition.HIDDEN:
            matched = not await locator.is_visible()
        else:
            actual = await locator.inner_text(timeout=action.timeout_ms)
            if action.condition is AssertionCondition.TEXT_EQUALS:
                matched = actual == action.expected
            else:
                matched = action.expected in actual if action.expected is not None else False
        if not matched:
            raise AssertionError(
                f"Assertion {action.condition.value} failed for {action.target.semantic_name}"
            )

    @staticmethod
    def _not_found_message(target: Target, errors: list[str]) -> str:
        detail = f" ({'; '.join(errors)})" if errors else ""
        return f"No locator matched target: {target.semantic_name}{detail}"

    @staticmethod
    def _element_candidate(item: Mapping[str, Any]) -> ElementCandidate:
        tag = str(item.get("tag") or "element")
        role = str(item.get("role") or tag)
        name = str(item.get("name") or "").strip()
        text = str(item.get("text") or "").strip()
        label = str(item.get("label") or "").strip()
        field_name = str(item.get("fieldName") or "").strip()
        semantic_name = label or name or text or field_name or role
        strategies: list[LocatorStrategy] = []
        if label:
            strategies.append(LabelLocator(value=label))
        if role:
            strategies.append(RoleLocator(role=role, name=name or text or None))
        if text and tag in {"a", "button"}:
            strategies.append(TextLocator(value=text))
        if field_name:
            escaped_name = field_name.replace("\\", "\\\\").replace('"', '\\"')
            strategies.append(CssLocator(value=f'{tag}[name="{escaped_name}"]'))
        return ElementCandidate(
            semantic_name=semantic_name,
            role=role,
            name=name or None,
            text=text or None,
            enabled=bool(item.get("enabled", True)),
            visible=bool(item.get("visible", True)),
            target=Target(semantic_name=semantic_name, strategies=tuple(strategies)),
            metadata={"tag": tag},
        )


_ELEMENT_SNAPSHOT_SCRIPT = """
(elements) => elements.map((element) => {
  const tag = element.tagName.toLowerCase();
  const implicitRoles = {
    a: 'link', button: 'button', select: 'combobox', textarea: 'textbox'
  };
  let role = element.getAttribute('role') || implicitRoles[tag] || tag;
  if (tag === 'input') {
    const type = (element.getAttribute('type') || 'text').toLowerCase();
    role = ['button', 'submit', 'reset'].includes(type) ? 'button' : 'textbox';
  }
  const label = element.labels && element.labels.length
    ? element.labels[0].innerText.trim()
    : (element.getAttribute('aria-label') || '').trim();
  const text = (element.innerText || element.value || '').trim();
  const name = (element.getAttribute('aria-label') || label || text).trim();
  return {
    tag,
    role,
    name,
    label,
    text,
    fieldName: element.getAttribute('name') || '',
    enabled: !element.disabled,
    visible: Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length),
  };
})
"""
