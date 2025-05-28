from django.db import models
from django.conf import settings
from django.db.models import QuerySet


class UserAttributes(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, models.DO_NOTHING, primary_key=True)
    show_hidden = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

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

    class Meta:
        managed = False
        db_table = 'date'


class CategoryType(models.Model):
    category_type_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    category_type_name = models.CharField(max_length=64)
    invert_amounts = models.BooleanField(blank=True, null=True)
    hidden = models.BooleanField(blank=True, null=True)
    sort_index = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"budget"."category_type"'
        unique_together = (('user_id', 'category_type_name'),)


class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_type = models.ForeignKey(CategoryType, models.DO_NOTHING)
    category_name = models.CharField(max_length=128)
    default_monthly_amount = models.TextField(blank=True, null=True)  # This field type is a guess.
    sort_index = models.IntegerField()
    hidden = models.BooleanField()
    deleted = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def monthly_amount(self, year_month: int) -> float:
        monthly_amount = 0
        transactions = self.transactions_set.filter(date__year_month=year_month)
        for transaction in transactions:
            monthly_amount += transaction.amount
        if self.category_type.invert_amounts:
            monthly_amount = -monthly_amount
        return round(monthly_amount, 2)

    class Meta:
        managed = False
        db_table = '"budget"."categories"'
        unique_together = (('category_type', 'category_name'),)


class CategoryMonth:
    def __init__(self, category: Categories, year_month: int):
        self.category = category
        self.month_total = category.monthly_amount(year_month)
        self.month_total_display = '${:,.2f}'.format(self.month_total)


class CategoryTypeMonth:
    def __init__(self, category_type: CategoryType, year_month: int, include_hidden: bool = False):
        self.year_month = year_month
        self.category_type = category_type
        self.categories = self.get_month_categories(include_hidden)

    def get_month_categories(self, include_hidden: bool) -> list:
        if include_hidden:
            categories = self.category_type.categories_set.all()
        else:
            categories = self.category_type.categories_set.filter(hidden=False)
        return [
            CategoryMonth(
                category=category,
                year_month=self.year_month
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

class AccessTokens(models.Model):
    access_token_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    access_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    institution_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"plaid"."access_tokens"'


class Accounts(models.Model):
    account_id = models.CharField(primary_key=True, max_length=64)
    access_token = models.ForeignKey(AccessTokens, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=64)
    sub_type = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=128)
    official_name = models.CharField(max_length=128, blank=True, null=True)
    given_name = models.CharField(max_length=128, blank=True, null=True)
    balance = models.TextField(blank=True, null=True)  # This field type is a guess.
    transactions_last_updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"plaid"."accounts"'


class Transactions(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=64)
    pending_transaction = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
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
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    @property
    def amount(self):
        amount = self._amount.replace('$', '')
        amount = amount.replace(',', '')
        return float(amount)

    @property
    def display_amount(self):
        return -1 * self.amount if self.category.category_type.invert_amounts else self.amount

    class Meta:
        managed = False
        db_table = '"plaid"."transactions"'