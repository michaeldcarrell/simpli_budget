from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import Transactions, Categories
from helpers import Input


class Transaction(LoginRequiredMixin, View):
    def get(self, request, transaction_id: str):
        transaction = Transactions.objects.get(transaction_id=transaction_id)
        categories = Categories.objects.filter(category_type__user_id=request.user.id)
        context = {
            'transaction': transaction,
            'categories': categories,
            'inputs': [
                Input(
                    id='account',
                    label='Account',
                    type='text',
                    value=transaction.account.name,
                    disabled=True
                ),
                Input(
                    id='date',
                    label='Date',
                    type='text',
                    value=transaction.date.date.strftime('%Y-%m-%d'),
                    disabled=True
                ),
                Input(
                    id='payee',
                    label='Payee',
                    type='text',
                    value=transaction.merchant_name,
                    disabled=True
                ),
                Input(
                    id='amount',
                    label='Amount',
                    type='text',
                    value=transaction.display_amount,
                    disabled=True
                )
            ]
        }
        return render(request, template_name="transaction/index.html", context=context)