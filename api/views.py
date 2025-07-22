from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from datetime import datetime as dt
from simpli_budget.models import Transactions, Tag, AccessTokens, Accounts
from helpers.plaid import Plaid


class TransactionCategoryAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, transaction_id: str):
        transaction = Transactions.objects.get(transaction_id=transaction_id)
        if not transaction.user_has_access(request.user):
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
        if not transaction.user_has_access(request.user):
            return Response(data={'message': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        transaction_tags = transaction.transactiontag_set.all()
        for tag_id in request.data['tag_ids']:
            if not transaction_tags.filter(tag_id=tag_id).exists():
                if not Tag.objects.filter(tag_id=tag_id).first().user_has_access(request.user):
                    return Response(data={'message': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)
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


class PlaidLinkTokenAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, account_id: str):
        access_token = Accounts.objects.filter(
            account_id=account_id,
        ).first().access_token
        if not access_token.user_has_access(request.user):
            return Response(data={'message': 'Access token not found'}, status=status.HTTP_404_NOT_FOUND)

        plaid = Plaid()
        link_token = plaid.get_link_token(access_token=access_token.access_token)
        return Response(data={'link_token': link_token}, status=status.HTTP_200_OK)


class PlaidPublicTokenExchangeAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, access_token_id: int):
        access_token = AccessTokens.objects.get(access_token_id=access_token_id)
        plaid = Plaid()
        exchange_response = plaid.public_token_exchange(public_token=request.data['public_token'])
        if exchange_response['success']:
            token = exchange_response['token']
            access_token.access_token = token
            access_token.save()
        if not access_token.user_has_access(request.user):
            return Response(data={'message': 'Access token not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data=access_token.to_dict(), status=status.HTTP_200_OK)
