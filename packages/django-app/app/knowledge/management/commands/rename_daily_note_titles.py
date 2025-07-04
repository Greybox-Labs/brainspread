from django.core.management.base import BaseCommand
from django.db import transaction

from knowledge.models import Page


class Command(BaseCommand):
    help = "Rename daily note titles to match their current slug"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making any changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get all daily note pages where title doesn't match slug
        daily_notes = Page.objects.filter(page_type="daily").exclude(
            title__exact="",  # Skip empty titles
        )

        pages_to_update = []
        for page in daily_notes:
            if page.title != page.slug:
                pages_to_update.append(page)

        if not pages_to_update:
            self.stdout.write(
                self.style.SUCCESS("No daily note pages need title updates.")
            )
            return

        self.stdout.write(
            f"Found {len(pages_to_update)} daily note pages with titles that don't match their slug:"
        )

        for page in pages_to_update:
            self.stdout.write(f'  Page ID {page.id}: "{page.title}" -> "{page.slug}"')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: No changes were made. Run without --dry-run to apply changes."
                )
            )
            return

        # Apply the changes
        with transaction.atomic():
            updated_count = 0
            for page in pages_to_update:
                old_title = page.title
                page.title = page.slug
                page.save(update_fields=["title"])
                updated_count += 1
                self.stdout.write(
                    f'Updated page {page.id}: "{old_title}" -> "{page.title}"'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated_count} daily note titles."
            )
        )
