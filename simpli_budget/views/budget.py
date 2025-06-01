from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories
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
