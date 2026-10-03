from collections import defaultdict
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryType, Transactions, get_user_group, money_as_float

AVERAGE_MONTHS = 3


def _previous_year_months(count: int) -> list[int]:
    """The `count` complete months before the current one, as YYYYMM ints."""
    today = date.today()
    year, month = today.year, today.month
    year_months = []
    for _ in range(count):
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
        year_months.append(year * 100 + month)
    return year_months


def _set_monthly_averages(group_id: int, sections: list[dict]) -> None:
    """
    Attach `monthly_average` (or None) and `average_months` to each category: the average monthly total
    over the last AVERAGE_MONTHS complete months, counting only months since the category started (its
    creation or first transaction, whichever is earlier) so new categories aren't dragged toward zero.
    """
    categories = [category for section in sections for category in section["categories"]]
    window = _previous_year_months(AVERAGE_MONTHS)
    transactions = Transactions.objects.filter(
        category_id__in=[category.category_id for category in categories],
        account__group_id=group_id,
        account__deleted=False,
        deleted=False,
    )
    first_year_months = dict(
        transactions.values("category_id").annotate(first=Min("date__year_month")).values_list("category_id", "first")
    )
    totals = defaultdict(float)
    for category_id, year_month, amount in transactions.filter(date__year_month__in=window).values_list(
        "category_id", "date__year_month", "_amount"
    ):
        totals[(category_id, year_month)] += money_as_float(amount) or 0

    for category in categories:
        start = category.created_at.year * 100 + category.created_at.month
        if category.category_id in first_year_months:
            start = min(start, first_year_months[category.category_id])
        months = [year_month for year_month in window if year_month >= start]
        category.average_months = len(months)
        category.monthly_average = None
        if months:
            average = sum(totals[(category.category_id, year_month)] for year_month in months) / len(months)
            if category.category_type.invert_amounts:
                average = -average
            category.monthly_average = round(average, 2)


class Categories(LoginRequiredMixin, View):
    def get(self, request):
        group_id = get_user_group(request.user, request).group_id
        category_types = CategoryType.objects.filter(
            group_id=group_id,
            hidden=False,
        ).order_by("sort_index")
        sections = [
            {
                "category_type": category_type,
                "categories": list(category_type.categories_set.filter(
                    deleted=False,
                    hidden=False,
                ).select_related("category_type").order_by("sort_index")),
            }
            for category_type in category_types
        ]
        _set_monthly_averages(group_id, sections)
        context = {
            "title": "Categories",
            "category_types": category_types,
            "sections": sections,
            "average_months": AVERAGE_MONTHS,
        }
        return render(request, template_name="categories/index.html", context=context)


class Category(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "title": "Category",
        }
        return render(request, template_name="transaction/index.html", context=context)