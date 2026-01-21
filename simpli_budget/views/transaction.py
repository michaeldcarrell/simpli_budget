from typing import NamedTuple

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import (
    Transactions,
    Categories,
    Tag,
    GroupUser,
    get_user_group,
    Accounts,
)
from helpers import Input

class CurrentTransactionTag(NamedTuple):
    tag_id: int
    name: str
    deleted: bool
    transaction_tag_id: int | None = None


class Transaction(LoginRequiredMixin, View):
    def get(self, request, transaction_id: str):
        transaction = Transactions.objects.get(transaction_id=transaction_id)
        if not transaction.user_has_access(request.user):
            return render(
                request,
                template_name="404.html",
                context={
                    "message": "Transaction not found"
                }
            )
        group_id = transaction.category.category_type.group_id
        categories = Categories.objects.filter(category_type__group_id=group_id).order_by("category_type__sort_index", "sort_index")
        tags = Tag.objects.filter(group_id=group_id)
        current_transaction_tags = []
        for tag in tags:
            searched_tag = transaction.transactiontag_set.filter(tag_id=tag.tag_id)
            if searched_tag.exists():
                transaction_tag_id = searched_tag.get().transaction_tag_id
            else:
                transaction_tag_id = None
            current_transaction_tag = CurrentTransactionTag(
                transaction_tag_id=transaction_tag_id,
                tag_id=tag.tag_id,
                name=tag.name,
                deleted=tag.deleted
            )

            current_transaction_tags.append(current_transaction_tag)

        context = {
            'title': transaction.name,
            'transaction': transaction,
            'categories': categories,
            'transaction_tags': current_transaction_tags,
            'inputs': [
                Input(
                    id='transaction_name',
                    label='Transaction Name',
                    type='text',
                    value=transaction.name,
                    disabled=True
                ),
                Input(
                    id='account',
                    label='Account',
                    type='text',
                    value=transaction.account.given_name,
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


class TransactionSearch(LoginRequiredMixin, View):
    def get(self, request):
        group_id = get_user_group(request.user, request)
        categories = Categories.objects.filter(category_type__group_id=group_id).order_by("category_type__sort_index", "sort_index")
        accounts = Accounts.objects.filter(group_id=group_id, deleted=False)
        tags = Tag.objects.filter(group_id=group_id, deleted=False)
        context = {
            'categories': categories,
            'accounts': accounts,
            'tags': tags,
            'title': 'Transaction Search'
        }
        return render(request, template_name="transaction/search.html", context=context)