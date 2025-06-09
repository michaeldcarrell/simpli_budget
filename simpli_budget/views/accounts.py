from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import (
    CategoryMonth,
    Categories,
    CategoryType,
    UserAttributes,
    BudgetMonth,
    AccessTokens,
)
from datetime import datetime as dt


class AccountsView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'link_token': AccessTokens.objects.filter()
        }
        return render(request, template_name='accounts/index.html', context=context)