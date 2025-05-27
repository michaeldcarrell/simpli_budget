from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views import View
from simpli_budget.models import *
from datetime import datetime as dt


class Index(LoginRequiredMixin, View):
    def get(self, request):
        category_types = CategoryType.objects.filter(user_id=request.user.id)
        current_year_month = int(f"{dt.now().year}{dt.now().month:02}")
        year_month = request.GET.get("month", current_year_month)
        context = {
            'budget_month': BudgetMonth(category_types, year_month),
        }
        return render(request, template_name="index.html", context=context)

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("/accounts/google/login")