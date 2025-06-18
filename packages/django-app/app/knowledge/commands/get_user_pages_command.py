from typing import Any, Dict

from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Page


class GetUserPagesCommand(AbstractBaseCommand):
    """Command to get user's pages"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command"""
        super().execute()  # This validates the form
        
        published_only = self.form.cleaned_data.get('published_only', True)
        limit = self.form.cleaned_data.get('limit', 10)
        offset = self.form.cleaned_data.get('offset', 0)
        
        queryset = Page.objects.filter(user=self.user)
        if published_only:
            queryset = queryset.filter(is_published=True)
        
        pages = queryset[offset:offset + limit]
        total_count = queryset.count()
        
        return {
            'pages': list(pages),
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        }