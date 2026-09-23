from django.conf import settings
from django.http import Http404

from helpers.chat import chat_allowed
from simpli_budget.models import UserAttributes, get_user_group


def onboarding(request):
    if not request.user.is_authenticated:
        return {}
    attributes = UserAttributes.objects.filter(user=request.user).first()
    return {
        'onboarding_completed': attributes.onboarding_completed if attributes else False,
    }


def chat(request):
    if not request.user.is_authenticated or not settings.CHAT_GROUP_IDS:
        return {}
    try:
        group = get_user_group(request.user, request)
    except Http404:
        return {}
    return {
        'chat_enabled': chat_allowed(request.user, group),
    }
