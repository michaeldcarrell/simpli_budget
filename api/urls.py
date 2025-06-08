from django.urls import path

from api.views import TransactionAPI

urlpatterns = [
    path('transaction', TransactionAPI.as_view(), name='transaction'),
]
