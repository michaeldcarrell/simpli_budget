from django.db import models
from django.conf import settings
from django.db.models import QuerySet
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import relativedelta
from pytz import UTC


def money_as_float(field):
    if field is None:
        return None
    val = field.replace("$", "")
    val = val.replace(",", "")
    return float(val)

def money_display(field, amount_inverted: bool = False):
    value = -1 * field if amount_inverted else field
    return f"${value:,.2f}"

def user_to_dict(user: settings.AUTH_USER_MODEL) -> dict:
    return {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined.isoformat(),
    }


class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    class Meta:
        managed = False
        db_table = '"budget"."group"'

    def to_dict(self):
        return {
            'group_id': self.group_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self, user=user).exists()

class GroupUser(models.Model):
    group_user_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.DO_NOTHING, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=False)
    user_default_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        managed = False
        db_table = '"budget"."group_user"'

    def to_dict(self):
        return {
            'group_user_id': self.group_user_id,
            'group': self.group.to_dict(),
            'user': user_to_dict(self.user),
            'created_at': self.created_at.isoformat(),
        }


class UserAttributes(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, models.DO_NOTHING, primary_key=True)
    show_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=dt.now)
    updated_at = models.DateTimeField(default=dt.now)

    class Meta:
        managed = False
        db_table = 'user_attributes'


class Date(models.Model):
    date = models.DateField(primary_key=True, unique=True)
    date_key = models.IntegerField(unique=True)
    date_of_month = models.IntegerField()
    day_of_week = models.IntegerField()
    weekday_name_short = models.TextField()
    weekday_name = models.TextField()
    is_weekend = models.TextField()
    week_of_month = models.IntegerField()
    week_of_year = models.IntegerField()
    day_of_year = models.IntegerField()
    iso_week_of_year = models.IntegerField()
    month_number = models.IntegerField()
    month_name_short = models.TextField()
    month_name = models.TextField()
    days_in_month = models.IntegerField()
    year = models.IntegerField()
    year_month = models.IntegerField()
    is_daylight_savings = models.TextField()
    is_holiday = models.TextField()
    holiday_name = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    @property
    def year_month_display(self):
        return f"{self.month_name} - {self.year}"

    @property
    def year_month_short_display(self):
        return f"{self.month_name_short} - {self.year}"

    @property
    def date_display(self):
        return f"{self.date.year}-{self.date.month}-{self.date.day}"

    class Meta:
        managed = False
        db_table = 'date'


class CategoryType(models.Model):
    category_type_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    category_type_name = models.CharField(max_length=64)
    invert_amounts = models.BooleanField(blank=True, null=True)
    hidden = models.BooleanField(blank=True, null=True)
    sort_index = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self) -> dict:
        return_dict = {
            'category_type_id': self.category_type_id,
            'group': self.group.to_dict(),
            'category_type_name': self.category_type_name,
            'invert_amounts': self.invert_amounts,
            'hidden': self.hidden,
            'sort_index': self.sort_index,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        return return_dict

    class Meta:
        managed = False
        db_table = '"budget"."category_type"'
        unique_together = (('group_id', 'category_type_name'),)

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self.group, user=user).exists()


class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_type = models.ForeignKey(CategoryType, models.DO_NOTHING)
    category_name = models.CharField(max_length=128)
    _default_monthly_amount = models.TextField(blank=True, null=True, db_column='default_monthly_amount')  # This field type is a guess.
    sort_index = models.IntegerField()
    hidden = models.BooleanField()
    deleted = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    @property
    def default_monthly_amount(self):
        return money_as_float(self._default_monthly_amount)

    @property
    def budget_display(self):
        return money_display(self.default_monthly_amount if self.default_monthly_amount else 0)

    def to_dict(self) -> dict:
        return {
            'category_id': self.category_id,
            'category_type': self.category_type.to_dict(),
            'category_name': self.category_name,
            'default_monthly_amount': self.default_monthly_amount,
            'sort_index': self.sort_index,
            'hidden': self.hidden,
            'deleted': self.deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def monthly_amount(self, year_month: int) -> float:
        monthly_amount = 0
        transactions = self.transactions_set.filter(
            date__year_month=year_month,
            account__deleted=False,
            deleted=False,
        )
        for transaction in transactions:
            monthly_amount += transaction.amount
        if self.category_type.invert_amounts:
            monthly_amount = -monthly_amount
        return round(monthly_amount, 2)

    class Meta:
        managed = False
        db_table = '"budget"."categories"'
        unique_together = (('category_type', 'category_name'),)

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group_id=self.category_type.group_id, user=user).exists()


class Month:
    def __init__(self, year_month: int):
        self.year_month = year_month
        self.start_of_month_date = Date.objects.filter(year_month=year_month).order_by('date').first()
        self.end_of_month_date = Date.objects.filter(year_month=year_month).order_by('date').last()
        self.name = f"{self.start_of_month_date.month_name}, {self.start_of_month_date.year}"
        self.name_short = f"{self.start_of_month_date.month_name_short}, {self.start_of_month_date.year}"
        self.__start_dt = dt(year=self.start_of_month_date.year, month=self.start_of_month_date.month_number, day=1)
        self.__next_month_dt = self.__start_dt + relativedelta(months=1)
        self.__last_month_dt = self.__start_dt - relativedelta(months=1)

    @property
    def next_month(self):
        next_month_year = self.__next_month_dt.year
        next_month_month = str(self.__next_month_dt.month).zfill(2)
        return Month(year_month=int(f'{next_month_year}{next_month_month}'))

    @property
    def last_month(self):
        last_month_year = self.__last_month_dt.year
        last_month_month = str(self.__last_month_dt.month).zfill(2)
        return Month(year_month=int(f'{last_month_year}{last_month_month}'))


class CategoryMonth:
    def __init__(self, category: Categories, year_month: int):
        self.category = category
        self.month = Month(year_month=year_month)
        self.month_total = category.monthly_amount(year_month)
        self.month_total_display = '${:,.2f}'.format(self.month_total)
        self.transactions = category.transactions_set.filter(
            date__year_month=year_month,
            account__deleted=False,
            deleted=False,
        ).order_by('-date')


class CategoryTypeMonth:
    def __init__(self, category_type: CategoryType, year_month: int, include_hidden: bool = False):
        self.month = Month(year_month=year_month)
        self.category_type = category_type
        self.categories = self.get_month_categories(include_hidden)

    def get_month_categories(self, include_hidden: bool) -> list[CategoryMonth]:
        if include_hidden:
            categories = self.category_type.categories_set.all()
        else:
            categories = self.category_type.categories_set.filter(
                hidden=False
            )
        return [
            CategoryMonth(
                category=category,
                year_month=self.month.year_month
            ) for category in categories
        ]

class BudgetMonth:
    def __init__(self, category_types: QuerySet, year_month: int, include_hidden: bool = False):
        if not include_hidden:
            category_types = category_types.filter(hidden=False)
        self.category_types = [
            CategoryTypeMonth(
                category_type=category_type,
                year_month=year_month,
                include_hidden=include_hidden
            ) for category_type in category_types
        ]
        self.year_month = year_month
        self.month = Month(year_month=year_month)
        net = self.__get_net()
        self.income = net['income']
        self.expenses = net['expenses']

    def __get_net(self):
        income = 0
        expenses = 0
        for category_type in self.category_types:
            expense = not category_type.category_type.invert_amounts
            for category_month in category_type.categories:
                for transaction in category_month.transactions:
                    if expense:
                        expenses += transaction.amount
                    else:
                        income += transaction.amount
        return {
            'income': money_display(income, amount_inverted=True),
            'expenses': money_display(expenses),
        }

class AccessTokens(models.Model):
    access_token_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    access_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    institution_id = models.CharField(max_length=64, blank=True, null=True)

    def to_dict(self, public: bool = True):
        return_dict = {
            "access_token_id": self.access_token_id,
            "group": self.group.to_dict(),
            "access_token": self.access_token,
            "institution_id": self.institution_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted": self.deleted,
        }
        if public:
            del return_dict['access_token']
        return return_dict

    class Meta:
        managed = False
        db_table = '"plaid"."access_tokens"'

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self.group, user=user).exists()


class Accounts(models.Model):
    account_id = models.CharField(primary_key=True, max_length=64)
    access_token = models.ForeignKey(AccessTokens, models.DO_NOTHING, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    type = models.CharField(max_length=64)
    sub_type = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=128)
    official_name = models.CharField(max_length=128, blank=True, null=True)
    given_name = models.CharField(max_length=128, blank=True, null=True)
    _balance = models.TextField(blank=True, null=True, db_column='balance')  # This field type is a guess.
    transactions_last_updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)

    @property
    def balance(self):
        return money_as_float(self._balance)

    def to_dict(self, public: bool = True):
        return_dict = {
            'account_id': self.account_id,
            'access_token': self.access_token.to_dict(public=public),
            'group': self.group.to_dict(),
            'type': self.type,
            'sub_type': self.sub_type,
            'name': self.name,
            'official_name': self.official_name,
            'given_name': self.given_name,
            'balance': self.balance,
            'transactions_last_updated_at': self.transactions_last_updated_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted': self.deleted,
        }
        if public:
            del return_dict['access_token']
        return return_dict

    class Meta:
        managed = False
        db_table = '"plaid"."accounts"'

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self.group, user=user).exists()

    @property
    def display_name(self):
        if self.given_name:
            return self.given_name
        elif self.official_name:
            return self.official_name
        else:
            return self.name

    @property
    def display_balance(self):
        return money_display(field=self.balance)

    @property
    def out_of_date(self):
        return (dt.now(tz=UTC) - self.updated_at) > timedelta(days=3)


class Transactions(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=64)
    pending_transaction_id = models.CharField(max_length=64, blank=True, null=True)
    account = models.ForeignKey(Accounts, models.DO_NOTHING)
    category = models.ForeignKey(Categories, models.DO_NOTHING)
    merchant_entity_id = models.CharField(max_length=64, blank=True, null=True)
    transaction_type = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=1024)
    merchant_name = models.CharField(max_length=1024, blank=True, null=True)
    iso_currency_code = models.CharField(max_length=3, blank=True, null=True)
    date = models.ForeignKey(Date, models.DO_NOTHING, to_field="date", db_column="date")
    authorized_date = models.DateField(blank=True, null=True)
    pending = models.BooleanField(blank=True, null=True)
    _amount = models.TextField(blank=True, null=True, db_column="amount")
    website = models.CharField(max_length=128, blank=True, null=True)
    logo_url = models.CharField(max_length=128, blank=True, null=True)
    deleted = models.BooleanField(blank=False, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    @property
    def amount(self):
        return money_as_float(self._amount)

    @property
    def display_amount(self):
        return money_display(
            field=self.amount,
            amount_inverted=self.category.category_type.invert_amounts
        )

    @property
    def group(self):
        return self.account.group

    def to_dict(self, public: bool = True):
        return_dict = {
            'transaction_id': self.transaction_id,
            'pending_transaction_id': self.pending_transaction_id,
            'account': self.account.to_dict(public=public),
            'category': self.category.to_dict(),
            'merchant_entity_id': self.merchant_entity_id,
            'transaction_type': self.transaction_type,
            'name': self.name,
            'merchant_name': self.merchant_name,
            'iso_currency_code': self.iso_currency_code,
            'date': self.date.date_display,
            'authorized_date': self.authorized_date.isoformat() if self.authorized_date else None,
            'pending': self.pending,
            'amount': self.amount,
            'website': self.website,
            'logo_url': self.logo_url,
            'group': self.group.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        return return_dict

    class Meta:
        managed = False
        db_table = '"plaid"."transactions"'

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self.account.group, user=user).exists()


class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=32, null=False)
    deleted = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    class Meta:
        managed = False
        db_table = '"budget"."tag"'

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'group': self.group.to_dict(),
            'name': self.name,
            'deleted': self.deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def user_has_access(self, user: settings.AUTH_USER_MODEL) -> bool:
        return GroupUser.objects.filter(group=self.group, user=user).exists()


class TransactionTag(models.Model):
    transaction_tag_id = models.AutoField(primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, null=False)
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        managed = False
        db_table = '"budget"."transaction_tag"'

    def to_dict(self):
        return {
            'transaction_tag_id': self.transaction_tag_id,
            'tag': self.tag.to_dict(),
            'transaction': self.transaction.to_dict(),
            'created_at': self.created_at.isoformat(),
        }
