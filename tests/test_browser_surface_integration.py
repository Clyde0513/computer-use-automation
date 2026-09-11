from __future__ import annotations

import os
import threading
from contextlib import suppress
from wsgiref.simple_server import WSGIServer, make_server

import pytest

from cua.surfaces.browser import BrowserSurfaceAdapter
from cua.surfaces.models import (
    ActionStatus,
    ClickAction,
    CssLocator,
    EvidenceKind,
    LabelLocator,
    NavigateAction,
    ReadAction,
    RoleLocator,
    SurfaceContext,
    Target,
    TypeAction,
)
from proxy_app.app import application

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_BROWSER_TESTS") != "1",
    reason="set RUN_BROWSER_TESTS=1 after installing Chromium",
)


@pytest.fixture
def proxy_server() -> str:
    server: WSGIServer = make_server("127.0.0.1", 0, application)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.mark.asyncio
async def test_real_browser_adapter_drives_proxy_workflow(proxy_server: str) -> None:
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    try:
        page = await browser.new_page()
        adapter = BrowserSurfaceAdapter(page)

        navigation = await adapter.execute(NavigateAction(destination=proxy_server))
        member_id = Target(
            semantic_name="Member Number",
            strategies=(
                LabelLocator(value="Member Number"),
                CssLocator(value='input[name="member_id"]'),
            ),
        )
        typed = await adapter.execute(TypeAction(target=member_id, text="10001"))
        searched = await adapter.execute(
            ClickAction(
                target=Target(
                    semantic_name="Search",
                    strategies=(RoleLocator(role="button", name="Search"),),
                )
            )
        )
        await page.wait_for_url("**/members/10001")
        opened = await adapter.execute(
            ClickAction(
                target=Target(
                    semantic_name="Savings Open button",
                    strategies=(CssLocator(value=".account-grid tr:nth-child(2) button"),),
                )
            )
        )
        await page.wait_for_url("**/accounts/savings?")
        balance = await adapter.execute(
            ReadAction(
                target=Target(
                    semantic_name="Current savings balance",
                    context=SurfaceContext(name="account-pane"),
                    strategies=(CssLocator(value='[data-field="current-balance"]'),),
                )
            )
        )
        observation = await adapter.observe()
        evidence = await adapter.capture_evidence()

        assert all(
            result.status is ActionStatus.SUCCEEDED
            for result in (navigation, typed, searched, opened, balance)
        )
        assert balance.value == "$1,245.67"
        assert observation.location is not None
        assert observation.location.endswith("/accounts/savings?")
        assert evidence.kind is EvidenceKind.SCREENSHOT
        assert evidence.content
    finally:
        with suppress(Exception):
            await browser.close()
        await playwright.stop()
