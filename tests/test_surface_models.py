from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from cua.surfaces.models import (
    Action,
    ActionKind,
    ActionResult,
    ActionStatus,
    ClickAction,
    CssLocator,
    LabelLocator,
    LocatorKind,
    RoleLocator,
    SessionReference,
    StructuralLocator,
    SurfaceKind,
    Target,
)


def test_action_union_round_trips_with_ordered_locator_candidates() -> None:
    action = ClickAction(
        target=Target(
            semantic_name="Member ID input",
            strategies=(
                LabelLocator(value="Member ID"),
                RoleLocator(role="textbox", name="Member ID"),
                StructuralLocator(
                    container_text="Member Search",
                    descendant_role="textbox",
                ),
                CssLocator(value="input[name='memberId']"),
            ),
        )
    )
    adapter = TypeAdapter(Action)

    restored = adapter.validate_json(adapter.dump_json(action))

    assert isinstance(restored, ClickAction)
    assert [strategy.kind for strategy in restored.target.strategies] == [
        LocatorKind.LABEL,
        LocatorKind.ROLE,
        LocatorKind.STRUCTURAL,
        LocatorKind.CSS,
    ]


def test_target_requires_at_least_one_locator_candidate() -> None:
    with pytest.raises(ValidationError):
        Target(semantic_name="Unlocatable", strategies=())


def test_only_prd_02_action_types_are_available() -> None:
    assert {kind.value for kind in ActionKind} == {
        "click",
        "type",
        "select",
        "navigate",
        "read",
        "wait",
        "assert",
    }


def test_failed_action_result_requires_structured_error() -> None:
    now = datetime.now(UTC)
    action = ClickAction(
        target=Target(
            semantic_name="Search",
            strategies=(RoleLocator(role="button", name="Search"),),
        )
    )
    with pytest.raises(ValidationError):
        ActionResult(
            action_id=action.action_id,
            status=ActionStatus.FAILED,
            started_at=now,
            completed_at=now,
        )


def test_session_contract_is_surface_extensible() -> None:
    browser = SessionReference(surface_kind=SurfaceKind.BROWSER, adapter_name="browser")
    accessibility = SessionReference(
        surface_kind=SurfaceKind.ACCESSIBILITY,
        adapter_name="future-accessibility-adapter",
    )
    desktop = SessionReference(
        surface_kind=SurfaceKind.DESKTOP,
        adapter_name="future-desktop-adapter",
    )

    assert len({browser.surface_kind, accessibility.surface_kind, desktop.surface_kind}) == 3
