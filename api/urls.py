from django.urls import path

from api.views import TransactionCategoryAPI, TransactionTagsAPI

urlpatterns = [
    path('transaction/<str:transaction_id>/category', TransactionCategoryAPI.as_view(), name='Transaction Category'),
    path('transaction/<str:transaction_id>/tags', TransactionTagsAPI.as_view(), name='Transaction Tags'),
]
