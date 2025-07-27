from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import (
    RuleSet,
    GroupUser,
    Rule,
    Categories,
    RuleMatchType
)


class Rules(LoginRequiredMixin, View):
    def get(self, request):
        user_default_group = GroupUser.objects.filter(
            user_id=request.user.id,
            user_default_group=True
        ).first()
        group_id = request.GET.get("group_id", user_default_group.group_id)
        categories = Categories.objects.filter(
            category_type__group_id=group_id,
            category_type__hidden=False,
            hidden=False,
            deleted=False
        ).order_by(
            "category_type__sort_index",
            "sort_index"
        )
        context = {
            "title": "Rules",
            "rule_sets": RuleSet.objects.filter(group_id=group_id).all(),
            "categories": categories,
        }
        return render(request, template_name="rules/index.html", context=context)


class RuleView(LoginRequiredMixin, View):
    def get(self, request, rule_set_id: int):
        user_default_group = GroupUser.objects.filter(
            user_id=request.user.id,
            user_default_group=True
        ).first()
        group_id = request.GET.get("group_id", user_default_group.group_id)
        rule_set = RuleSet.objects.filter(
            set_id=rule_set_id,
            group_id=group_id
        ).first()
        if rule_set is None:
            return render(request, template_name='404.html', context={})
        rules = Rule.objects.filter(
            set_id=rule_set_id,
        ).all()
        match_types = RuleMatchType.objects.all()
        categories = Categories.objects.filter(
            category_type__group_id=group_id,
            category_type__hidden=False,
            hidden=False,
            deleted=False
        ).order_by(
            "category_type__sort_index",
            "sort_index"
        )
        context = {
            "title": "Rule",
            "rule_set": rule_set,
            "rules": rules,
            "match_types": match_types,
            "categories": categories,
        }
        return render(request, template_name="rules/rule.html", context=context)