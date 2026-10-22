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
from helpers.airflow import refresh_allowed

class CurrentTransactionTag(NamedTuple):
    tag_id: int
    name: str
    deleted: bool
    transaction_tag_id: int | None = None


class Transaction(LoginRequiredMixin, View):
    def get(self, request, transaction_id: str):
        transaction = Transactions.objects.filter(transaction_id=transaction_id).first()
        if transaction is None or not transaction.user_has_access(request.user):
            return render(
                request,
                template_name="404.html",
                context={
                    "message": "Transaction not found"
                }
            )
        group_id = transaction.category.category_type.group_id
        categories = Categories.objects.filter(
            category_type__group_id=group_id,
            deleted=False,
        ).order_by("category_type__sort_index", "sort_index")
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

        amount = transaction.amount
        is_inflow = amount < 0
        context = {
            'title': transaction.name,
            'transaction': transaction,
            'categories': categories,
            'transaction_tags': current_transaction_tags,
            'amount_display': f"{'+' if is_inflow else ''}${abs(amount):,.2f}",
            'is_inflow': is_inflow,
            'details': [
                ('Date', transaction.date.date.strftime('%a %b %-d, %Y')),
                ('Account', transaction.account.display_name),
                ('Payee', transaction.merchant_name or '—'),
            ],
        }
        return render(request, template_name="transaction/index.html", context=context)


class TransactionSearch(LoginRequiredMixin, View):
    def get(self, request):
        group_id = get_user_group(request.user, request)
        categories = Categories.objects.filter(
            category_type__group_id=group_id,
            deleted=False,
        ).order_by("category_type__sort_index", "sort_index")
        accounts = Accounts.objects.filter(group_id=group_id, deleted=False)
        tags = Tag.objects.filter(group_id=group_id, deleted=False)
        context = {
            'categories': categories,
            'accounts': accounts,
            'tags': tags,
            'title': 'Transaction Search',
            'refresh_enabled': refresh_allowed(request.user, group_id),
        }
        return render(request, template_name="transaction/search.html", context=context)