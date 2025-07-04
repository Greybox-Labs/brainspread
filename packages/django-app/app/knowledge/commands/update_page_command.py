from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.update_page_form import UpdatePageForm
from ..models import Page


class UpdatePageCommand(AbstractBaseCommand):
    """Command to update an existing page"""

    def __init__(self, form: UpdatePageForm) -> None:
        self.form = form

    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form

        page = self.form.cleaned_data["page"]

        # Update fields if provided
        if (
            "title" in self.form.cleaned_data
            and self.form.cleaned_data["title"] is not None
        ):
            page.title = self.form.cleaned_data["title"]

        if (
            "content" in self.form.cleaned_data
            and self.form.cleaned_data["content"] is not None
        ):
            page.content = self.form.cleaned_data["content"]

        if (
            "slug" in self.form.cleaned_data
            and self.form.cleaned_data["slug"] is not None
        ):
            page.slug = self.form.cleaned_data["slug"]

        if (
            "is_published" in self.form.cleaned_data
            and self.form.cleaned_data["is_published"] is not None
        ):
            page.is_published = self.form.cleaned_data["is_published"]

        page.save()

        return page
