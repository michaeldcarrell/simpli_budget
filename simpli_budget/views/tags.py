from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from simpli_budget.models import TagType, GroupUser


class Tags(LoginRequiredMixin, View):
    def get(self, request):
        group_id = request.GET.get(
            "group_id",
            GroupUser.objects.filter(
                user_id=request.user.id,
                user_default_group=True
            ).first().group_id
        )
        tag_types = TagType.objects.filter(group_id=group_id).order_by("name")
        sections = [
            {
                "tag_type": tag_type,
                "tags": tag_type.tag_set.filter(deleted=False).order_by("name"),
            }
            for tag_type in tag_types
        ]
        context = {
            "title": "Tags",
            "sections": sections,
            "tag_types": tag_types,
        }
        return render(request, template_name="tags/index.html", context=context)
