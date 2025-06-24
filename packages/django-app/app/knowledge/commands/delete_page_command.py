from common.commands.abstract_base_command import AbstractBaseCommand

from ..models import Page


class DeletePageCommand(AbstractBaseCommand):
    """Command to delete a page"""

    def __init__(self, form, user):
        self.form = form
        self.user = user

    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form

        page = Page.objects.get(uuid=self.form.cleaned_data["page_id"], user=self.user)
        page.delete()
        return True
