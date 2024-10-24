from django.core.management.base import BaseCommand

from ....cms.utils.contact_utils import find_all_contacts


class Command(BaseCommand):

    help = (
        "Goes through all models registered to contain contacts, records any new contacts found"
        "and removes all outdated contacts"
    )

    def handle(self, *args, **options):
        self.stdout.write("Updating all contacts...")
        return "\n".join(
            [
                f"{model.capitalize()}: {', '.join([f'{count} {label}' for label, count in data.items()])}"
                for model, data in find_all_contacts().items()
            ]
        )
