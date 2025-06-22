from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from datetime import datetime as dt
from simpli_budget.models import Transactions


class TransactionCategoryAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id: str):
        transaction = Transactions.objects.get(transaction_id=transaction_id)
        if request.user.id != transaction.user.id:
            return Response(data={'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        transaction.category_id = int(request.data['category_id'])
        transaction.updated_at = dt.now()
        transaction.save()
        return_transaction = transaction.to_dict()
        return Response(data=return_transaction, status=status.HTTP_200_OK)


class TransactionTagsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id: str):
        transaction = Transactions.objects.get(transaction_id=transaction_id)
        if request.user.id != transaction.user.id:
            return Response(data={'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        transaction_tags = transaction.transactiontag_set.all()
        for tag_id in request.data['tag_ids']:
            if not transaction_tags.filter(tag_id=tag_id).exists():
                transaction.transactiontag_set.create(
                    tag_id=tag_id,
                )
                transaction.save()
        for transaction_tag in transaction_tags:
            if transaction_tag.tag_id not in request.data['tag_ids']:
                transaction_tag.delete()
        return Response(
            data=[tag.to_dict() for tag in transaction.transactiontag_set.all()],
            status=status.HTTP_200_OK
        )