from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import CategoryMonth, Categories, CategoryType, UserAttributes, BudgetMonth, Month, GroupUser
from datetime import datetime as dt

class BudgetCategory(LoginRequiredMixin, View):
    def get(self, request, category_id: int):
        current_year_month = f"{dt.now().year}{dt.now().month:02}"
        month = request.GET.get("month", current_year_month)
        user_default_group = GroupUser.objects.filter(
            user_id=request.user.id,
            user_default_group=True
        ).first()
        group_id = request.GET.get("group_id", user_default_group.group_id)
        category = Categories.objects.get(category_id=category_id)
        if not category.user_has_access(request.user):
            return render(
                request,
                template_name="404.html",
                context={
                    "message": "Category not found"
                }
            )
        category_month = CategoryMonth(category=category, year_month=int(month))
        categories = [
            category for category in
            Categories.objects.filter(
                category_type__group_id=group_id,
                hidden=False
            )
        ]

        # TODO: This will cause issues with New users, currently that category type is attached to my group
        categories.append(
            Categories.objects.filter(
                category_id=-1
            ).first()
        )

        context = {
            "title": f"{category.category_name} - {category_month.month.name_short}",
            "category_month": category_month,
            'categories': categories,
        }

        return render(request, template_name="budget/category.html", context=context)


class MonthBudget(LoginRequiredMixin, View):
    def get(self, request):
        current_year_month = int(f"{dt.now().year}{dt.now().month:02}")
        year_month = request.GET.get("month", current_year_month)
        group_id = request.GET.get(
            "group_id",
            GroupUser.objects.filter(
                user_id=request.user.id,
                user_default_group=True
            ).first().group_id
        )

        category_types = CategoryType.objects.filter(group_id=group_id).order_by("sort_index")
        attributes = UserAttributes.objects.filter(user_id=request.user.id).first()
        context = {
            'budget_month': BudgetMonth(
                category_types=category_types,
                year_month=year_month,
                include_hidden=attributes.show_hidden
            ),
            'svg_button_size': 32,
        }
        return render(request, template_name="budget/month_overview.html", context=context)
