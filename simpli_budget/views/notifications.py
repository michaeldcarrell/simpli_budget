from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import (
    Accounts,
    CategoryType,
    get_user_group,
    NotificationAccounts,
    NotificationCategories,
    UserAttributes,
)


class Notifications(LoginRequiredMixin, View):
    def get(self, request):
        group_id = get_user_group(request.user, request).group_id
        user_attributes, _ = UserAttributes.objects.get_or_create(user=request.user)
        subscribed_category_ids = set(
            NotificationCategories.objects.filter(
                user_attributes=user_attributes
            ).values_list("category_id", flat=True)
        )

        category_types = CategoryType.objects.filter(
            group_id=group_id,
            hidden=False,
        ).order_by("sort_index")
        sections = []
        for category_type in category_types:
            categories = category_type.categories_set.filter(
                deleted=False,
                hidden=False,
            ).order_by("sort_index")
            for category in categories:
                category.is_subscribed = category.category_id in subscribed_category_ids
            sections.append({
                "category_type": category_type,
                "categories": categories,
            })

        subscribed_account_ids = set(
            NotificationAccounts.objects.filter(
                user_attributes=user_attributes
            ).values_list("account_id", flat=True)
        )
        accounts = Accounts.objects.filter(
            group_id=group_id,
            deleted=False,
        ).order_by("name")
        for account in accounts:
            account.is_subscribed = account.account_id in subscribed_account_ids

        context = {
            "title": "Notifications",
            "discord_user_id": user_attributes.discord_user_id,
            "discord_notifications_enabled": user_attributes.discord_notifications_enabled,
            "email_notifications_enabled": user_attributes.email_notifications_enabled,
            "notification_frequency_days": user_attributes.notification_frequency_days,
            "bank_login_alerts_enabled": user_attributes.bank_login_alerts_enabled,
            "sections": sections,
            "accounts": accounts,
        }
        return render(request, template_name="notifications/index.html", context=context)
