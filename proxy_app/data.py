"""Synthetic records used by the local proxy application."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Account:
    account_type: str
    masked_number: str
    current_balance: Decimal
    status: str = "Active"


@dataclass(frozen=True, slots=True)
class Member:
    member_id: str
    display_name: str
    service_tier: str
    accounts: tuple[Account, ...]
    access_allowed: bool = True
    is_synthetic: bool = True

    def account(self, account_type: str) -> Account | None:
        return next(
            (item for item in self.accounts if item.account_type == account_type),
            None,
        )


MEMBERS: Mapping[str, Member] = MappingProxyType(
    {
        "10001": Member(
            member_id="10001",
            display_name="Avery Example",
            service_tier="Standard Demo",
            accounts=(
                Account("Savings", "S-4101", Decimal("1245.67")),
                Account("Checking", "C-7720", Decimal("386.11")),
            ),
        ),
        "10002": Member(
            member_id="10002",
            display_name="Jordan Sample",
            service_tier="Plus Demo",
            accounts=(
                Account("Savings", "S-4102", Decimal("98.04")),
                Account("Checking", "C-7721", Decimal("2075.50")),
            ),
        ),
        "10003": Member(
            member_id="10003",
            display_name="Riley Demo",
            service_tier="Restricted Demo",
            accounts=(Account("Savings", "S-4103", Decimal("7500.00")),),
            access_allowed=False,
        ),
    }
)
