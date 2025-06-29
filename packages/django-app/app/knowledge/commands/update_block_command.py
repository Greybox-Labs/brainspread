from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.update_block_form import UpdateBlockForm
from ..models import Block


class UpdateBlockCommand(AbstractBaseCommand):
    """Command to update an existing block"""

    def __init__(self, form: UpdateBlockForm) -> None:
        self.form = form

    def execute(self) -> Block:
        """Execute the command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data["user"]
        block = self.form.cleaned_data["block"]
        parent = None
        if "parent" in self.form.cleaned_data:
            parent = self.form.cleaned_data["parent"]

        # Update fields
        content_updated = False

        if parent:
            # Check for circular references
            if self._would_create_circular_reference(block, parent):
                raise ValidationError(
                    "Cannot create circular reference: block cannot be its own ancestor"
                )

            block.parent = parent
        else:
            # If no parent is provided, ensure parent is set to None
            block.parent = None

        # Update other fields
        for field in [
            "content",
            "content_type",
            "block_type",
            "order",
            "media_url",
            "media_metadata",
            "properties",
        ]:
            if (
                field in self.form.cleaned_data
                and self.form.cleaned_data[field] is not None
            ):
                setattr(block, field, self.form.cleaned_data[field])
                if field == "content":
                    content_updated = True

        # Auto-detect block type from content if content was updated
        if content_updated:
            auto_detected_type = self._detect_block_type_from_content(
                block.content, block.block_type
            )
            if auto_detected_type != block.block_type:
                block.block_type = auto_detected_type

        block.save()

        # Extract and set tags if content was updated (business logic)
        if content_updated and block.content:
            block.set_tags_from_content(block.content, user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()

        return block

    def _detect_block_type_from_content(
        self, content: str, current_block_type: str
    ) -> str:
        """Auto-detect block type from content patterns"""
        # Only auto-detect for bullet, todo, and done types
        # Don't override other explicit types like heading, code, etc.
        if current_block_type not in ["bullet", "todo", "done"]:
            return current_block_type

        # Only auto-detect if we have content
        if not content:
            return current_block_type

        content_stripped = content.strip()
        content_lower = content_stripped.lower()

        # Check for TODO patterns
        if content_lower.startswith("todo"):
            return "todo"
        elif content_lower.startswith("[ ]"):
            return "todo"
        elif content_lower.startswith("[x]"):
            return "done"
        elif content_stripped.startswith("☐"):
            return "todo"
        elif content_stripped.startswith("☑"):
            return "done"
        elif content_lower.startswith("done"):
            return "done"

        # If none of the patterns match, return bullet for todo/done types
        if current_block_type in ["todo", "done"]:
            return "bullet"
        return current_block_type

    def _would_create_circular_reference(self, block, proposed_parent):
        """Check if setting proposed_parent as parent would create a circular reference"""
        # Walk up the proposed parent's ancestry to see if we find the block itself
        current = proposed_parent
        while current:
            if current.uuid == block.uuid:
                return True
            current = current.parent
        return False
