from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories, CategoryType, UserAttributes, BudgetMonth
from datetime import datetime as dt

class BudgetCategory(LoginRequiredMixin, View):
    def get(self, request, category_id: int):
        current_year_month = f"{dt.now().year}{dt.now().month:02}"
        month = request.GET.get("month", current_year_month)
        category = Categories.objects.get(category_id=category_id)
        category_month = CategoryMonth(category=category, year_month=int(month))
        context = {
            "title": f"{category.category_name} - {category_month.month.name_short}",
            "category_month": category_month,
        }

        return render(request, template_name="budget/category.html", context=context)


class MonthBudget(LoginRequiredMixin, View):
    def get(self, request):
        category_types = CategoryType.objects.filter(user_id=request.user.id)
        current_year_month = int(f"{dt.now().year}{dt.now().month:02}")
        year_month = request.GET.get("month", current_year_month)
        attributes = UserAttributes.objects.filter(user_id=request.user.id).first()
        context = {
            'budget_month': BudgetMonth(
                category_types=category_types,
                year_month=year_month,
                include_hidden=attributes.show_hidden
            ),
        }
        return render(request, template_name="budget/month_overview.html", context=context)
