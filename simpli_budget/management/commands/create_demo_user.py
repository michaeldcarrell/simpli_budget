from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from simpli_budget.models import GroupUser


class Command(BaseCommand):
    help = (
        "Creates (or reuses) the shared read-only user behind the public /demo link: "
        "settings.DEMO_USERNAME, a member of only settings.DEMO_GROUP_ID, with no password or "
        "Google login. Safe to re-run."
    )

    def handle(self, *args, **options):
        if settings.DEMO_GROUP_ID is None:
            raise CommandError("DEMO_GROUP_ID is not set - run seed_demo_data first and set it.")

        user, created = get_user_model().objects.get_or_create(
            username=settings.DEMO_USERNAME,
            defaults={"first_name": "Demo", "email": ""},
        )
        if created:
            user.set_unusable_password()
            user.save()
        elif user.is_staff or user.is_superuser or user.socialaccount_set.exists():
            raise CommandError(
                f"User '{user.username}' already exists and is a staff/superuser or has a Google login, "
                "so it can't double as the public demo account. Set DEMO_USERNAME to a different name."
            )

        other_groups = GroupUser.objects.filter(user=user).exclude(group_id=settings.DEMO_GROUP_ID)
        if other_groups.exists():
            raise CommandError(
                f"User '{user.username}' belongs to groups other than the demo group "
                f"({list(other_groups.values_list('group_id', flat=True))}); refusing to expose them publicly."
            )
        GroupUser.objects.get_or_create(
            user=user,
            group_id=settings.DEMO_GROUP_ID,
            defaults={"user_default_group": True},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Demo user '{user.username}' (id={user.id}) {'created' if created else 'already existed'} "
            f"in group {settings.DEMO_GROUP_ID}. Visitors can now use /demo."
        ))
