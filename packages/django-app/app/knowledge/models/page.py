import re
from typing import TypedDict

from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin
from tagging.models import TaggableMixin


class Page(UUIDModelMixin, CRUDTimestampsMixin, TaggableMixin):
    """
    A page is simply a container/namespace for blocks.
    Pages can be daily notes, regular pages, or any other type of content collection.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pages"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    content = models.TextField(blank=True, help_text="Text content of the page")
    is_published = models.BooleanField(
        default=True, help_text="Whether the page is published"
    )
    page_type = models.CharField(
        max_length=20,
        choices=[
            ("page", "Regular Page"),
            ("daily", "Daily Note"),
            ("template", "Template"),
        ],
        default="page",
    )
    date = models.DateField(null=True, blank=True, help_text="Date for daily notes")

    class Meta:
        db_table = "pages"
        unique_together = [("user", "slug")]
        ordering = ("title",)
        indexes = [
            models.Index(fields=["user", "page_type", "date"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def get_root_blocks(self):
        """Get top-level blocks (no parent)"""
        return self.blocks.filter(parent=None).order_by("order")

    def get_backlinks(self):
        """Get all blocks that link to this page"""
        from .block import Block

        pattern = r"\[\[" + re.escape(self.title) + r"\]\]"
        return Block.objects.filter(content__iregex=pattern, user=self.user).exclude(
            page=self
        )

    @classmethod
    def get_or_create_daily_note(cls, user, date):
        """Get or create a daily note page for a specific date"""
        date_str = date.strftime("%Y-%m-%d")
        page, created = cls.objects.get_or_create(
            user=user,
            slug=date_str,
            defaults={"title": date_str, "page_type": "daily", "date": date},
        )
        return page, created


# API response type for Page data
class PageData(TypedDict):
    uuid: str
    title: str
    slug: str
    content: str
    is_published: bool
    page_type: str
    date: str | None
    created_at: str
    updated_at: str
    user_uuid: str
