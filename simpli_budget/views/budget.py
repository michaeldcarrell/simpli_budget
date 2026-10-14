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

        context = {
            "title": f"{category.category_name} - {category_month.month.name_short}",
            "category_month": category_month,
            'categories': categories,
        }

        return render(request, template_name="budget/category.html", context=context)


BAR_SEGMENTS = 10


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
        income = spent = budgeted_expenses = 0
        for category_type_month in budget_month.category_types:
            is_income = bool(category_type_month.category_type.invert_amounts)
            rows = [_category_row(category_month, is_income) for category_month in category_type_month.categories]
            section_spent = sum(row['spent'] for row in rows)
            section_target = sum(row['target'] for row in rows)
            if is_income:
                income += section_spent
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
        context = {
            'budget_month': budget_month,
            'sections': sections,
            'income_display': _num(income),
            'spent_display': _num(spent),
            'left_display': _num(left),
            'left_is_negative': left < 0,
            'is_current_month': is_current_month,
            'day_of_month': today.day,
            'days_in_month': days_in_month,
            'month_percent': round(today.day / days_in_month * 100),
            'month_label': f"{month_start.month_name_short} {month_start.year}".upper(),
            'is_demo_group': settings.DEMO_GROUP_ID is not None and int(group_id) == settings.DEMO_GROUP_ID,
        }
        return render(request, template_name="budget/month_overview.html", context=context)
