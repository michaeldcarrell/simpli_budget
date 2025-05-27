from django.db import models


class AccessTokens(models.Model):
    access_token_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=128)
    access_token = models.CharField(max_length=64)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True)
    institution_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'access_tokens'


class Accounts(models.Model):
    account_id = models.CharField(primary_key=True, max_length=64)
    access_token = models.ForeignKey(AccessTokens, models.DO_NOTHING, blank=True, null=True)
    user_id = models.CharField(max_length=128)
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
        db_table = 'accounts'


class Transactions(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=64)
    pending_transaction = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    account = models.ForeignKey(Accounts, models.DO_NOTHING)
    category_id = models.IntegerField(blank=True, null=True)
    merchant_entity_id = models.CharField(max_length=64, blank=True, null=True)
    transaction_type = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=1024)
    merchant_name = models.CharField(max_length=1024, blank=True, null=True)
    iso_currency_code = models.CharField(max_length=3, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    authorized_date = models.DateField(blank=True, null=True)
    pending = models.BooleanField(blank=True, null=True)
    amount = models.TextField(blank=True, null=True)  # This field type is a guess.
    website = models.CharField(max_length=128, blank=True, null=True)
    logo_url = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'transactions'