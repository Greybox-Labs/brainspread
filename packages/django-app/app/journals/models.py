from django.db import models
from django.conf import settings
from django.utils import timezone

from common.models.uuid_mixin import UUIDModelMixin
from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from tagging.models import TaggableMixin


class JournalEntry(UUIDModelMixin, CRUDTimestampsMixin, TaggableMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal_entries'
    )
    date = models.DateField(default=timezone.now)
    content = models.TextField(blank=True, help_text='Markdown content')
    
    class Meta:
        db_table = 'journal_entries'
        unique_together = [('user', 'date')]
        ordering = ('-date',)
        verbose_name = 'journal entry'
        verbose_name_plural = 'journal entries'
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"


class Page(UUIDModelMixin, CRUDTimestampsMixin, TaggableMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    content = models.TextField(blank=True, help_text='Markdown content')
    is_published = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'journal_pages'
        unique_together = [('user', 'slug')]
        ordering = ('title',)
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
