from simpli_budget.models import UserAttributes


class SetUserAttributeDefaults:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not UserAttributes.objects.filter(
            user=request.user
        ).exists():
            UserAttributes.objects.create(
                user=request.user,
                show_hidden=False
            )
        return self.get_response(request)