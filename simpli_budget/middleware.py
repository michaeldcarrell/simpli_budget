from django.http import HttpResponseForbidden, JsonResponse

from simpli_budget.models import UserAttributes, is_demo_user


class SetUserAttributeDefaults:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not UserAttributes.objects.filter(
                user=request.user
            ).exists():
                UserAttributes.objects.create(
                    user=request.user,
                    show_hidden=False
                )
        return self.get_response(request)


DEMO_READ_ONLY_MESSAGE = "This is a read-only demo, so changes aren't saved. Sign in with Google to use your own budget."


class DemoReadOnly:
    """
    Rejects every write from the demo user, so new endpoints are read-only for it by default.
    The exceptions are requests that only look like writes: the transaction search is a POST, and the
    theme/onboarding endpoints keep the demo user's choices in its session rather than the database.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    ALLOWED_WRITES = (
        ('POST', '/api/transactions'),
        ('PUT', '/api/settings'),
        ('POST', '/api/onboarding/complete'),
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method not in self.SAFE_METHODS
            and (request.method, request.path) not in self.ALLOWED_WRITES
            and is_demo_user(request.user)
        ):
            if request.path.startswith('/api/'):
                return JsonResponse({'message': DEMO_READ_ONLY_MESSAGE}, status=403)
            return HttpResponseForbidden(DEMO_READ_ONLY_MESSAGE)
        return self.get_response(request)
