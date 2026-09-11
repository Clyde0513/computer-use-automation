"""Framework-independent surface adapter boundary."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import Action, ActionResult, Evidence, Observation, SessionReference


@runtime_checkable
class SurfaceAdapter(Protocol):
    async def observe(self) -> Observation: ...

    async def execute(self, action: Action) -> ActionResult: ...

    async def capture_evidence(self) -> Evidence: ...

    async def get_session_reference(self) -> SessionReference: ...
