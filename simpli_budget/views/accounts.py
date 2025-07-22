from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import (
    Accounts,
    GroupUser
)
from helpers.plaid import Plaid

class AccountsView(LoginRequiredMixin, View):
    def get(self, request):
        group_id = request.GET.get(
            "group_id",
            GroupUser.objects.filter(
                user_id=request.user.id,
                user_default_group=True
            ).first().group_id
        )
        plaid = Plaid()
        context = {
            'link_token': plaid.get_link_token(),
            'accounts': Accounts.objects.filter(
                group_id=group_id,
                deleted=False,
            ).order_by('name'),
        }
        return render(request, template_name='accounts/index.html', context=context)


class Account(LoginRequiredMixin, View):
    def get(self, request, account_id: str):
        account = Accounts.objects.filter(account_id=account_id).first()
        plaid = Plaid()

        if account is None or not account.user_has_access(request.user):
            return render(request, template_name="error/not_found.html", context={})
        link_token_response = plaid.get_link_token(access_token=account.access_token.access_token)
        context = {
            'account': account,
            'link_token': link_token_response.get('token')
        }
        return render(request, template_name='accounts/account.html', context=context)