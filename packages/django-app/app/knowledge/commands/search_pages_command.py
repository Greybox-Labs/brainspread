from django.db.models import Q

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.search_pages_form import SearchPagesForm
from ..models import Page, PagesData


class SearchPagesCommand(AbstractBaseCommand):
    """Command to search user's pages by title and slug"""

    def __init__(self, form: SearchPagesForm) -> None:
        self.form = form

    def execute(self) -> PagesData:
        """Execute the search command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data.get("user")
        query = self.form.cleaned_data.get("query")
        limit = self.form.cleaned_data.get("limit", 10)

        # Search in title and slug only (case-insensitive)
        search_q = Q(title__icontains=query) | Q(slug__icontains=query)

        queryset = (
            Page.objects.filter(user=user, is_published=True)
            .filter(search_q)
            .order_by(
                "-modified_at", "title"
            )  # Order by most recently updated first, then by title
            .select_related("user")  # Optimize query
        )

        pages = list(queryset[:limit])

        return PagesData(
            pages=[page.to_dict() for page in pages],
            total_count=queryset.count(),
            has_more=False,
        )
