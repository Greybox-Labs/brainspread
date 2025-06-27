from common.commands.abstract_base_command import AbstractBaseCommand
from knowledge.forms.delete_block_form import DeleteBlockForm


class DeleteBlockCommand(AbstractBaseCommand):
    """Command to delete a block"""

    def __init__(self, form: DeleteBlockForm) -> None:
        self.form = form

    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form

        block = self.form.cleaned_data["block"]
        block.delete()
        return True
