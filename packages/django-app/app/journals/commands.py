from datetime import date
from typing import Any, Dict, Optional
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand
from .models import JournalEntry, Page


class CreateOrUpdateJournalEntryCommand(AbstractBaseCommand):
    """Command to create or update a journal entry"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> JournalEntry:
        """Execute the command"""
        super().execute()  # This validates the form
        
        entry, created = JournalEntry.objects.update_or_create(
            user=self.user,
            date=self.form.cleaned_data['entry_date'],
            defaults={'content': self.form.cleaned_data.get('content', '')}
        )
        
        if entry.content:
            entry.set_tags_from_content(entry.content, self.user)
        
        return entry


class GetJournalEntryCommand(AbstractBaseCommand):
    """Command to get a journal entry"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Optional[JournalEntry]:
        """Execute the command"""
        super().execute()  # This validates the form
        
        try:
            entry = JournalEntry.objects.get(
                user=self.user,
                date=self.form.cleaned_data['entry_date']
            )
            return entry
        except JournalEntry.DoesNotExist:
            return None


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
            title=self.form.cleaned_data['title'],
            slug=self.form.cleaned_data.get('slug') or slugify(self.form.cleaned_data['title']),
            content=self.form.cleaned_data.get('content', ''),
            is_published=self.form.cleaned_data.get('is_published', True)
        )
        
        if page.content:
            page.set_tags_from_content(page.content, self.user)
        
        return page


class UpdatePageCommand(AbstractBaseCommand):
    """Command to update an existing page"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form
        
        page = Page.objects.get(uuid=self.form.cleaned_data['page_id'], user=self.user)
        
        # Update fields if provided
        if 'title' in self.form.cleaned_data and self.form.cleaned_data['title'] is not None:
            page.title = self.form.cleaned_data['title']
        
        if 'content' in self.form.cleaned_data and self.form.cleaned_data['content'] is not None:
            page.content = self.form.cleaned_data['content']
        
        if 'slug' in self.form.cleaned_data and self.form.cleaned_data['slug'] is not None:
            page.slug = self.form.cleaned_data['slug']
        
        if 'is_published' in self.form.cleaned_data and self.form.cleaned_data['is_published'] is not None:
            page.is_published = self.form.cleaned_data['is_published']
        
        page.save()
        
        if page.content:
            page.set_tags_from_content(page.content, self.user)
        
        return page


class DeletePageCommand(AbstractBaseCommand):
    """Command to delete a page"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form
        
        page = Page.objects.get(uuid=self.form.cleaned_data['page_id'], user=self.user)
        page.delete()
        return True


class GetUserJournalEntriesCommand(AbstractBaseCommand):
    """Command to get user's journal entries"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command"""
        super().execute()  # This validates the form
        
        limit = self.form.cleaned_data.get('limit', 10)
        offset = self.form.cleaned_data.get('offset', 0)
        
        entries = JournalEntry.objects.filter(user=self.user)[offset:offset + limit]
        total_count = JournalEntry.objects.filter(user=self.user).count()
        
        return {
            'entries': list(entries),
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        }


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