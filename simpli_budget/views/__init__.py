from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from simpli_budget.models import GroupUser
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
        return redirect("/?signed_out=1")


class Landing(View):
    """
    The public front page and settings.LOGIN_URL: a choice between Google sign-in and the read-only demo.
    Signed-in users go on to the budget overview, keeping the query string so old `/?month=` links still work.
    """
    def get(self, request):
        if request.user.is_authenticated:
            query = request.GET.copy()
            query.pop("next", None)
            query.pop("signed_out", None)
            return redirect("/budget" + (f"?{query.urlencode()}" if query else ""))
        next_url = request.GET.get("next", "/budget")
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = "/budget"
        # prompt=select_account so Google offers an account choice instead of silently reusing the last one.
        google_login_url = "/accounts/google/login?" + urlencode({
            "auth_params": "prompt=select_account",
            "next": next_url,
        })
        return render(request, "landing.html", {
            "signed_out": "signed_out" in request.GET,
            "google_login_url": google_login_url,
            "demo_enabled": settings.DEMO_GROUP_ID is not None,
        })


class Demo(View):
    """Shareable entry point that signs a visitor in as the read-only demo user."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/budget")
        if settings.DEMO_GROUP_ID is None:
            raise Http404("Demo not found")
        demo_user = get_user_model().objects.filter(username=settings.DEMO_USERNAME, is_active=True).first()
        if demo_user is None or not GroupUser.objects.filter(user=demo_user, group_id=settings.DEMO_GROUP_ID).exists():
            raise Http404("Demo not found")
        login(request, demo_user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("/budget")
