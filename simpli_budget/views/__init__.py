from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views import View
from simpli_budget.models import *
from datetime import datetime as dt
from simpli_budget.views.categories import Categories, Category
from simpli_budget.views.transaction import Transaction
from simpli_budget.views.budget import BudgetCategory


class Index(LoginRequiredMixin, View):
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
        return render(request, template_name="index.html", context=context)


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("/accounts/google/login")