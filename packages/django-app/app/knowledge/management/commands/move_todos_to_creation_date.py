from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import User
from knowledge.models import Block
from knowledge.repositories import BlockRepository, PageRepository


class Command(BaseCommand):
    help = "Move TODO blocks back to their original creation date (useful for rolling back bulk moves)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            required=True,
            help="Email of the user to move TODOs for",
        )
        parser.add_argument(
            "--block-type",
            type=str,
            default="todo",
            choices=["todo", "done", "all"],
            help="Type of blocks to move (default: todo)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be moved without actually moving",
        )
        parser.add_argument(
            "--from-date",
            type=str,
            help="Only move blocks created from this date onwards (YYYY-MM-DD format)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        user_email = options["user"]
        block_type = options["block_type"]
        dry_run = options["dry_run"]
        from_date_str = options.get("from_date")

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f"User with email '{user_email}' does not exist")

        # Parse from_date if provided
        from_date = None
        if from_date_str:
            try:
                from_date = date.fromisoformat(from_date_str)
            except ValueError:
                raise CommandError(
                    f"Invalid date format: {from_date_str}. Use YYYY-MM-DD"
                )

        # Build query for blocks to move
        queryset = Block.objects.filter(user=user)

        if block_type == "all":
            queryset = queryset.filter(block_type__in=["todo", "done"])
        else:
            queryset = queryset.filter(block_type=block_type)

        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)

        # Get blocks that are NOT on their creation date's daily page
        blocks_to_move = []
        for block in queryset.select_related("page"):
            creation_date = block.created_at.date()

            # Skip if block is already on its creation date's page
            if (
                block.page.page_type == "daily"
                and hasattr(block.page, "date")
                and block.page.date == creation_date
            ):
                continue

            blocks_to_move.append((block, creation_date))

        if not blocks_to_move:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ No blocks need to be moved for user {user.email}"
                )
            )
            return

        self.stdout.write(f"Found {len(blocks_to_move)} blocks to move:")

        # Group by target date for summary
        moves_by_date = {}
        for block, target_date in blocks_to_move:
            if target_date not in moves_by_date:
                moves_by_date[target_date] = []
            moves_by_date[target_date].append(block)

        # Show summary
        for target_date, blocks in sorted(moves_by_date.items()):
            self.stdout.write(f"  → {target_date}: {len(blocks)} blocks")
            if options.get("verbosity", 1) >= 2:
                for block in blocks[:3]:  # Show first 3 blocks
                    content_preview = (
                        (block.content[:50] + "...")
                        if len(block.content) > 50
                        else block.content
                    )
                    self.stdout.write(f"    - {block.block_type}: {content_preview}")
                if len(blocks) > 3:
                    self.stdout.write(f"    ... and {len(blocks) - 3} more")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: No blocks were actually moved. Use --dry-run=false to execute."
                )
            )
            return

        # Confirm before proceeding (unless in non-interactive mode)
        if not options.get("verbosity", 1) == 0:  # Skip confirmation in quiet mode
            confirm = input(
                f"\nProceed with moving {len(blocks_to_move)} blocks? [y/N]: "
            )
            if confirm.lower() != "y":
                self.stdout.write("Cancelled.")
                return

        # Perform the moves
        moved_count = 0
        created_pages = 0

        try:
            with transaction.atomic():
                for target_date, blocks in moves_by_date.items():
                    # Get or create the daily page for the target date
                    target_page, created = PageRepository.get_or_create_daily_note(
                        user, target_date
                    )
                    if created:
                        created_pages += 1
                        self.stdout.write(f"  Created daily page for {target_date}")

                    # Move blocks to the target page
                    success = BlockRepository.move_blocks_to_page(blocks, target_page)
                    if not success:
                        raise CommandError(f"Failed to move blocks to {target_date}")

                    moved_count += len(blocks)
                    self.stdout.write(f"  Moved {len(blocks)} blocks to {target_date}")

        except Exception as e:
            raise CommandError(f"Error during move operation: {str(e)}")

        # Output final result
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Successfully moved {moved_count} blocks back to their creation dates for user {user.email}"
            )
        )

        if created_pages > 0:
            self.stdout.write(f"  Created {created_pages} new daily pages")

        self.stdout.write(
            "\n"
            + self.style.WARNING(
                "Tip: You can now run 'move_undone_todos' again to move undone TODOs with the fixed logic!"
            )
        )
