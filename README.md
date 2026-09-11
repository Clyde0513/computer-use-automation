# Computer-Use Automation System

This repository contains the PRD-01 proxy application and the PRD-02
surface-neutral action and observation contracts. The proxy is a deliberately
awkward, local-only financial servicing UI for exercising computer-use
automation. All people, identifiers, accounts, and balances in the application
are synthetic.

## Run the proxy application

Python 3.11 or newer is required. The proxy application itself has no
third-party runtime dependencies.

```powershell
python -m proxy_app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/>. Stop the server with `Ctrl+C`.

The primary manual workflow is:

1. Search for member `10001` or `10002`.
2. Open the member record.
3. Open the Savings account row.
4. Read the current balance from the embedded account frame.

Member `10003` is a synthetic restricted record and deterministically produces
`PERMISSION_DENIED`.

## Deterministic scenarios

The home page includes links for every required exceptional state:

| State | Trigger |
| --- | --- |
| `MEMBER_NOT_FOUND` | Search for `99999` |
| `VALIDATION_ERROR` | Search for a blank or non-five-digit ID |
| `PERMISSION_DENIED` | Search for `10003` |
| `SESSION_EXPIRED` | Open `/members/10001?scenario=SESSION_EXPIRED` |
| `TRANSIENT_LOAD_FAILURE` | Open `/members/10001/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE&attempt=1`; its Retry link succeeds |
| `UNEXPECTED_DIALOG` | Open `/members/10001?scenario=UNEXPECTED_DIALOG` |

The optional sub-account workflow starts from an allowed member's detail page.
It reaches a review dialog without making a change. The final simulated action
requires the operator to explicitly enter `PERMIT`; even then, no data is
persisted.

## Tests

Install the project and development tools, then run the full suite:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
mypy
```

Browser binaries are only needed for real Playwright integration tests:

```powershell
python -m playwright install chromium
$env:RUN_BROWSER_TESTS = "1"
python -m pytest tests/test_browser_surface_integration.py
```
