from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories, CategoryType, UserAttributes, BudgetMonth, Month
from datetime import datetime as dt

class BudgetCategory(LoginRequiredMixin, View):
    def get(self, request, category_id: int):
        current_year_month = f"{dt.now().year}{dt.now().month:02}"
        month = request.GET.get("month", current_year_month)
        category = Categories.objects.get(category_id=category_id)
        category_month = CategoryMonth(category=category, year_month=int(month))
        categories = [
            category for category in
            Categories.objects.filter(
                category_type__user_id=request.user.id,
                hidden=False
            )
        ]
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
            'svg_button_size': 32,
        }
        return render(request, template_name="budget/month_overview.html", context=context)
