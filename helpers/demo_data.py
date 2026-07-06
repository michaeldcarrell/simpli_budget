import random
import uuid
from datetime import datetime as dt

from dateutil.relativedelta import relativedelta
from django.db import transaction as db_transaction
from pytz import UTC

from simpli_budget.models import (
    Group,
    CategoryType,
    Categories,
    CategoryMonth,
    Accounts,
    Transactions,
    Date,
)

DEMO_GROUP_NAME = "Demo Household"

CHECKING = "checking"
CREDIT_CARD = "credit_card"

ACCOUNT_PROFILES = {
    CHECKING: {
        "name": "Demo Checking",
        "type": "depository",
        "sub_type": "checking",
        "balance": 3200.00,
    },
    CREDIT_CARD: {
        "name": "Demo Credit Card",
        "type": "credit",
        "sub_type": "credit card",
        "balance": -420.00,
    },
}

# Each category type groups categories that share an `invert_amounts` sign convention.
# Each category carries a monthly budget plus a schedule describing how its transactions
# should be fabricated so totals track the budget and merchants suit the category:
#   "fixed"    - occurs on ~fixed days each month (rent, paycheck, subscriptions); the
#                budget is split evenly across those occurrences.
#   "variable" - occurs a random number of times per month (groceries, restaurants); the
#                budget is split unevenly across however many occurrences land that month.
CATEGORY_TYPE_PROFILES = [
    {
        "name": "Income",
        "invert_amounts": True,
        "sort_index": 0,
        "categories": [
            {
                "name": "Paycheck",
                "default_monthly_amount": 5200.00,
                "account": CHECKING,
                "schedule": "fixed",
                "days_of_month": [1, 15],
                "merchants": ["Acme Corp Payroll"],
            },
        ],
    },
    {
        "name": "Housing",
        "invert_amounts": False,
        "sort_index": 1,
        "categories": [
            {
                "name": "Rent",
                "default_monthly_amount": 1800.00,
                "account": CHECKING,
                "schedule": "fixed",
                "days_of_month": [1],
                "merchants": ["Skyline Apartments"],
            },
            {
                "name": "Electric & Gas",
                "default_monthly_amount": 120.00,
                "account": CHECKING,
                "schedule": "fixed",
                "days_of_month": [10],
                "merchants": ["Pacific Power & Gas"],
            },
        ],
    },
    {
        "name": "Food",
        "invert_amounts": False,
        "sort_index": 2,
        "categories": [
            {
                "name": "Groceries",
                "default_monthly_amount": 600.00,
                "account": CREDIT_CARD,
                "schedule": "variable",
                "frequency_per_month": (8, 12),
                "amount_bounds": (25.00, 95.00),
                "merchants": ["Trader Joe's", "Whole Foods", "Safeway", "Kroger"],
            },
            {
                "name": "Restaurants",
                "default_monthly_amount": 250.00,
                "account": CREDIT_CARD,
                "schedule": "variable",
                "frequency_per_month": (6, 10),
                "amount_bounds": (9.00, 55.00),
                "merchants": ["Chipotle", "Sushi House", "Local Pizzeria", "Starbucks"],
            },
        ],
    },
    {
        "name": "Transportation",
        "invert_amounts": False,
        "sort_index": 3,
        "categories": [
            {
                "name": "Gas",
                "default_monthly_amount": 160.00,
                "account": CREDIT_CARD,
                "schedule": "variable",
                "frequency_per_month": (3, 5),
                "amount_bounds": (30.00, 65.00),
                "merchants": ["Shell", "Chevron", "76"],
            },
            {
                "name": "Rideshare",
                "default_monthly_amount": 60.00,
                "account": CREDIT_CARD,
                "schedule": "variable",
                "frequency_per_month": (2, 5),
                "amount_bounds": (8.00, 30.00),
                "merchants": ["Uber", "Lyft"],
            },
        ],
    },
    {
        "name": "Subscriptions",
        "invert_amounts": False,
        "sort_index": 4,
        "categories": [
            {
                "name": "Streaming & Software",
                "default_monthly_amount": 45.00,
                "account": CREDIT_CARD,
                "schedule": "fixed",
                "days_of_month": [5],
                "merchants": ["Netflix", "Spotify"],
            },
        ],
    },
]


def _get_or_create_group() -> Group:
    from django.conf import settings
    if settings.DEMO_GROUP_ID is not None:
        group = Group.objects.filter(group_id=settings.DEMO_GROUP_ID).first()
        if group is not None:
            return group
    group, _ = Group.objects.get_or_create(name=DEMO_GROUP_NAME)
    return group


def _ensure_accounts(group: Group) -> dict:
    accounts = {}
    for key, profile in ACCOUNT_PROFILES.items():
        account = Accounts.objects.filter(group=group, name=profile["name"]).first()
        if account is None:
            now = dt.now(tz=UTC)
            account = Accounts.objects.create(
                account_id=f"demo-{uuid.uuid4().hex}",
                group=group,
                type=profile["type"],
                sub_type=profile["sub_type"],
                name=profile["name"],
                _balance=f"{profile['balance']:.2f}",
                transactions_last_updated_at=now,
                created_at=now,
                updated_at=now,
                deleted=False,
            )
        accounts[key] = account
    return accounts


def _ensure_categories(group: Group) -> tuple[dict, dict]:
    """Returns ({category_name: Categories}, {category_type_name: CategoryType})."""
    categories = {}
    category_types = {}
    now = dt.now(tz=UTC)
    for type_profile in CATEGORY_TYPE_PROFILES:
        category_type, _ = CategoryType.objects.get_or_create(
            group=group,
            category_type_name=type_profile["name"],
            defaults={
                "invert_amounts": type_profile["invert_amounts"],
                "hidden": False,
                "sort_index": type_profile["sort_index"],
                "created_at": now,
                "updated_at": now,
            },
        )
        category_types[type_profile["name"]] = category_type
        for sort_index, category_profile in enumerate(type_profile["categories"]):
            category, _ = Categories.objects.get_or_create(
                category_type=category_type,
                category_name=category_profile["name"],
                defaults={
                    "_default_monthly_amount": f"{category_profile['default_monthly_amount']:.2f}",
                    "sort_index": sort_index,
                    "hidden": False,
                    "deleted": False,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            categories[category_profile["name"]] = category
    return categories, category_types


def _ensure_category_month(category: Categories, year_month: int, amount: float) -> None:
    CategoryMonth.objects.get_or_create(
        category=category,
        year_month=year_month,
        defaults={"amount": f"{amount:.2f}"},
    )


def _dates_for_month(year_month: int) -> list:
    return list(Date.objects.filter(year_month=year_month).order_by("date"))


def _closest_date_for_day(dates: list, day: int):
    if not dates:
        return None
    return min(dates, key=lambda d: abs(d.date_of_month - day))


def _make_transaction(*, account, category, merchant, amount, date, invert_amounts) -> Transactions:
    stored_amount = -amount if invert_amounts else amount
    now = dt.now(tz=UTC)
    return Transactions.objects.create(
        transaction_id=f"demo-{uuid.uuid4().hex}",
        account=account,
        category=category,
        name=merchant,
        merchant_name=merchant,
        iso_currency_code="USD",
        date=date,
        authorized_date=date.date,
        pending=False,
        _amount=f"{stored_amount:.2f}",
        deleted=False,
        created_at=now,
        updated_at=now,
    )


def _generate_fixed(category_profile, category, category_type, accounts, dates) -> list:
    occurrences = category_profile["days_of_month"]
    budget = category.default_monthly_amount or category_profile["default_monthly_amount"]
    share = budget / len(occurrences)
    transactions = []
    for day in occurrences:
        date = _closest_date_for_day(dates, day)
        if date is None:
            continue
        amount = round(share * random.uniform(0.97, 1.03), 2)
        merchant = random.choice(category_profile["merchants"])
        transactions.append(_make_transaction(
            account=accounts[category_profile["account"]],
            category=category,
            merchant=merchant,
            amount=amount,
            date=date,
            invert_amounts=category_type.invert_amounts,
        ))
    return transactions


def _generate_variable(category_profile, category, category_type, accounts, dates, count=None, anchor_to_budget=True) -> list:
    if count is None:
        count = random.randint(*category_profile["frequency_per_month"])
    if count <= 0 or not dates:
        return []

    low, high = category_profile["amount_bounds"]
    if anchor_to_budget:
        # Split a budget-sized total unevenly across this month's occurrences, so the
        # category's actual total lands close to (not exactly on) what it's budgeted for.
        budget = category.default_monthly_amount or category_profile["default_monthly_amount"]
        total_target = budget * random.uniform(0.8, 1.05)
        weights = [random.random() for _ in range(count)]
        weight_sum = sum(weights) or 1
        amounts = [round(min(max(total_target * (weight / weight_sum), low), high), 2) for weight in weights]
    else:
        # Incremental "more activity" batch - just plausible one-off amounts, not anchored
        # to the remaining month budget.
        amounts = [round(random.uniform(low, high), 2) for _ in range(count)]

    transactions = []
    for amount in amounts:
        merchant = random.choice(category_profile["merchants"])
        date = random.choice(dates)
        transactions.append(_make_transaction(
            account=accounts[category_profile["account"]],
            category=category,
            merchant=merchant,
            amount=amount,
            date=date,
            invert_amounts=category_type.invert_amounts,
        ))
    return transactions


def seed_demo_account(months_back: int = 3) -> Group:
    """Creates (or reuses) the demo group, its accounts/categories, and `months_back`
    months of history plus the current month - each category's transactions anchored to
    its own budget so the demo budget page looks like a real, lived-in household."""
    group = _get_or_create_group()
    accounts = _ensure_accounts(group)
    categories, category_types = _ensure_categories(group)

    today = dt.now(tz=UTC).replace(day=1)
    year_months = [
        int(f"{(today - relativedelta(months=i)).year}{(today - relativedelta(months=i)).month:02}")
        for i in range(months_back, -1, -1)
    ]

    with db_transaction.atomic():
        for year_month in year_months:
            dates = _dates_for_month(year_month)
            if not dates:
                continue
            for type_profile in CATEGORY_TYPE_PROFILES:
                category_type = category_types[type_profile["name"]]
                for category_profile in type_profile["categories"]:
                    category = categories[category_profile["name"]]
                    _ensure_category_month(category, year_month, category_profile["default_monthly_amount"])
                    if category_profile["schedule"] == "fixed":
                        _generate_fixed(category_profile, category, category_type, accounts, dates)
                    else:
                        _generate_variable(category_profile, category, category_type, accounts, dates)
    return group


def generate_recent_activity(group: Group) -> list:
    """Adds a small batch of new everyday transactions (groceries, restaurants, gas, ...)
    up through today, for a demo account that already exists. Meant to be called on
    demand (e.g. a "simulate more activity" button) rather than regenerating the month,
    so it doesn't disturb anything a demo visitor has already categorized or tagged.
    Fixed-schedule categories (rent, paycheck, subscriptions) are skipped here since
    they shouldn't recur mid-month."""
    today = dt.now(tz=UTC)
    year_month = int(f"{today.year}{today.month:02}")
    dates = [date for date in _dates_for_month(year_month) if date.date <= today.date()]
    if not dates:
        return []

    accounts = _ensure_accounts(group)
    created = []
    for type_profile in CATEGORY_TYPE_PROFILES:
        category_type = CategoryType.objects.filter(group=group, category_type_name=type_profile["name"]).first()
        if category_type is None:
            continue
        for category_profile in type_profile["categories"]:
            if category_profile["schedule"] != "variable":
                continue
            category = Categories.objects.filter(category_type=category_type, category_name=category_profile["name"]).first()
            if category is None:
                continue
            budget = category.default_monthly_amount or category_profile["default_monthly_amount"]
            if category.monthly_amount(year_month) >= budget * 1.5:
                continue  # already well over budget this month - don't keep piling on
            created += _generate_variable(
                category_profile, category, category_type, accounts, dates,
                count=random.randint(1, 3),
                anchor_to_budget=False,
            )
    return created
