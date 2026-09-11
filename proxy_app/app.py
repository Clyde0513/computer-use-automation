"""Dependency-free WSGI application for the synthetic servicing proxy."""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from io import BytesIO
from typing import Any
from urllib.parse import parse_qs

from .data import MEMBERS, Member
from .pages import (
    checking_page,
    error_page,
    member_detail_page,
    savings_frame_page,
    savings_shell_page,
    search_page,
    simulated_confirmation_page,
    subaccount_form_page,
    subaccount_review_page,
    transient_failure_page,
)

StartResponse = Callable[[str, list[tuple[str, str]]], Any]


@dataclass(frozen=True, slots=True)
class Response:
    body: bytes
    status: str = "200 OK"
    content_type: str = "text/html; charset=utf-8"
    extra_headers: tuple[tuple[str, str], ...] = ()

    @classmethod
    def html(cls, content: str, status: str = "200 OK") -> Response:
        return cls(content.encode("utf-8"), status=status)

    @classmethod
    def redirect(cls, location: str) -> Response:
        return cls(
            b"",
            status="303 See Other",
            extra_headers=(("Location", location),),
        )

    def send(self, start_response: StartResponse) -> Iterable[bytes]:
        headers = [
            ("Content-Type", self.content_type),
            ("Content-Length", str(len(self.body))),
            ("Cache-Control", "no-store"),
            *self.extra_headers,
        ]
        start_response(self.status, headers)
        return [self.body]


class ProxyApplication:
    """Small server-rendered application with deterministic failure scenarios."""

    _member_pattern = re.compile(r"^/members/(?P<member_id>\d{5})$")
    _account_pattern = re.compile(
        r"^/members/(?P<member_id>\d{5})/accounts/(?P<account_type>savings|checking)$"
    )
    _savings_frame_pattern = re.compile(r"^/members/(?P<member_id>\d{5})/savings/frame$")
    _subaccount_new_pattern = re.compile(r"^/members/(?P<member_id>\d{5})/subaccounts/new$")
    _subaccount_confirm_pattern = re.compile(r"^/members/(?P<member_id>\d{5})/subaccounts/confirm$")

    def __call__(
        self, environ: Mapping[str, Any], start_response: StartResponse
    ) -> Iterable[bytes]:
        try:
            response = self.dispatch(environ)
        except Exception:
            response = Response.html(
                error_page(
                    "INTERNAL_ERROR",
                    "The local proxy encountered an unexpected error.",
                ),
                "500 Internal Server Error",
            )
        return response.send(start_response)

    def dispatch(self, environ: Mapping[str, Any]) -> Response:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        query = _parse_values(str(environ.get("QUERY_STRING", "")))

        if path == "/static/legacy.css" and method == "GET":
            css = files("proxy_app").joinpath("static", "legacy.css").read_bytes()
            return Response(css, content_type="text/css; charset=utf-8")

        if query.get("scenario", "").upper() == "SESSION_EXPIRED":
            return Response.html(
                error_page(
                    "SESSION_EXPIRED",
                    "The simulated servicing session expired. Return to member search to begin again.",
                ),
                "401 Unauthorized",
            )

        if path == "/" and method == "GET":
            return Response.html(search_page())
        if path == "/members/search" and method == "GET":
            return self._search(query)

        if match := self._member_pattern.fullmatch(path):
            return self._member_detail(method, match.group("member_id"), query)
        if match := self._account_pattern.fullmatch(path):
            return self._account(
                method, match.group("member_id"), match.group("account_type"), query
            )
        if match := self._savings_frame_pattern.fullmatch(path):
            return self._savings_frame(method, match.group("member_id"), query)
        if match := self._subaccount_new_pattern.fullmatch(path):
            return self._subaccount_new(method, match.group("member_id"), environ)
        if match := self._subaccount_confirm_pattern.fullmatch(path):
            return self._subaccount_confirm(method, match.group("member_id"), environ)

        if path.startswith("/members/"):
            return Response.html(
                error_page(
                    "MEMBER_NOT_FOUND", "The requested member or account route does not exist."
                ),
                "404 Not Found",
            )
        return Response.html(
            error_page("PAGE_NOT_FOUND", "The requested page does not exist."), "404 Not Found"
        )

    def _search(self, query: dict[str, str]) -> Response:
        member_id = query.get("member_id", "").strip()
        if not re.fullmatch(r"\d{5}", member_id):
            return Response.html(
                error_page("VALIDATION_ERROR", "Member Number must contain exactly five digits."),
                "400 Bad Request",
            )
        if member_id not in MEMBERS:
            return Response.html(
                error_page("MEMBER_NOT_FOUND", f"No synthetic member matched {member_id}."),
                "404 Not Found",
            )
        return Response.redirect(f"/members/{member_id}")

    def _member_detail(self, method: str, member_id: str, query: dict[str, str]) -> Response:
        if method != "GET":
            return self._method_not_allowed()
        member_or_error = self._allowed_member(member_id)
        if isinstance(member_or_error, Response):
            return member_or_error
        show_dialog = query.get("scenario", "").upper() == "UNEXPECTED_DIALOG"
        return Response.html(member_detail_page(member_or_error, show_dialog))

    def _account(
        self,
        method: str,
        member_id: str,
        account_type: str,
        query: dict[str, str],
    ) -> Response:
        if method != "GET":
            return self._method_not_allowed()
        member_or_error = self._allowed_member(member_id)
        if isinstance(member_or_error, Response):
            return member_or_error
        member = member_or_error
        account = member.account(account_type.title())
        if account is None:
            return Response.html(
                error_page("ACCOUNT_NOT_FOUND", "The requested synthetic account does not exist."),
                "404 Not Found",
            )
        if account_type == "checking":
            return Response.html(checking_page(member, account))
        if (
            query.get("scenario", "").upper() == "TRANSIENT_LOAD_FAILURE"
            and query.get("attempt", "1") != "2"
        ):
            return Response.html(transient_failure_page(member_id), "503 Service Unavailable")
        delay_ms = _bounded_delay(query.get("delay_ms"), default=350)
        return Response.html(savings_shell_page(member, delay_ms))

    def _savings_frame(self, method: str, member_id: str, query: dict[str, str]) -> Response:
        if method != "GET":
            return self._method_not_allowed()
        member_or_error = self._allowed_member(member_id)
        if isinstance(member_or_error, Response):
            return member_or_error
        member = member_or_error
        account = member.account("Savings")
        if account is None:
            return Response.html(
                error_page("ACCOUNT_NOT_FOUND", "The member has no synthetic savings account."),
                "404 Not Found",
            )
        time.sleep(_bounded_delay(query.get("delay_ms"), default=350) / 1000)
        return Response.html(savings_frame_page(member, account))

    def _subaccount_new(self, method: str, member_id: str, environ: Mapping[str, Any]) -> Response:
        member_or_error = self._allowed_member(member_id)
        if isinstance(member_or_error, Response):
            return member_or_error
        member = member_or_error
        if method == "GET":
            return Response.html(subaccount_form_page(member))
        if method != "POST":
            return self._method_not_allowed()

        values = _read_form(environ)
        product = values.get("product", "").strip()
        nickname = values.get("nickname", "").strip()
        deposit_text = values.get("opening_deposit", "").strip()
        errors, deposit = _validate_subaccount(product, nickname, deposit_text)
        if errors or deposit is None:
            return Response.html(
                subaccount_form_page(member, tuple(errors), values),
                "422 Unprocessable Entity",
            )
        return Response.html(subaccount_review_page(member, product, nickname, deposit))

    def _subaccount_confirm(
        self, method: str, member_id: str, environ: Mapping[str, Any]
    ) -> Response:
        if method != "POST":
            return self._method_not_allowed()
        member_or_error = self._allowed_member(member_id)
        if isinstance(member_or_error, Response):
            return member_or_error
        values = _read_form(environ)
        if values.get("authorization", "") != "PERMIT":
            return Response.html(
                error_page(
                    "CONFIRMATION_REQUIRED",
                    "No simulated action was taken. Explicit authorization is required.",
                    f"/members/{member_id}",
                ),
                "409 Conflict",
            )
        return Response.html(simulated_confirmation_page(member_or_error))

    def _allowed_member(self, member_id: str) -> Member | Response:
        member = MEMBERS.get(member_id)
        if member is None:
            return Response.html(
                error_page("MEMBER_NOT_FOUND", f"No synthetic member matched {member_id}."),
                "404 Not Found",
            )
        if not member.access_allowed:
            return Response.html(
                error_page(
                    "PERMISSION_DENIED",
                    "This synthetic record is restricted for the current simulated operator.",
                ),
                "403 Forbidden",
            )
        return member

    @staticmethod
    def _method_not_allowed() -> Response:
        return Response.html(
            error_page("METHOD_NOT_ALLOWED", "That operation is not supported."),
            "405 Method Not Allowed",
        )


def _parse_values(encoded: str) -> dict[str, str]:
    return {key: values[-1] for key, values in parse_qs(encoded, keep_blank_values=True).items()}


def _read_form(environ: Mapping[str, Any]) -> dict[str, str]:
    try:
        length = int(str(environ.get("CONTENT_LENGTH", "0") or "0"))
    except ValueError:
        length = 0
    stream = environ.get("wsgi.input", BytesIO())
    body = stream.read(length) if hasattr(stream, "read") else b""
    return _parse_values(body.decode("utf-8", errors="replace"))


def _bounded_delay(raw_value: str | None, default: int) -> int:
    try:
        value = int(raw_value) if raw_value is not None else default
    except ValueError:
        value = default
    return max(0, min(value, 1500))


def _validate_subaccount(
    product: str,
    nickname: str,
    deposit_text: str,
) -> tuple[list[str], Decimal | None]:
    errors: list[str] = []
    if product not in {"Holiday Savings", "Special Savings"}:
        errors.append("Select an available product.")
    if not nickname or len(nickname) > 30:
        errors.append("Nickname is required and must be 30 characters or fewer.")
    try:
        deposit = Decimal(deposit_text)
    except InvalidOperation:
        errors.append("Opening Deposit must be a number.")
        return errors, None
    if not deposit.is_finite():
        errors.append("Opening Deposit must be a finite number.")
        return errors, deposit
    if deposit < 0 or deposit > Decimal("100000"):
        errors.append("Opening Deposit must be between 0 and 100000.")
    exponent = deposit.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        errors.append("Opening Deposit may have at most two decimal places.")
    return errors, deposit


application = ProxyApplication()
