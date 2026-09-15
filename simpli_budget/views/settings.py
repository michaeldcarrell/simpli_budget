from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryType, GroupUser, NotificationCategories, UserAttributes


class Settings(LoginRequiredMixin, View):
    def get(self, request):
        group_id = request.GET.get(
            "group_id",
            GroupUser.objects.filter(
                user_id=request.user.id,
                user_default_group=True
            ).first().group_id
        )
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
            "title": "Settings",
            "discord_user_id": user_attributes.discord_user_id,
            "sections": sections,
        }
        return render(request, template_name="settings/index.html", context=context)
