import math

from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Max
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from datetime import datetime as dt
from pytz import UTC
from simpli_budget.models import (
    get_user_group,
    Transactions,
    Tag,
    TagType,
    AccessTokens,
    Accounts,
    Rule,
    Group,
    GroupUser,
    RuleSet,
    CategoryType,
    Categories,
    CategoryMonth,
    TransactionSearch,
    UserAttributes
)
from helpers.plaid import Plaid
from helpers.demo_data import generate_recent_activity


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


class PlaidNewAccountAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group = get_user_group(request.user, request)
        plaid = Plaid()

        exchange_response = plaid.public_token_exchange(public_token=request.data['public_token'])
        if not exchange_response['success']:
            return Response(data={'message': 'Failed to exchange public token'}, status=status.HTTP_400_BAD_REQUEST)

        now = dt.now(tz=UTC)
        access_token = AccessTokens.objects.create(
            group=group,
            access_token=exchange_response['token'],
            institution_id=request.data.get('institution_id'),
            created_at=now,
            updated_at=now,
            deleted=False,
        )

        accounts_response = plaid.get_accounts(access_token.access_token)
        if not accounts_response['success']:
            return Response(data={'message': 'Failed to fetch accounts'}, status=status.HTTP_400_BAD_REQUEST)

        for plaid_account in accounts_response['accounts']:
            balance = plaid_account.get('balances', {}).get('current')
            account_fields = {
                'access_token': access_token,
                'group': group,
                'type': plaid_account.get('type'),
                'sub_type': plaid_account.get('subtype'),
                'name': plaid_account.get('name'),
                'official_name': plaid_account.get('official_name'),
                '_balance': f'{balance:.2f}' if balance is not None else None,
                'deleted': False,
            }
            Accounts.objects.update_or_create(
                account_id=plaid_account['account_id'],
                defaults={**account_fields, 'updated_at': now},
                create_defaults={**account_fields, 'transactions_last_updated_at': now, 'created_at': now, 'updated_at': now},
            )

        return Response(data={'created_count': len(accounts_response['accounts'])}, status=status.HTTP_200_OK)


class OnboardingAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserAttributes.objects.filter(user=request.user).update(onboarding_completed=True)
        return Response(data={'onboarding_completed': True}, status=status.HTTP_200_OK)


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


class CategoryTypeAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group = get_user_group(request.user, request)
        if group is None or not GroupUser.objects.filter(group=group, user=request.user).exists():
            return Response(data={'message': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        category_type_name = (request.data.get('category_type_name') or '').strip()
        if not category_type_name:
            return Response(data={'message': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if CategoryType.objects.filter(group=group, category_type_name=category_type_name).exists():
            return Response(data={'message': 'A category group with that name already exists'}, status=status.HTTP_400_BAD_REQUEST)

        next_sort_index = CategoryType.objects.filter(group=group).aggregate(Max('sort_index'))['sort_index__max']
        next_sort_index = 0 if next_sort_index is None else next_sort_index + 1

        now = dt.now(tz=UTC)
        category_type = CategoryType.objects.create(
            group=group,
            category_type_name=category_type_name,
            invert_amounts=False,
            hidden=False,
            sort_index=next_sort_index,
            created_at=now,
            updated_at=now,
        )
        return Response(data=category_type.to_dict(), status=status.HTTP_201_CREATED)


class CategoryAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        category_type = CategoryType.objects.filter(
            category_type_id=request.data.get('category_type_id')
        ).first()
        if category_type is None or not category_type.user_has_access(request.user):
            return Response(data={'message': 'Category type not found'}, status=status.HTTP_404_NOT_FOUND)

        category_name = (request.data.get('category_name') or '').strip()
        if not category_name:
            return Response(data={'message': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        default_monthly_amount = float(request.data.get('default_monthly_amount') or 0)
        now = dt.now(tz=UTC)

        existing_category = Categories.objects.filter(category_type=category_type, category_name=category_name).first()
        if existing_category is not None:
            if not existing_category.deleted:
                return Response(data={'message': 'A category with that name already exists'}, status=status.HTTP_400_BAD_REQUEST)
            # Re-adding a category that was previously removed - restore it in place rather
            # than erroring, since the name is still taken by its (soft-deleted) old row.
            existing_category.deleted = False
            existing_category._default_monthly_amount = f"{default_monthly_amount:.2f}"
            existing_category.updated_at = now
            existing_category.save()
            return Response(data=existing_category.to_dict(), status=status.HTTP_200_OK)

        next_sort_index = (
            Categories.objects.filter(category_type=category_type).aggregate(Max('sort_index'))['sort_index__max']
        )
        next_sort_index = 0 if next_sort_index is None else next_sort_index + 1

        category = Categories.objects.create(
            category_type=category_type,
            category_name=category_name,
            _default_monthly_amount=f"{default_monthly_amount:.2f}",
            sort_index=next_sort_index,
            hidden=False,
            deleted=False,
            created_at=now,
            updated_at=now,
        )
        return Response(data=category.to_dict(), status=status.HTTP_201_CREATED)

    def delete(self, request, category_id: int):
        category = Categories.objects.filter(category_id=category_id).first()
        if category is None or not category.user_has_access(request.user):
            return Response(data={'message': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        now = dt.now(tz=UTC)
        with db_transaction.atomic():
            category.deleted = True
            category.updated_at = now
            category.save()

            # A deleted category shouldn't keep auto-categorizing new transactions.
            RuleSet.objects.filter(default_category_id=category_id).update(active=False, updated_at=now)
            Rule.objects.filter(set__default_category_id=category_id).update(active=False, updated_at=now)

        return Response(data=category.to_dict(), status=status.HTTP_200_OK)


class TagTypeAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group = get_user_group(request.user, request)
        if group is None or not GroupUser.objects.filter(group=group, user=request.user).exists():
            return Response(data={'message': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        name = (request.data.get('name') or '').strip()
        if not name:
            return Response(data={'message': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if TagType.objects.filter(group=group, name=name).exists():
            return Response(data={'message': 'A tag type with that name already exists'}, status=status.HTTP_400_BAD_REQUEST)

        tag_type = TagType.objects.create(group=group, name=name, created_at=dt.now(tz=UTC))
        return Response(data=tag_type.to_dict(), status=status.HTTP_201_CREATED)


class TagAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group = get_user_group(request.user, request)
        if group is None or not GroupUser.objects.filter(group=group, user=request.user).exists():
            return Response(data={'message': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        name = (request.data.get('name') or '').strip()
        if not name:
            return Response(data={'message': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        tag_type = TagType.objects.filter(tag_type_id=request.data.get('tag_type_id'), group=group).first()
        if tag_type is None:
            return Response(data={'message': 'Tag type not found'}, status=status.HTTP_404_NOT_FOUND)

        existing_tag = Tag.objects.filter(group=group, name=name).first()
        if existing_tag is not None:
            if not existing_tag.deleted:
                return Response(data={'message': 'A tag with that name already exists'}, status=status.HTTP_400_BAD_REQUEST)
            # Re-adding a tag that was previously removed - restore it in place rather than
            # erroring, since the name is still taken by its (soft-deleted) old row.
            existing_tag.deleted = False
            existing_tag.tag_type = tag_type
            existing_tag.save()
            return Response(data=existing_tag.to_dict(), status=status.HTTP_200_OK)

        tag = Tag.objects.create(group=group, tag_type=tag_type, name=name, deleted=False)
        return Response(data=tag.to_dict(), status=status.HTTP_201_CREATED)

    def delete(self, request, tag_id: int):
        tag = Tag.objects.filter(tag_id=tag_id).first()
        if tag is None or not tag.user_has_access(request.user):
            return Response(data={'message': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)

        tag.deleted = True
        tag.save()
        return Response(data=tag.to_dict(), status=status.HTTP_200_OK)


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


class DemoGenerateActivityAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if settings.DEMO_GROUP_ID is None:
            return Response(data={'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        group = Group.objects.filter(group_id=settings.DEMO_GROUP_ID).first()
        if group is None or not group.user_has_access(request.user):
            return Response(data={'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        transactions = generate_recent_activity(group)
        # Demo accounts have no real Plaid access_token, and Accounts.to_dict()/Transactions.to_dict()
        # assume one exists, so just report a count rather than serializing the created rows.
        return Response(data={'created_count': len(transactions)}, status=status.HTTP_200_OK)


