import re
from typing import List, Optional, TypedDict

from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin
from knowledge.models import BlockData


class Page(UUIDModelMixin, CRUDTimestampsMixin):
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
            ("tag", "Tag Page"),
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

    def get_backlinks(self):
        """Get all blocks that link to this page"""
        from .block import Block

        pattern = r"\[\[" + re.escape(self.title) + r"\]\]"
        return Block.objects.filter(content__iregex=pattern, user=self.user).exclude(
            page=self
        )

    def get_tag_blocks(self):
        """If this is a tag page, get all blocks that belong to this tag"""
        if self.page_type == "tag":
            return self.tagged_blocks.all()
        return []

    def get_tag_name(self):
        """If this is a tag page, get the tag name without # prefix"""
        if self.page_type == "tag" and self.title.startswith("#"):
            return self.title[1:]
        return None

    def to_dict(self) -> "PageData":
        """Convert page to dictionary with proper typing"""
        return {
            "uuid": str(self.uuid),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "is_published": self.is_published,
            "page_type": self.page_type,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "user_uuid": str(self.user.uuid),
            "recent_blocks": None,  # fill these in later
        }


# API response type for Page data
class PageData(TypedDict):
    uuid: str
    title: str
    slug: str
    content: str
    is_published: bool
    page_type: str
    date: Optional[str]
    created_at: str
    modified_at: str
    user_uuid: str
    recent_blocks: Optional[List[BlockData]]
