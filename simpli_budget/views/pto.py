from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from helpers.pto import pto_enabled, pto_fund
from simpli_budget.models import get_user_group, is_demo_user


class Pto(LoginRequiredMixin, View):
    """The PTO tab: only for groups with a fund in helpers/pto.py's PTO_FUNDS, everyone else gets a 404."""
    def get(self, request):
        group_id = get_user_group(request.user, request).group_id
        if is_demo_user(request.user) or not pto_enabled(group_id):
            return render(request, template_name="404.html", context={"message": "Page not found"}, status=404)

        fund = pto_fund(group_id)
        context = {
            "title": f"{fund.owner}'s PTO" if fund else "PTO",
            "fund": fund,
        }
        return render(request, template_name="pto/index.html", context=context)
