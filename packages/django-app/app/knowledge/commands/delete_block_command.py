from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.delete_block_form import DeleteBlockForm
from ..models import Block


class DeleteBlockCommand(AbstractBaseCommand):
    """Command to delete a block"""

    def __init__(self, form: DeleteBlockForm) -> None:
        self.form = form

    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data["user"]
        block_id = self.form.cleaned_data["block_id"]

        try:
            block = Block.objects.get(uuid=block_id, user=user)
            block.delete()
            return True
        except Block.DoesNotExist:
            raise ValidationError("Block not found")
