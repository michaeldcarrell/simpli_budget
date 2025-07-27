from django.urls import path

from api.views import (
    TransactionCategoryAPI,
    TransactionTagsAPI,
    PlaidLinkTokenAPI,
    PlaidPublicTokenExchangeAPI,
    RuleSetAPI,
    RuleAPI
)
urlpatterns = [
    path('transaction/<str:transaction_id>/category', TransactionCategoryAPI.as_view(), name='Transaction Category'),
    path('transaction/<str:transaction_id>/tags', TransactionTagsAPI.as_view(), name='Transaction Tags'),
    path('accounts/<str:account_id>/link_token', PlaidLinkTokenAPI.as_view(), name='Plaid Link Token'),
    path('access_token/<int:access_token_id>', PlaidPublicTokenExchangeAPI.as_view(), name='Plaid Public Token Exchange'),
    path('rule_set', RuleSetAPI.as_view(), name='Rule Set'),
    path('rule_set/<int:rule_set_id>', RuleSetAPI.as_view(), name='Rule Set'),
    path('rule_set/<int:rule_set_id>/rule', RuleAPI.as_view(), name='Rule'),
]
