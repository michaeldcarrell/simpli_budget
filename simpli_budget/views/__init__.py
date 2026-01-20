from django.shortcuts import redirect
from django.contrib.auth import logout
from django.views import View
from simpli_budget.views.categories import Categories, Category
from simpli_budget.views.transaction import Transaction, TransactionSearch
from simpli_budget.views.budget import BudgetCategory, MonthBudget
from simpli_budget.views.accounts import AccountsView, Account
from simpli_budget.views.rules import Rules, RuleView


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("/accounts/google/login")