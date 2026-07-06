from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryType, GroupUser


class Categories(LoginRequiredMixin, View):
    def get(self, request):
        group_id = request.GET.get(
            "group_id",
            GroupUser.objects.filter(
                user_id=request.user.id,
                user_default_group=True
            ).first().group_id
        )
        category_types = CategoryType.objects.filter(
            group_id=group_id,
            hidden=False,
        ).order_by("sort_index")
        sections = [
            {
                "category_type": category_type,
                "categories": category_type.categories_set.filter(
                    deleted=False,
                    hidden=False,
                ).order_by("sort_index"),
            }
            for category_type in category_types
        ]
        context = {
            "title": "Categories",
            "category_types": category_types,
            "sections": sections,
        }
        return render(request, template_name="categories/index.html", context=context)


class Category(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "title": "Category",
        }
        return render(request, template_name="transaction/index.html", context=context)