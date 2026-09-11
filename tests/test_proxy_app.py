from __future__ import annotations

import unittest
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlencode, urlsplit
from wsgiref.util import setup_testing_defaults

from proxy_app.app import application
from proxy_app.data import MEMBERS


@dataclass(frozen=True)
class WsgiResponse:
    status: str
    headers: dict[str, str]
    text: str


def request(path: str, method: str = "GET", form: dict[str, str] | None = None) -> WsgiResponse:
    parsed = urlsplit(path)
    environ: dict[str, object] = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = parsed.path
    environ["QUERY_STRING"] = parsed.query
    encoded_form = urlencode(form or {}).encode("utf-8")
    environ["wsgi.input"] = BytesIO(encoded_form)
    environ["CONTENT_LENGTH"] = str(len(encoded_form))
    environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"
    captured: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    result = application(environ, start_response)
    try:
        body = b"".join(result)
    finally:
        close = getattr(result, "close", None)
        if close is not None:
            close()
    return WsgiResponse(
        status=str(captured["status"]),
        headers=dict(captured["headers"]),
        text=body.decode("utf-8"),
    )


class ProxyApplicationTests(unittest.TestCase):
    def test_successful_member_search_and_savings_balance_workflow(self) -> None:
        search = request("/members/search?member_id=10001")
        self.assertEqual("303 See Other", search.status)
        self.assertEqual("/members/10001", search.headers["Location"])

        detail = request(search.headers["Location"])
        self.assertEqual("200 OK", detail.status)
        self.assertIn("Avery Example", detail.text)
        self.assertIn("Savings", detail.text)

        savings = request("/members/10001/accounts/savings?delay_ms=0")
        self.assertEqual("200 OK", savings.status)
        self.assertIn("<iframe", savings.text)
        self.assertIn("Savings account balance", savings.text)

        frame = request("/members/10001/savings/frame?delay_ms=0")
        self.assertEqual("200 OK", frame.status)
        self.assertIn("Current Balance", frame.text)
        self.assertIn("$1,245.67", frame.text)

    def test_member_not_found_is_deterministic(self) -> None:
        response = request("/members/search?member_id=99999")
        self.assertEqual("404 Not Found", response.status)
        self.assertIn("MEMBER_NOT_FOUND", response.text)

    def test_invalid_member_id_returns_validation_error(self) -> None:
        for member_id in ("", "ABC", "1000", "100011"):
            with self.subTest(member_id=member_id):
                response = request(f"/members/search?member_id={member_id}")
                self.assertEqual("400 Bad Request", response.status)
                self.assertIn("VALIDATION_ERROR", response.text)

    def test_restricted_seed_member_returns_permission_denied(self) -> None:
        response = request("/members/10003")
        self.assertEqual("403 Forbidden", response.status)
        self.assertIn("PERMISSION_DENIED", response.text)

    def test_session_expiry_can_be_simulated(self) -> None:
        response = request("/members/10001?scenario=SESSION_EXPIRED")
        self.assertEqual("401 Unauthorized", response.status)
        self.assertIn("SESSION_EXPIRED", response.text)

    def test_transient_failure_succeeds_on_declared_retry(self) -> None:
        failure = request(
            "/members/10001/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE&attempt=1"
        )
        self.assertEqual("503 Service Unavailable", failure.status)
        self.assertIn("TRANSIENT_LOAD_FAILURE", failure.text)
        self.assertIn("/members/10001/accounts/savings", failure.text)
        self.assertIn("attempt=2", failure.text)

        retry = request(
            "/members/10001/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE&attempt=2&delay_ms=0"
        )
        self.assertEqual("200 OK", retry.status)
        self.assertIn("<iframe", retry.text)

    def test_unexpected_dialog_is_present_and_open(self) -> None:
        response = request("/members/10001?scenario=UNEXPECTED_DIALOG")
        self.assertEqual("200 OK", response.status)
        self.assertIn("<dialog open", response.text)
        self.assertIn("UNEXPECTED_DIALOG", response.text)

    def test_secondary_workflow_stops_at_review_without_permission(self) -> None:
        review = request(
            "/members/10001/subaccounts/new",
            method="POST",
            form={
                "product": "Holiday Savings",
                "nickname": "Trip fund",
                "opening_deposit": "25.00",
            },
        )
        self.assertEqual("200 OK", review.status)
        self.assertIn("Review only: no account has been opened", review.text)
        self.assertIn("Confirmation Boundary", review.text)

        blocked = request(
            "/members/10001/subaccounts/confirm",
            method="POST",
            form={"authorization": ""},
        )
        self.assertEqual("409 Conflict", blocked.status)
        self.assertIn("CONFIRMATION_REQUIRED", blocked.text)

        permitted = request(
            "/members/10001/subaccounts/confirm",
            method="POST",
            form={"authorization": "PERMIT"},
        )
        self.assertEqual("200 OK", permitted.status)
        self.assertIn("No account or financial data was persisted", permitted.text)

    def test_secondary_form_has_deterministic_validation_failure(self) -> None:
        for deposit in ("nope", "NaN", "Infinity", "1.001"):
            with self.subTest(deposit=deposit):
                response = request(
                    "/members/10001/subaccounts/new",
                    method="POST",
                    form={
                        "product": "Holiday Savings",
                        "nickname": "Test",
                        "opening_deposit": deposit,
                    },
                )
                self.assertEqual("422 Unprocessable Entity", response.status)
                self.assertIn("VALIDATION_ERROR", response.text)

    def test_all_seed_records_are_explicitly_synthetic(self) -> None:
        self.assertEqual({"10001", "10002", "10003"}, set(MEMBERS))
        self.assertTrue(all(member.is_synthetic for member in MEMBERS.values()))

    def test_legacy_characteristics_are_exposed_without_hiding_workflow(self) -> None:
        home = request("/")
        self.assertIn("/members/10001/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE", home.text)
        detail = request("/members/10001")
        self.assertGreaterEqual(detail.text.count("<table"), 4)
        self.assertGreaterEqual(detail.text.count(">Open</button>"), 2)
        savings = request("/members/10001/accounts/savings?delay_ms=0")
        self.assertIn('name="account-pane"', savings.text)
        self.assertIn("loads separately and may be delayed", savings.text)


if __name__ == "__main__":
    unittest.main()
