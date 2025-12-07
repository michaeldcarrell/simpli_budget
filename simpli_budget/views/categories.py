from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import GroupUser, CategoryType


class CategoriesView(LoginRequiredMixin, View):
    def get(self, request):
        user_default_group = GroupUser.objects.filter(
            user_id=request.user.id,
            user_default_group=True
        ).first()
        group_id = request.GET.get("group_id", user_default_group.group_id)
        category_types = CategoryType.objects.filter(
            group_id=group_id,
            category_type_id__gt=0
        ).order_by("sort_index")
        context = {
            "title": "Categories",
            "category_types": category_types,
        }
        return render(request, template_name="categories/index.html", context=context)


class Category(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "title": "Category",
        }
        return render(request, template_name="transaction/index.html", context=context)