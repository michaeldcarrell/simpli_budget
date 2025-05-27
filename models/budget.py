from django.db import models


class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_type = models.ForeignKey('CategoryType', models.DO_NOTHING)
    category_name = models.CharField(max_length=128)
    default_monthly_amount = models.TextField(blank=True, null=True)  # This field type is a guess.
    sort_index = models.IntegerField()
    hidden = models.BooleanField()
    deleted = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'categories'
        unique_together = (('category_type', 'category_name'),)


class CategoryType(models.Model):
    category_type_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=128)
    category_type_name = models.CharField(max_length=64)
    invert_amounts = models.BooleanField(blank=True, null=True)
    hidden = models.BooleanField(blank=True, null=True)
    sort_index = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'category_type'
        unique_together = (('user_id', 'category_type_name'),)
