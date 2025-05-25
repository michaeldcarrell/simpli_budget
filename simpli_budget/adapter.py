from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return

        # Extract data from social provider (e.g., email, username)
        # and assign it to the user object

        if sociallogin.account.provider == 'google':
            user.email = sociallogin.account.extra_data.get('email')
            user.username = sociallogin.account.extra_data.get('email').split('@')[0].lower()

        # Check if user with this email already exists
        try:
            existing_user = User.objects.get(email=user.email)
            sociallogin.connect(request, existing_user)
            return
        except User.DoesNotExist:
            pass

        sociallogin.save(request)


class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False