from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.views import View
from simpli_budget.views.categories import Categories, Category
from simpli_budget.views.transaction import Transaction, TransactionSearch
from simpli_budget.views.budget import BudgetCategory, MonthBudget
from simpli_budget.views.accounts import AccountsView, Account
from simpli_budget.views.rules import Rules, RuleView
from simpli_budget.views.tags import Tags
from simpli_budget.views.notifications import Notifications


class Logout(View):
    def get(self, request):
        logout(request)
        # Not straight to the Google login: with SOCIALACCOUNT_LOGIN_ON_GET, Google silently signs the
        # browser's account back in, so logging out looked like it did nothing.
        return redirect("logged_out")


class LoggedOut(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/")
        return render(request, "logged_out.html")