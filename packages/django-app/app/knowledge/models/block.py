import re
from typing import TypedDict

from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin
from tagging.models import TaggableMixin


class Block(UUIDModelMixin, CRUDTimestampsMixin, TaggableMixin):
    """
    Everything is a block. Blocks can contain text, media, or any other content.
    They can be nested hierarchically and have various types and properties.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    page = models.ForeignKey("Page", on_delete=models.CASCADE, related_name="blocks")

    # Content and media
    content = models.TextField(blank=True, help_text="Text content of the block")
    content_type = models.CharField(
        max_length=20,
        choices=[
            ("text", "Text"),
            ("markdown", "Markdown"),
            ("image", "Image"),
            ("video", "Video"),
            ("audio", "Audio"),
            ("file", "File"),
            ("embed", "Embed"),
            ("code", "Code"),
            ("quote", "Quote"),
        ],
        default="text",
    )

    # For media blocks
    media_url = models.URLField(blank=True, help_text="URL for media content")
    media_file = models.FileField(upload_to="blocks/", blank=True, null=True)
    media_metadata = models.JSONField(
        default=dict, blank=True, help_text="Metadata for media files"
    )

    # Block properties (key:: value pairs)
    properties = models.JSONField(
        default=dict, blank=True, help_text="Block properties as key-value pairs"
    )

    # Block behavior
    block_type = models.CharField(
        max_length=20,
        choices=[
            ("bullet", "Bullet Point"),
            ("todo", "Todo"),
            ("done", "Done"),
            ("heading", "Heading"),
            ("quote", "Quote"),
            ("code", "Code Block"),
            ("divider", "Divider"),
        ],
        default="bullet",
    )

    order = models.PositiveIntegerField(default=0, help_text="Order within parent/page")
    collapsed = models.BooleanField(
        default=False, help_text="Whether block is collapsed"
    )

    class Meta:
        db_table = "blocks"
        ordering = ("page", "order")
        indexes = [
            models.Index(fields=["user", "page"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["page", "order"]),
            models.Index(fields=["content_type"]),
            models.Index(fields=["block_type"]),
        ]

    def __str__(self):
        if self.content:
            preview = (
                self.content[:50] + "..." if len(self.content) > 50 else self.content
            )
            return f"Block {self.uuid}: {preview}"
        elif self.media_url or self.media_file:
            return f"Block {self.uuid}: [{self.content_type}]"
        else:
            return f"Block {self.uuid}: [empty]"

    def get_children(self):
        """Get direct children blocks"""
        return self.children.all().order_by("order")

    def get_descendants(self):
        """Get all descendant blocks recursively"""
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_depth(self):
        """Get the depth/level of this block in the hierarchy"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def extract_page_links(self):
        """Extract [[page]] links from content"""
        if not self.content:
            return []
        pattern = r"\[\[([^\]]+)\]\]"
        return re.findall(pattern, self.content)

    def extract_block_references(self):
        """Extract ((block-id)) references from content"""
        if not self.content:
            return []
        pattern = r"\(\(([^\)]+)\)\)"
        return re.findall(pattern, self.content)

    def extract_properties_from_content(self):
        """Extract key:: value properties from content and sync with properties field"""
        if not self.content:
            return {}

        pattern = r"^([a-zA-Z0-9_-]+)::\s*(.+)$"
        extracted_properties = {}
        for line in self.content.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                extracted_properties[match.group(1)] = match.group(2)

        # Sync with properties field
        if extracted_properties != self.properties:
            self.properties = extracted_properties
            self.save(update_fields=["properties"])

        return extracted_properties

    def get_property(self, key, default=None):
        """Get a specific property value"""
        return self.properties.get(key, default)

    def set_property(self, key, value):
        """Set a property value"""
        if not self.properties:
            self.properties = {}
        self.properties[key] = value
        self.save(update_fields=["properties"])

    def remove_property(self, key):
        """Remove a property"""
        if self.properties and key in self.properties:
            del self.properties[key]
            self.save(update_fields=["properties"])

    def get_media_info(self):
        """Get media information for this block"""
        if self.content_type in ["image", "video", "audio", "file"]:
            return {
                "type": self.content_type,
                "url": self.media_url,
                "file": self.media_file.url if self.media_file else None,
                "metadata": self.media_metadata,
            }
        return None


# API response type for Block data
class BlockData(TypedDict):
    uuid: str
    content: str
    content_type: str
    block_type: str
    order: int
    collapsed: bool
    parent_block_uuid: str | None
    page_uuid: str
    user_uuid: str
    created_at: str
    updated_at: str
    media_url: str
    properties: dict
