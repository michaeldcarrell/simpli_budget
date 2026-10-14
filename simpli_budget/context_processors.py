from django.conf import settings
from django.http import Http404

from helpers.chat import chat_allowed
from simpli_budget.models import UserAttributes, get_user_group


THEMES = ('dark', 'light')
DEFAULT_THEME = 'dark'


def user_preferences(request):
    if not request.user.is_authenticated:
        return {'theme': DEFAULT_THEME}
    attributes = UserAttributes.objects.filter(user=request.user).first()
    return {
        'onboarding_completed': attributes.onboarding_completed if attributes else False,
        'theme': attributes.theme if attributes and attributes.theme in THEMES else DEFAULT_THEME,
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


NAV_SECTIONS = (
    ('/transaction', 'transactions'),
    ('/categories', 'categories'),
    ('/tags', 'tags'),
    ('/rules', 'rules'),
    ('/accounts', 'accounts'),
    ('/notifications', 'more'),
    ('/budget', 'budget'),
)


def navigation(request):
    """Which main nav item the current page belongs to, for highlighting it."""
    if request.path == '/':
        return {'nav_section': 'budget'}
    for prefix, section in NAV_SECTIONS:
        if request.path.startswith(prefix):
            return {'nav_section': section}
    return {'nav_section': None}
