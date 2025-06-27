from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.delete_page_form import DeletePageForm


class DeletePageCommand(AbstractBaseCommand):
    """Command to delete a page"""

    def __init__(self, form: DeletePageForm) -> None:
        self.form = form

    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form

        page = self.form.cleaned_data["page"]
        page.delete()
        return True
