from simpli_budget.models import UserAttributes


def onboarding(request):
    if not request.user.is_authenticated:
        return {}
    attributes = UserAttributes.objects.filter(user=request.user).first()
    return {
        'onboarding_completed': attributes.onboarding_completed if attributes else False,
    }
