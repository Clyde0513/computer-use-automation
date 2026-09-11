"""Server-rendered pages for the deliberately legacy-styled proxy UI."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from urllib.parse import quote

from .data import Account, Member


def layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - Northstar Legacy Servicing</title>
  <link rel="stylesheet" href="/static/legacy.css">
</head>
<body>
  <table class="shell" role="presentation">
    <tr><td class="masthead">
      <b>NORTHSTAR FINANCIAL</b>
      <span>Legacy Servicing Console</span>
    </td></tr>
    <tr><td class="nav"><a href="/">Member Search</a> | Accounts | Reports | Help</td></tr>
    <tr><td class="sandbox">TRAINING SANDBOX — SYNTHETIC RECORDS ONLY</td></tr>
    <tr><td class="content">{body}</td></tr>
    <tr><td class="footer">Internal training proxy · no real bank data</td></tr>
  </table>
</body>
</html>"""


def search_page() -> str:
    return layout(
        "Member Search",
        """
<h1>Member Search</h1>
<table class="panel" role="presentation"><tr><td>
  <form method="get" action="/members/search">
    <table class="form-grid" role="presentation">
      <tr><td>Member Number:</td><td><input name="member_id" size="18" autocomplete="off"></td></tr>
      <tr><td></td><td><button type="submit">Search</button> <button type="reset">Clear</button></td></tr>
    </table>
  </form>
</td></tr></table>

<h2>Deterministic test scenarios</h2>
<table class="results">
  <tr><th>Condition</th><th>Launch</th></tr>
  <tr><td>MEMBER_NOT_FOUND</td><td><a href="/members/search?member_id=99999">Open</a></td></tr>
  <tr><td>VALIDATION_ERROR</td><td><a href="/members/search?member_id=ABC">Open</a></td></tr>
  <tr><td>PERMISSION_DENIED</td><td><a href="/members/10003">Open</a></td></tr>
  <tr><td>SESSION_EXPIRED</td><td><a href="/members/10001?scenario=SESSION_EXPIRED">Open</a></td></tr>
  <tr><td>TRANSIENT_LOAD_FAILURE</td><td><a href="/members/10001/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE&amp;attempt=1">Open</a></td></tr>
  <tr><td>UNEXPECTED_DIALOG</td><td><a href="/members/10001?scenario=UNEXPECTED_DIALOG">Open</a></td></tr>
</table>
<p class="hint">Suggested successful records: <b>10001</b> and <b>10002</b>.</p>
""",
    )


def error_page(code: str, message: str, return_href: str = "/") -> str:
    return layout(
        code.replace("_", " ").title(),
        f"""
<h1>Request could not be completed</h1>
<table class="error-box" role="presentation"><tr><td>
  <strong class="error-code">{escape(code)}</strong>
  <p>{escape(message)}</p>
  <a href="{escape(return_href, quote=True)}">Return</a>
</td></tr></table>
""",
    )


def member_detail_page(member: Member, show_unexpected_dialog: bool = False) -> str:
    rows = "".join(_account_row(member, account) for account in member.accounts)
    dialog = ""
    if show_unexpected_dialog:
        dialog = """
<dialog open class="unexpected-dialog" aria-label="Unexpected system notice">
  <form method="dialog">
    <h2>System Notice</h2>
    <strong>UNEXPECTED_DIALOG</strong>
    <p>A legacy profile reminder interrupted the normal workflow.</p>
    <button value="continue">Continue</button>
    <button value="dismiss">Continue</button>
  </form>
</dialog>
"""
    return layout(
        f"Member {member.member_id}",
        f"""
<h1>Member Detail</h1>
<table class="panel details" role="presentation"><tr><td>
  <table class="nested-details">
    <tr><td class="label">Member Number</td><td>{escape(member.member_id)}</td></tr>
    <tr><td class="label">Member Name</td><td>{escape(member.display_name)}</td></tr>
    <tr><td class="label">Service Tier</td><td>{escape(member.service_tier)}</td></tr>
    <tr><td class="label">Record Type</td><td>Synthetic training record</td></tr>
  </table>
</td></tr></table>

<h2>Accounts</h2>
<table class="results account-grid">
  <tr><th>Type</th><th>Account</th><th>Status</th><th>Action</th></tr>
  {rows}
</table>

<table class="actions" role="presentation"><tr>
  <td><a class="button-link" href="/members/{quote(member.member_id)}/subaccounts/new">Open Sub-Account</a></td>
  <td><a href="/">Back to Search</a></td>
</tr></table>
{dialog}
""",
    )


def _account_row(member: Member, account: Account) -> str:
    route = account.account_type.lower()
    return f"""
<tr>
  <td>{escape(account.account_type)}</td>
  <td>{escape(account.masked_number)}</td>
  <td>{escape(account.status)}</td>
  <td><form method="get" action="/members/{quote(member.member_id)}/accounts/{quote(route)}"><button type="submit">Open</button></form></td>
</tr>"""


def savings_shell_page(member: Member, delay_ms: int = 350) -> str:
    frame_url = f"/members/{quote(member.member_id)}/savings/frame?delay_ms={delay_ms}"
    return layout(
        "Savings Account",
        f"""
<h1>Savings Account</h1>
<table class="panel" role="presentation"><tr><td>
  <b>Member:</b> {escape(member.member_id)} — {escape(member.display_name)}
</td></tr><tr><td>
  <span class="loading-note">Account pane loads separately and may be delayed.</span>
</td></tr></table>
<iframe name="account-pane" title="Savings account balance" src="{escape(frame_url, quote=True)}"></iframe>
<p><a href="/members/{quote(member.member_id)}">Return to Member Detail</a></p>
""",
    )


def savings_frame_page(member: Member, account: Account) -> str:
    balance = f"${account.current_balance:,.2f}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Savings Details</title>
<link rel="stylesheet" href="/static/legacy.css"></head>
<body class="frame-body">
<table class="panel frame-table" role="presentation"><tr><td>
  <table class="nested-details">
    <tr><td class="label">Account Type</td><td>{escape(account.account_type)}</td></tr>
    <tr><td class="label">Account Number</td><td>{escape(account.masked_number)}</td></tr>
    <tr><td class="label">Current Balance</td><td><strong data-field="current-balance">{balance}</strong></td></tr>
    <tr><td class="label">Available Balance</td><td>{balance}</td></tr>
    <tr><td class="label">Status</td><td>{escape(account.status)}</td></tr>
  </table>
</td></tr></table>
</body></html>"""


def checking_page(member: Member, account: Account) -> str:
    return layout(
        "Checking Account",
        f"""
<h1>Checking Account</h1>
<table class="panel"><tr><td>Member</td><td>{escape(member.member_id)}</td></tr>
<tr><td>Account</td><td>{escape(account.masked_number)}</td></tr>
<tr><td>Current Balance</td><td>${account.current_balance:,.2f}</td></tr></table>
<p><a href="/members/{quote(member.member_id)}">Return to Member Detail</a></p>
""",
    )


def transient_failure_page(member_id: str) -> str:
    retry = f"/members/{quote(member_id)}/accounts/savings?scenario=TRANSIENT_LOAD_FAILURE&amp;attempt=2"
    return layout(
        "Temporary Load Failure",
        f"""
<h1>Account pane unavailable</h1>
<table class="error-box" role="presentation"><tr><td>
  <strong class="error-code">TRANSIENT_LOAD_FAILURE</strong>
  <p>The legacy account service did not answer. This simulated failure clears on retry.</p>
  <a class="button-link" href="{retry}">Retry</a>
</td></tr></table>
""",
    )


def subaccount_form_page(
    member: Member,
    errors: tuple[str, ...] = (),
    values: dict[str, str] | None = None,
) -> str:
    values = values or {}
    error_markup = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_markup = (
            f'<div class="validation"><strong>VALIDATION_ERROR</strong><ul>{items}</ul></div>'
        )
    return layout(
        "Open Sub-Account",
        f"""
<h1>Open Sub-Account</h1>
<p>Member {escape(member.member_id)} — {escape(member.display_name)}</p>
{error_markup}
<form method="post" action="/members/{quote(member.member_id)}/subaccounts/new">
  <table class="form-grid panel" role="presentation">
    <tr><td>Product</td><td><select name="product"><option value="">-- Select --</option><option value="Holiday Savings">Holiday Savings</option><option value="Special Savings">Special Savings</option></select></td></tr>
    <tr><td>Nickname</td><td><input name="nickname" value="{escape(values.get("nickname", ""), quote=True)}"></td></tr>
    <tr><td>Opening Deposit</td><td>$ <input name="opening_deposit" value="{escape(values.get("opening_deposit", ""), quote=True)}"></td></tr>
    <tr><td></td><td><button type="submit">Continue</button> <a href="/members/{quote(member.member_id)}">Cancel</a></td></tr>
  </table>
</form>
""",
    )


def subaccount_review_page(
    member: Member,
    product: str,
    nickname: str,
    opening_deposit: Decimal,
) -> str:
    return layout(
        "Review Sub-Account",
        f"""
<h1>Review Sub-Account</h1>
<div class="warning">Review only: no account has been opened.</div>
<table class="results">
  <tr><th>Member</th><td>{escape(member.member_id)} — {escape(member.display_name)}</td></tr>
  <tr><th>Product</th><td>{escape(product)}</td></tr>
  <tr><th>Nickname</th><td>{escape(nickname)}</td></tr>
  <tr><th>Opening Deposit</th><td>${opening_deposit:,.2f}</td></tr>
</table>
<button type="button" onclick="document.querySelector('.confirm-dialog').showModal()">Continue</button>
<a href="/members/{quote(member.member_id)}">Cancel</a>

<dialog class="confirm-dialog" aria-label="Confirm simulated account opening">
  <form method="post" action="/members/{quote(member.member_id)}/subaccounts/confirm">
    <h2>Confirmation Boundary</h2>
    <p>This is the boundary for a simulated irreversible action. Enter <b>PERMIT</b> to continue.</p>
    <input type="hidden" name="product" value="{escape(product, quote=True)}">
    <input type="hidden" name="nickname" value="{escape(nickname, quote=True)}">
    <input type="hidden" name="opening_deposit" value="{opening_deposit}">
    <label>Authorization <input name="authorization" autocomplete="off"></label>
    <button type="submit">Confirm</button>
    <button type="button" onclick="this.closest('dialog').close()">Cancel</button>
  </form>
</dialog>
""",
    )


def simulated_confirmation_page(member: Member) -> str:
    return layout(
        "Simulation Complete",
        f"""
<h1>Simulation Complete</h1>
<div class="success"><strong>CONFIRMED</strong><p>The explicitly permitted simulation completed. No account or financial data was persisted.</p></div>
<p><a href="/members/{quote(member.member_id)}">Return to Member Detail</a></p>
""",
    )
