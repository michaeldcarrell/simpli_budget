from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories, CategoryType, UserAttributes, BudgetMonth, Month, get_user_group
from datetime import datetime as dt
from simpli_budget.views.categories import _set_monthly_averages

class BudgetCategory(LoginRequiredMixin, View):
    def get(self, request, category_id: int):
        current_year_month = f"{dt.now().year}{dt.now().month:02}"
        month = request.GET.get("month", current_year_month)
        group_id = get_user_group(request.user, request).group_id
        category = Categories.objects.get(category_id=category_id)
        if not category.user_has_access(request.user):
            return render(
                request,
                template_name="404.html",
                context={
                    "message": "Category not found"
                }
            )
        category_month = CategoryMonth(category=category, year_month=int(month)).get()
        categories = [
            category for category in
            Categories.objects.filter(
                category_type__group_id=group_id,
                hidden=False,
                deleted=False,
            ).order_by("category_type__sort_index", "sort_index")
        ]

        # TODO: This will cause issues with New users, currently that category type is attached to my group
        categories.append(
            Categories.objects.filter(
                category_id=-1
            ).first()
        )

        spent = category_month.month_total
        budgeted = category_month.amount or 0
        is_income = bool(category.category_type.invert_amounts)
        month_start = category_month.month.start_of_month_date
        _set_monthly_averages(group_id, [{'categories': [category]}])
        context = {
            "title": f"{category.category_name} - {category_month.month.name_short}",
            "category_month": category_month,
            'categories': categories,
            'is_income': is_income,
            'spent_display': _num(spent),
            'budgeted_display': _num(budgeted),
            'left_display': _num(abs(budgeted - spent)),
            'left_label': ('Above' if spent >= budgeted else 'To go') if is_income else ('Over' if spent > budgeted else 'Left'),
            'left_is_over': not is_income and spent > budgeted,
            'month_label': f"{month_start.month_name_short} {month_start.year}".upper(),
            'month_name': month_start.month_name,
            'budgeted_amount': f"{budgeted:.2f}",
            'is_override': category_month.is_override,
            'default_display': _num(category.default_monthly_amount or 0),
            'average_display': _num(category.monthly_average) if category.monthly_average is not None else '—',
        }

        return render(request, template_name="budget/category.html", context=context)


BAR_SEGMENTS = 10
# Income is budgeted as two paychecks a month, but bi-weekly pay is 26 a year, so it averages 13/12 of that.
PAYCHECKS_PER_YEAR = 26
BUDGETED_PAYCHECKS_PER_MONTH = 2


def _num(value: float) -> str:
    """Ledger-style amount: grouped, two decimals, no currency sign."""
    return f"{value:,.2f}"


def _category_row(category_month, is_income: bool) -> dict:
    """Everything the month overview shows for one category, precomputed for the template."""
    spent = category_month.month_total
    target = category_month.amount or 0
    row = {
        'category_month': category_month,
        'category_id': category_month.category.category_id,
        'name': category_month.category.category_name,
        'spent': spent,
        'target': target,
        'spent_display': _num(spent),
        'target_display': _num(target),
        'has_target': target > 0,
        'is_override': category_month.is_override,
        'state': 'none',
        'segments': [],
        'status': '',
    }
    if target <= 0:
        return row

    over = spent > target
    if is_income:
        row['state'] = 'income'
        row['status'] = f"+{_num(spent - target)} above" if spent >= target else f"{_num(target - spent)} to go"
    elif over:
        row['state'] = 'over'
        row['status'] = f"+{_num(spent - target)} over"
    else:
        row['state'] = 'ok'
        row['status'] = f"{_num(target - spent)} left"
    filled = max(0, min(BAR_SEGMENTS, round(spent / target * BAR_SEGMENTS)))
    row['segments'] = [i < filled for i in range(BAR_SEGMENTS)]
    return row


def _average_income(budgeted_income: float) -> float:
    """Budgeted income (two paychecks) scaled to what bi-weekly pay averages to per month."""
    return budgeted_income * PAYCHECKS_PER_YEAR / 12 / BUDGETED_PAYCHECKS_PER_MONTH


def _left_state(spent: float, budgeted_expenses: float, income_limit: float) -> tuple[str, int]:
    """
    Colour zone for the month's Left: 'ok' while within budget, 'warn' while over budget but still within
    income_limit, and 'over' beyond that. For 'warn', also how far (0-100) spending is from the budget
    toward income_limit.
    """
    if spent <= budgeted_expenses:
        return 'ok', 0
    if spent > income_limit:
        return 'over', 100
    headroom = income_limit - budgeted_expenses
    return 'warn', round((spent - budgeted_expenses) / headroom * 100)


class MonthBudget(LoginRequiredMixin, View):
    def get(self, request):
        today = dt.now()
        current_year_month = int(f"{today.year}{today.month:02}")
        year_month = int(request.GET.get("month", current_year_month))
        group_id = get_user_group(request.user, request).group_id

        category_types = CategoryType.objects.filter(group_id=group_id).order_by("sort_index")
        attributes = UserAttributes.objects.filter(user_id=request.user.id).first()
        budget_month = BudgetMonth(
            category_types=category_types,
            year_month=year_month,
            include_hidden=attributes.show_hidden
        )

        sections = []
        income = spent = budgeted_expenses = budgeted_income = 0
        for category_type_month in budget_month.category_types:
            is_income = bool(category_type_month.category_type.invert_amounts)
            rows = [_category_row(category_month, is_income) for category_month in category_type_month.categories]
            section_spent = sum(row['spent'] for row in rows)
            section_target = sum(row['target'] for row in rows)
            if is_income:
                income += section_spent
                budgeted_income += section_target
            else:
                spent += section_spent
                budgeted_expenses += section_target
            sections.append({
                'category_type': category_type_month.category_type,
                'is_income': is_income,
                'rows': rows,
                'spent_display': _num(section_spent),
                'target_display': _num(section_target),
            })

        _set_monthly_averages(group_id, [
            {'categories': [row['category_month'].category for row in section['rows']]}
            for section in sections
        ])
        for section in sections:
            for row in section['rows']:
                average = row['category_month'].category.monthly_average
                row['average_display'] = _num(average) if average is not None else None

        month_start = budget_month.month.start_of_month_date
        days_in_month = month_start.days_in_month
        is_current_month = year_month == current_year_month
        left = budgeted_expenses - spent
        average_income = _average_income(budgeted_income)
        # A three-paycheck month can bring in more than the average; spending covered by it isn't red.
        income_limit = max(average_income, income)
        left_state, left_overspend_percent = _left_state(spent, budgeted_expenses, income_limit)
        context = {
            'budget_month': budget_month,
            'sections': sections,
            'income_display': _num(income),
            'spent_display': _num(spent),
            'left_display': _num(left),
            'left_state': left_state,
            'left_overspend_percent': left_overspend_percent,
            'budgeted_expenses_display': _num(budgeted_expenses),
            'budgeted_income_display': _num(budgeted_income),
            'average_income_display': _num(average_income),
            'income_limit_display': _num(income_limit),
            'paychecks_per_year': PAYCHECKS_PER_YEAR,
            'budgeted_paychecks_per_year': BUDGETED_PAYCHECKS_PER_MONTH * 12,
            'is_current_month': is_current_month,
            'day_of_month': today.day,
            'days_in_month': days_in_month,
            'month_percent': round(today.day / days_in_month * 100),
            'month_label': f"{month_start.month_name_short} {month_start.year}".upper(),
            'is_demo_group': settings.DEMO_GROUP_ID is not None and int(group_id) == settings.DEMO_GROUP_ID,
        }
        return render(request, template_name="budget/month_overview.html", context=context)
