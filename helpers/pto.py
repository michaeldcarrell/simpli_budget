"""PTO funds, shown on the PTO tab for the groups configured in settings.PTO_FUNDS only.

A fund is an account someone sets their quarterly estimated taxes aside in, so what's in it beyond this quarter's taxes
is time off they've saved up: the account's balance minus tax_rate of the income received since the quarter began.
Earlier quarters' taxes are assumed already paid out of the account.
"""
from dataclasses import dataclass
from datetime import date, datetime as dt, timedelta

from django.conf import settings
from pytz import UTC

from simpli_budget.models import Accounts, Transactions

# A balance older than this gets a "reconnect" warning, since the PTO figure is only as fresh as it.
STALE_AFTER = timedelta(hours=36)


@dataclass
class PtoFund:
    owner: str
    account: Accounts
    balance: float
    quarter_label: str
    quarter_income: float
    tax_rate: float
    income_transactions: list[Transactions]

    @property
    def taxes_set_aside(self) -> float:
        return round(self.quarter_income * self.tax_rate, 2)

    @property
    def pto(self) -> float:
        return self.balance - self.taxes_set_aside

    @property
    def balance_as_of(self):
        return self.account.updated_at

    @property
    def is_stale(self) -> bool:
        return self.account.updated_at is None or dt.now(tz=UTC) - self.account.updated_at > STALE_AFTER


def pto_enabled(group_id) -> bool:
    """Whether the group gets the PTO tab; a config lookup only, so it's cheap enough for every page's nav."""
    return group_id is not None and int(group_id) in settings.PTO_FUNDS


def _quarter_start(today: date) -> date:
    return date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)


def pto_fund(group_id: int, today: date | None = None) -> PtoFund | None:
    """The group's PTO fund as of today, or None if the group doesn't have one (or its account is missing)."""
    config = settings.PTO_FUNDS.get(int(group_id))
    if config is None:
        return None
    account = Accounts.objects.filter(group_id=group_id, given_name=config['account_name'], deleted=False).first()
    if account is None:
        return None

    today = today or dt.now().date()
    quarter_start = _quarter_start(today)
    # Income categories can also hold outgoing transfers (e.g. contributions to the fund); only money received
    # counts as income, and Plaid records money in as a negative amount.
    income_transactions = [
        t for t in Transactions.objects.filter(
            category_id=config['income_category_id'],
            account__deleted=False,
            date__date__gte=quarter_start,
            date__date__lte=today,
        ).exclude(deleted=True).order_by('-date')
        if t.amount is not None and t.amount < 0
    ]
    quarter_income = -sum(t.amount for t in income_transactions)

    return PtoFund(
        owner=config['owner'],
        account=account,
        balance=account.balance or 0,
        quarter_label=f"Q{(quarter_start.month - 1) // 3 + 1} {quarter_start.year}",
        quarter_income=quarter_income,
        tax_rate=config['tax_rate'],
        income_transactions=income_transactions,
    )
