"""Typed, serializable contracts shared by every surface implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class ContractModel(BaseModel):
    """Strict immutable base for values crossing the surface boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SurfaceKind(StrEnum):
    BROWSER = "browser"
    ACCESSIBILITY = "accessibility"
    DESKTOP = "desktop"


class SessionOwner(StrEnum):
    AUTOMATION = "automation"
    HUMAN = "human"


class SessionReference(ContractModel):
    session_id: UUID = Field(default_factory=uuid4)
    surface_kind: SurfaceKind
    adapter_name: str = Field(min_length=1)
    owner: SessionOwner = SessionOwner.AUTOMATION
    location: str | None = None


class LocatorKind(StrEnum):
    LABEL = "label"
    ROLE = "role"
    TEXT = "text"
    TEXT_PROXIMITY = "text_proximity"
    STRUCTURAL = "structural"
    CSS = "css"
    COORDINATE = "coordinate"


class LabelLocator(ContractModel):
    kind: Literal[LocatorKind.LABEL] = LocatorKind.LABEL
    value: str = Field(min_length=1)
    exact: bool = True


class RoleLocator(ContractModel):
    kind: Literal[LocatorKind.ROLE] = LocatorKind.ROLE
    role: str = Field(min_length=1)
    name: str | None = None
    exact: bool = True


class TextLocator(ContractModel):
    kind: Literal[LocatorKind.TEXT] = LocatorKind.TEXT
    value: str = Field(min_length=1)
    exact: bool = True


class TextProximityLocator(ContractModel):
    kind: Literal[LocatorKind.TEXT_PROXIMITY] = LocatorKind.TEXT_PROXIMITY
    anchor: str = Field(min_length=1)
    element_role: str | None = None


class StructuralLocator(ContractModel):
    kind: Literal[LocatorKind.STRUCTURAL] = LocatorKind.STRUCTURAL
    container_text: str = Field(min_length=1)
    descendant_role: str = Field(min_length=1)
    descendant_name: str | None = None


class CssLocator(ContractModel):
    kind: Literal[LocatorKind.CSS] = LocatorKind.CSS
    value: str = Field(min_length=1)


class CoordinateLocator(ContractModel):
    kind: Literal[LocatorKind.COORDINATE] = LocatorKind.COORDINATE
    x: float = Field(ge=0)
    y: float = Field(ge=0)


LocatorStrategy = Annotated[
    LabelLocator
    | RoleLocator
    | TextLocator
    | TextProximityLocator
    | StructuralLocator
    | CssLocator
    | CoordinateLocator,
    Field(discriminator="kind"),
]


class SurfaceContext(ContractModel):
    """A named child surface, such as a browser frame or accessibility pane."""

    name: str = Field(min_length=1)


class Target(ContractModel):
    semantic_name: str = Field(min_length=1)
    strategies: tuple[LocatorStrategy, ...] = Field(min_length=1)
    context: SurfaceContext | None = None


class ElementCandidate(ContractModel):
    candidate_id: UUID = Field(default_factory=uuid4)
    semantic_name: str = Field(min_length=1)
    role: str | None = None
    name: str | None = None
    text: str | None = None
    enabled: bool = True
    visible: bool = True
    target: Target
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class Observation(ContractModel):
    observation_id: UUID = Field(default_factory=uuid4)
    captured_at: datetime = Field(default_factory=utc_now)
    session: SessionReference
    location: str | None = None
    title: str | None = None
    visible_text: str = ""
    elements: tuple[ElementCandidate, ...] = ()
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class ActionKind(StrEnum):
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    NAVIGATE = "navigate"
    READ = "read"
    WAIT = "wait"
    ASSERT = "assert"


class ActionBase(ContractModel):
    action_id: UUID = Field(default_factory=uuid4)
    timeout_ms: int = Field(default=10_000, gt=0, le=120_000)


class ClickAction(ActionBase):
    kind: Literal[ActionKind.CLICK] = ActionKind.CLICK
    target: Target


class TypeAction(ActionBase):
    kind: Literal[ActionKind.TYPE] = ActionKind.TYPE
    target: Target
    text: str
    clear_first: bool = True


class SelectAction(ActionBase):
    kind: Literal[ActionKind.SELECT] = ActionKind.SELECT
    target: Target
    value: str


class NavigateAction(ActionBase):
    kind: Literal[ActionKind.NAVIGATE] = ActionKind.NAVIGATE
    destination: str = Field(min_length=1)


class ReadProperty(StrEnum):
    TEXT = "text"
    VALUE = "value"
    ATTRIBUTE = "attribute"


class ReadAction(ActionBase):
    kind: Literal[ActionKind.READ] = ActionKind.READ
    target: Target
    property: ReadProperty = ReadProperty.TEXT
    attribute_name: str | None = None

    @model_validator(mode="after")
    def validate_attribute(self) -> ReadAction:
        if self.property is ReadProperty.ATTRIBUTE and not self.attribute_name:
            raise ValueError("attribute_name is required when reading an attribute")
        return self


class WaitState(StrEnum):
    ATTACHED = "attached"
    DETACHED = "detached"
    VISIBLE = "visible"
    HIDDEN = "hidden"


class WaitAction(ActionBase):
    kind: Literal[ActionKind.WAIT] = ActionKind.WAIT
    duration_ms: int | None = Field(default=None, ge=0, le=120_000)
    target: Target | None = None
    state: WaitState | None = None

    @model_validator(mode="after")
    def validate_wait_mode(self) -> WaitAction:
        duration_mode = self.duration_ms is not None
        target_mode = self.target is not None and self.state is not None
        if duration_mode == target_mode:
            raise ValueError("provide either duration_ms or both target and state")
        return self


class AssertionCondition(StrEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    TEXT_EQUALS = "text_equals"
    TEXT_CONTAINS = "text_contains"


class AssertAction(ActionBase):
    kind: Literal[ActionKind.ASSERT] = ActionKind.ASSERT
    target: Target
    condition: AssertionCondition
    expected: str | None = None

    @model_validator(mode="after")
    def validate_expected_value(self) -> AssertAction:
        needs_value = self.condition in {
            AssertionCondition.TEXT_EQUALS,
            AssertionCondition.TEXT_CONTAINS,
        }
        if needs_value and self.expected is None:
            raise ValueError("expected is required for text assertions")
        return self


Action = Annotated[
    ClickAction
    | TypeAction
    | SelectAction
    | NavigateAction
    | ReadAction
    | WaitAction
    | AssertAction,
    Field(discriminator="kind"),
]


class ActionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SurfaceError(ContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool = False


class ActionResult(ContractModel):
    action_id: UUID
    status: ActionStatus
    started_at: datetime
    completed_at: datetime
    value: JsonValue | None = None
    error: SurfaceError | None = None

    @model_validator(mode="after")
    def validate_result_shape(self) -> ActionResult:
        if self.status is ActionStatus.SUCCEEDED and self.error is not None:
            raise ValueError("successful actions cannot contain an error")
        if self.status is ActionStatus.FAILED and self.error is None:
            raise ValueError("failed actions must contain an error")
        return self


class EvidenceKind(StrEnum):
    SCREENSHOT = "screenshot"
    DOM_SNAPSHOT = "dom_snapshot"
    ACCESSIBILITY_SNAPSHOT = "accessibility_snapshot"
    SURFACE_SNAPSHOT = "surface_snapshot"


class EvidenceEncoding(StrEnum):
    BASE64 = "base64"
    TEXT = "text"


class Evidence(ContractModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    captured_at: datetime = Field(default_factory=utc_now)
    session: SessionReference
    kind: EvidenceKind
    media_type: str = Field(min_length=1)
    encoding: EvidenceEncoding
    content: str
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
