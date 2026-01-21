import math

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from datetime import datetime as dt
from simpli_budget.models import (
    get_user_group,
    Transactions,
    Tag,
    AccessTokens,
    Accounts,
    Rule,
    GroupUser,
    RuleSet,
    CategoryMonth,
    TransactionSearch
)
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
            access_token.updated_at = dt.now()
            access_token.save()
        if not access_token.user_has_access(request.user):
            return Response(data={'message': 'Access token not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data=access_token.to_dict(), status=status.HTTP_200_OK)


class RuleSetAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        rule_set_name = request.data['name']
        category_id = request.data['category_id']
        user_default_group = GroupUser.objects.filter(
            user_id=request.user.id,
            user_default_group=True
        ).first()
        group_id = request.data.get("group_id", user_default_group.group_id)
        rule_set = RuleSet.objects.create(
            name=rule_set_name,
            group_id=group_id,
            default_category_id=category_id
        )
        rule_set.save()
        return Response(data=rule_set.to_dict(), status=status.HTTP_201_CREATED)

    def put(self, request, rule_set_id: int):
        rule_set = RuleSet.objects.get(set_id=rule_set_id)
        if not rule_set.user_has_access(request.user):
            return Response(data={'message': 'Rule set not found'}, status=status.HTTP_404_NOT_FOUND)
        rule_set.default_category_id = request.data['category_id']
        rule_set.save()
        return Response(data=rule_set.to_dict(), status=status.HTTP_200_OK)


class RuleAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, rule_set_id: int):
        rule_set = RuleSet.objects.get(set_id=rule_set_id)
        if not rule_set.user_has_access(request.user):
            return Response(data={'message': 'Rule set not found'}, status=status.HTTP_404_NOT_FOUND)
        rule_match_type_id = request.data['match_type_id']
        match_string = request.data['match_string']
        match_number = request.data['match_number']
        rule = Rule.objects.create(
            set_id=rule_set_id,
            match_type_id=rule_match_type_id,
            match_string=match_string,
            match_number=match_number,
        )
        rule.save()
        return Response(data=rule.to_dict(), status=status.HTTP_201_CREATED)


class CategoryMonthAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, category_id: int):
        month_id = request.data['year_month']
        category_month = CategoryMonth.objects.filter(
            category_id=category_id,
            year_month=month_id
        ).first()
        if category_month is None:
            category_month = CategoryMonth.objects.create(
                category_id=category_id,
                year_month=month_id,
            )
        category_month.amount = int(request.data['amount'])
        category_month.save()
        return Response(data=category_month.to_dict(), status=status.HTTP_200_OK)


class TransactionsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def __transactions_response(
            self,
            request,
            page_number: int,
            page_size: int,
            ordering: dict = None,
            filters: dict = None,
    ):
        if ordering is None or ordering == {}:
            ordering = {'column': 'date', 'direction': 'desc'}
        ordering_map = {
            'display_amount': '_amount',
            'category.category_name': 'category_id'
        }
        ordering_column = ordering_map.get(ordering['column'], ordering['column'])
        ordering_direction = '-' if ordering.get('direction', 'asc') == 'desc' else ''
        ordering = f'{ordering_direction}{ordering_column}'

        if filters is None:
            filters = {
                'transactiontag': 'is not None'
            }
        filters['group_id'] = get_user_group(request.user, request).group_id
        offset = (page_number - 1) * page_size
        page_end = offset + page_size
        group_query_set = (
            TransactionSearch
                .objects
                .filter(**filters)
                .order_by(ordering)
        )

        total_records = len(group_query_set)

        max_page = math.ceil(total_records / page_size)
        has_next_page = max_page > page_number

        transactions = [
            {
                'date': transaction.date.isoformat(),
                'name': transaction.name,
                'amount': transaction.amount,
                'account': transaction.account,
                'category': transaction.category,
                'tags': transaction.tags
            } for transaction in group_query_set[offset:page_end]
        ]

        return Response(
            data={
                "transactions": transactions,
                "paging": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_pages": max_page,
                    "total_records": total_records,
                    "has_next_page": has_next_page,
                    "next_page": page_number + 1 if has_next_page else None,
                },
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        return self.__transactions_response(request, page_number, page_size)

    def post(self, request):
        body = request.data
        page_number = body.get('page', 1)
        page_size = body.get('page_size', 10)

        ordering = body.get('ordering', {
            'column': 'date',
            'direction': 'desc'
        })

        filter_mapping = {
            'name': 'name__icontains',
            'display_amount': '_amount__icontains',
            'tags': 'tags__icontains',
        }

        input_filters = body.get('filters', {})
        filters = {}

        for key, search_value in input_filters.items():
            if key == 'date':
                bounds = search_value.split(' - ')
                filters['date__gte'] = dt.strptime(bounds[0], '%m/%d/%Y').strftime('%Y-%m-%d')
                filters['date__lte'] = dt.strptime(bounds[1], '%m/%d/%Y').strftime('%Y-%m-%d')
                continue
            elif key == 'category.category_name':
                if int(search_value) != -999:
                    filters['category_id'] = int(search_value)
                continue
            elif key == 'account':
                if search_value != '-999':
                    filters['account_id'] = search_value
                continue
            elif key == 'tags':
                if search_value != '-999':
                    filters['tags__icontains'] = search_value
                continue
            if key in filter_mapping:
                filters[filter_mapping[key]] = search_value
            else:
                filters[key] = search_value

        return self.__transactions_response(request, page_number, page_size, ordering, filters)



