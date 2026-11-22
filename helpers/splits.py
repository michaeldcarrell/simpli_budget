"""
Validation for splitting one transaction across categories (BUDGET-1).

A split is stored as extra lines (budget.transaction_split); the transaction's own category keeps the
remainder, so the lines always add up to the transaction. This module is pure (no database) so the rules
can be unit tested; TransactionSplitsAPI checks category access before calling it.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal('0.01')
MAX_SPLIT_LINES = 20


class SplitError(ValueError):
    pass


@dataclass(frozen=True)
class SplitLine:
    category_id: int
    amount: Decimal  # carries the transaction's sign, as stored


def parse_amount(value) -> Decimal:
    """A user-entered amount ('12.5', '$1,234.56', 12.5) as a positive Decimal rounded to the cent."""
    if isinstance(value, bool) or value is None:
        raise SplitError('Each line needs an amount')
    try:
        amount = Decimal(str(value).replace('$', '').replace(',', '').strip())
    except InvalidOperation:
        raise SplitError(f'"{value}" is not a valid amount')
    if not amount.is_finite():
        raise SplitError(f'"{value}" is not a valid amount')
    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise SplitError('Each line needs an amount greater than 0')
    return amount


def build_split_lines(total: Decimal, primary_category_id: int, raw_lines) -> list[SplitLine]:
    """
    Turn the request's lines ([{category_id, amount}], amounts entered positive as the UI shows them) into
    stored lines carrying the transaction's sign. Raises SplitError when the split doesn't make sense:
    a zero transaction, a repeated category or the transaction's own category, or lines adding up to more
    than the transaction (which would flip the remainder's sign).
    """
    if total is None or total == 0:
        raise SplitError("A $0 transaction can't be split")
    if not isinstance(raw_lines, list) or not raw_lines:
        raise SplitError('Add at least one split line')
    if len(raw_lines) > MAX_SPLIT_LINES:
        raise SplitError(f'A transaction can be split into at most {MAX_SPLIT_LINES} extra lines')

    sign = 1 if total > 0 else -1
    lines = []
    seen = set()
    for raw in raw_lines:
        if not isinstance(raw, dict):
            raise SplitError('Each line needs a category and an amount')
        category_id = raw.get('category_id')
        if isinstance(category_id, str) and category_id.lstrip('-').isdigit():
            category_id = int(category_id)
        if isinstance(category_id, bool) or not isinstance(category_id, int):
            raise SplitError('Each line needs a category')
        if category_id == primary_category_id:
            raise SplitError("A line can't use the transaction's own category; that category gets what's left")
        if category_id in seen:
            raise SplitError('Each category can only appear once in a split')
        seen.add(category_id)
        lines.append(SplitLine(category_id=category_id, amount=sign * parse_amount(raw.get('amount'))))

    allocated = sum((abs(line.amount) for line in lines), Decimal('0'))
    if allocated > abs(total):
        raise SplitError(
            f'The lines add up to ${allocated:,.2f}, more than the ${abs(total):,.2f} transaction'
        )
    return lines


def remainder(total: Decimal, lines: list[SplitLine]) -> Decimal:
    return total - sum((line.amount for line in lines), Decimal('0'))
