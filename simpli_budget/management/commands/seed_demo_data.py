from django.core.management.base import BaseCommand

from helpers.demo_data import seed_demo_account


class Command(BaseCommand):
    help = (
        "Creates (or reuses) the demo group with fake accounts, categories, and a few "
        "months of realistic transaction history anchored to each category's budget. "
        "Safe to re-run - existing demo accounts/categories/category-months are reused, "
        "not duplicated. Prints the demo group id to set as DEMO_GROUP_ID."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--months-back",
            type=int,
            default=3,
            help="How many months of history to generate before the current month (default: 3).",
        )

    def handle(self, *args, **options):
        group = seed_demo_account(months_back=options["months_back"])
        self.stdout.write(self.style.SUCCESS(
            f"Demo group ready: '{group.name}' (group_id={group.group_id}). "
            f"Set DEMO_GROUP_ID={group.group_id} to enable the in-app 'generate more activity' endpoint."
        ))
