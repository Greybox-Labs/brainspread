from django.utils.text import slugify

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.create_page_form import CreatePageForm
from ..models import Page


class CreatePageCommand(AbstractBaseCommand):
    """Command to create a new page"""

    def __init__(self, form: CreatePageForm) -> None:
        self.form = form

    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data["user"]
        page = Page.objects.create(
            user=user,
            title=self.form.cleaned_data["title"],
            slug=self.form.cleaned_data.get("slug")
            or slugify(self.form.cleaned_data["title"]),
            content=self.form.cleaned_data.get("content", ""),
            is_published=self.form.cleaned_data.get("is_published", True),
        )

        return page
