from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories
from datetime import datetime as dt

class BudgetCategory(LoginRequiredMixin, View):
    def get(self, request):
        category_id = int(request.GET.get("category_id"))
        current_year_month = int(f"{dt.now().year}{dt.now().month:02}")
        month = request.GET.get("month", current_year_month)
        category = Categories.objects.get(id=category_id)
        context = {
            "category_month": CategoryMonth(category=category, year_month=int(month)),
        }

        return render(request, template_name="budget/category_month.html", context=context)
