from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pytest

from cua.surfaces.base import SurfaceAdapter
from cua.surfaces.browser import BrowserSurfaceAdapter
from cua.surfaces.models import (
    ActionStatus,
    AssertAction,
    AssertionCondition,
    ClickAction,
    CssLocator,
    EvidenceEncoding,
    LabelLocator,
    NavigateAction,
    ReadAction,
    ReadProperty,
    SelectAction,
    Target,
    TypeAction,
    WaitAction,
    WaitState,
)


class FakeLocator:
    def __init__(
        self,
        *,
        count: int = 1,
        text: str = "",
        value: str = "",
        visible: bool = True,
        elements: list[dict[str, Any]] | None = None,
    ) -> None:
        self._count = count
        self._text = text
        self._value = value
        self._visible = visible
        self._elements = elements or []
        self.calls: list[tuple[str, Any]] = []
        self.first = self

    async def count(self) -> int:
        return self._count

    async def click(self, **kwargs: Any) -> None:
        self.calls.append(("click", kwargs))

    async def fill(self, value: str, **kwargs: Any) -> None:
        self._value = value
        self.calls.append(("fill", value))

    async def type(self, value: str, **kwargs: Any) -> None:
        self._value += value
        self.calls.append(("type", value))

    async def select_option(self, value: str, **kwargs: Any) -> None:
        self._value = value
        self.calls.append(("select_option", value))

    async def inner_text(self, **kwargs: Any) -> str:
        return self._text

    async def input_value(self, **kwargs: Any) -> str:
        return self._value

    async def get_attribute(self, name: str, **kwargs: Any) -> str | None:
        return {"data-code": "A1"}.get(name)

    async def is_visible(self) -> bool:
        return self._visible

    async def wait_for(self, **kwargs: Any) -> None:
        self.calls.append(("wait_for", kwargs))

    async def evaluate_all(self, script: str) -> list[dict[str, Any]]:
        assert "elements.map" in script
        return self._elements

    def locator(self, selector: str) -> FakeLocator:
        self.calls.append(("locator", selector))
        return self

    def get_by_role(self, role: str, **kwargs: Any) -> FakeLocator:
        self.calls.append(("get_by_role", (role, kwargs)))
        return self


class FakeMouse:
    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []

    async def click(self, x: float, y: float) -> None:
        self.clicks.append((x, y))


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.mouse = FakeMouse()
        self.waits: list[int] = []
        self.body = FakeLocator(text="Member Search")
        self.element_list = FakeLocator(
            elements=[
                {
                    "tag": "input",
                    "role": "textbox",
                    "name": "Member Number",
                    "label": "Member Number",
                    "text": "",
                    "fieldName": "member_id",
                    "enabled": True,
                    "visible": True,
                }
            ]
        )
        self.labels: dict[str, FakeLocator] = {}
        self.roles: dict[tuple[str, str | None], FakeLocator] = {}
        self.texts: dict[str, FakeLocator] = {}
        self.css: dict[str, FakeLocator] = {}
        self.frames: dict[str, FakePage] = {}

    async def title(self) -> str:
        return "Synthetic page"

    async def goto(self, destination: str, **kwargs: Any) -> None:
        self.url = destination

    async def wait_for_timeout(self, duration_ms: int) -> None:
        self.waits.append(duration_ms)

    async def screenshot(self, **kwargs: Any) -> bytes:
        assert kwargs == {"full_page": True}
        return b"fake-png"

    def locator(self, selector: str) -> FakeLocator:
        if selector == "body":
            return self.body
        if selector == "a,button,input,select,textarea,[role]":
            return self.element_list
        return self.css.get(selector, FakeLocator(count=0))

    def get_by_label(self, value: str, **kwargs: Any) -> FakeLocator:
        return self.labels.get(value, FakeLocator(count=0))

    def get_by_role(self, role: str, **kwargs: Any) -> FakeLocator:
        return self.roles.get((role, kwargs.get("name")), FakeLocator(count=0))

    def get_by_text(self, value: str, **kwargs: Any) -> FakeLocator:
        return self.texts.get(value, FakeLocator(count=0))

    def frame(self, *, name: str) -> FakePage | None:
        return self.frames.get(name)


def target(*strategies: Any) -> Target:
    return Target(semantic_name="Test target", strategies=strategies)


@pytest.mark.asyncio
async def test_browser_adapter_implements_surface_protocol_and_observes() -> None:
    page = FakePage()
    adapter = BrowserSurfaceAdapter(page)

    assert isinstance(adapter, SurfaceAdapter)
    observation = await adapter.observe()

    assert observation.title == "Synthetic page"
    assert observation.visible_text == "Member Search"
    assert observation.metadata["adapter"] == "playwright"
    assert len(observation.elements) == 1
    assert len(observation.elements[0].target.strategies) == 3


@pytest.mark.asyncio
async def test_locator_candidates_fall_back_in_declared_order() -> None:
    page = FakePage()
    css_locator = FakeLocator()
    page.labels["Missing label"] = FakeLocator(count=0)
    page.css["button.search"] = css_locator
    adapter = BrowserSurfaceAdapter(page)

    result = await adapter.execute(
        ClickAction(
            target=target(
                LabelLocator(value="Missing label"),
                CssLocator(value="button.search"),
            )
        )
    )

    assert result.status is ActionStatus.SUCCEEDED
    assert css_locator.calls[0][0] == "click"


@pytest.mark.asyncio
async def test_browser_adapter_executes_all_normalized_action_shapes() -> None:
    page = FakePage()
    locator = FakeLocator(text="Current Balance", value="initial")
    page.css[".target"] = locator
    adapter = BrowserSurfaceAdapter(page)
    selected_target = target(CssLocator(value=".target"))

    navigate = await adapter.execute(NavigateAction(destination="http://example.test/"))
    typed = await adapter.execute(TypeAction(target=selected_target, text="10001"))
    selected = await adapter.execute(SelectAction(target=selected_target, value="Savings"))
    read = await adapter.execute(ReadAction(target=selected_target))
    value = await adapter.execute(ReadAction(target=selected_target, property=ReadProperty.VALUE))
    attribute = await adapter.execute(
        ReadAction(
            target=selected_target,
            property=ReadProperty.ATTRIBUTE,
            attribute_name="data-code",
        )
    )
    waited = await adapter.execute(WaitAction(duration_ms=25))
    waited_for_target = await adapter.execute(
        WaitAction(target=selected_target, state=WaitState.VISIBLE)
    )
    asserted = await adapter.execute(
        AssertAction(
            target=selected_target,
            condition=AssertionCondition.TEXT_CONTAINS,
            expected="Balance",
        )
    )

    assert all(
        result.status is ActionStatus.SUCCEEDED
        for result in (
            navigate,
            typed,
            selected,
            read,
            value,
            attribute,
            waited,
            waited_for_target,
            asserted,
        )
    )
    assert navigate.value == "http://example.test/"
    assert read.value == "Current Balance"
    assert value.value == "Savings"
    assert attribute.value == "A1"
    assert page.waits == [25]


@pytest.mark.asyncio
async def test_assertion_and_missing_target_return_structured_failures() -> None:
    page = FakePage()
    page.css[".hidden"] = FakeLocator(text="wrong", visible=False)
    adapter = BrowserSurfaceAdapter(page)

    assertion = await adapter.execute(
        AssertAction(
            target=target(CssLocator(value=".hidden")),
            condition=AssertionCondition.VISIBLE,
        )
    )
    missing = await adapter.execute(ReadAction(target=target(CssLocator(value=".missing"))))

    assert assertion.status is ActionStatus.FAILED
    assert assertion.error is not None
    assert assertion.error.code == "ASSERTIONERROR"
    assert missing.status is ActionStatus.FAILED
    assert missing.error is not None
    assert "No locator matched target" in missing.error.message


@pytest.mark.asyncio
async def test_capture_evidence_returns_serializable_png() -> None:
    adapter = BrowserSurfaceAdapter(FakePage())

    evidence = await adapter.capture_evidence()

    assert evidence.encoding is EvidenceEncoding.BASE64
    assert base64.b64decode(evidence.content) == b"fake-png"
    assert evidence.model_validate_json(evidence.model_dump_json()) == evidence


def test_playwright_reference_is_confined_to_browser_adapter() -> None:
    source_root = Path(__file__).parents[1] / "src" / "cua"
    offenders = []
    for path in source_root.rglob("*.py"):
        if path.name == "browser.py":
            continue
        if "playwright" in path.read_text(encoding="utf-8").lower():
            offenders.append(path.relative_to(source_root).as_posix())
    assert offenders == []
