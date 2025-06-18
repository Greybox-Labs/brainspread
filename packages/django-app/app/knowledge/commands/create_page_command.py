from django.utils.text import slugify

from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Page


class CreatePageCommand(AbstractBaseCommand):
    """Command to create a new page"""

    def __init__(self, form, user):
        self.form = form
        self.user = user

    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form

        page = Page.objects.create(
            user=self.user,
            title=self.form.cleaned_data["title"],
            slug=self.form.cleaned_data.get("slug")
            or slugify(self.form.cleaned_data["title"]),
            content=self.form.cleaned_data.get("content", ""),
            is_published=self.form.cleaned_data.get("is_published", True),
        )

        if page.content:
            page.set_tags_from_content(page.content, self.user)

        return page
