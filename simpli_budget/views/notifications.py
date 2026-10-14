from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryType, get_user_group, NotificationCategories, UserAttributes


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

        context = {
            "title": "Notifications",
            "discord_user_id": user_attributes.discord_user_id,
            "discord_notifications_enabled": user_attributes.discord_notifications_enabled,
            "email_notifications_enabled": user_attributes.email_notifications_enabled,
            "notification_frequency_days": user_attributes.notification_frequency_days,
            "sections": sections,
        }
        return render(request, template_name="notifications/index.html", context=context)
