import re
from typing import Optional, TypedDict

from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin


class Block(UUIDModelMixin, CRUDTimestampsMixin):
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
    pages = models.ManyToManyField(
        "Page",
        related_name="tagged_blocks",
        blank=True,
        help_text="Pages this block belongs to (used for tagging)",
    )

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

    def extract_properties_from_content(self):
        """Extract key:: value properties from content and sync with properties field"""
        if not self.content:
            return {}

        extracted_properties = {}

        # First: Handle line-start properties (can have multi-word values)
        line_pattern = r"^([a-zA-Z0-9_-]+)::\s*(.+)$"
        for line in self.content.split("\n"):
            match = re.match(line_pattern, line.strip())
            if match:
                key, value = match.groups()
                # For line-start properties, strip out any inline properties from the value
                # Split value and take only until the first inline property
                value_words = value.split()
                clean_value_words = []
                for word in value_words:
                    if "::" in word and re.match(r"^[a-zA-Z0-9_-]+::", word):
                        break  # Stop at first inline property
                    clean_value_words.append(word)
                if clean_value_words:
                    extracted_properties[key] = " ".join(clean_value_words)

        # Second: Handle inline properties (single word values)
        inline_pattern = r"([a-zA-Z0-9_-]+)::\s*([^\s]+)"
        for line in self.content.split("\n"):
            # Find all inline properties in each line
            matches = re.findall(inline_pattern, line)
            for key, value in matches:
                # Only add if not already found as line-start property
                if key not in extracted_properties:
                    extracted_properties[key] = value.strip()

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

    def get_tags(self):
        """Get all pages this block is tagged with (excludes the page it belongs to and daily notes)"""
        return self.pages.exclude(uuid=self.page.uuid).exclude(page_type="daily")

    def get_tag_names(self):
        """Get tag names (uses slug format without # prefix)"""
        return [page.slug for page in self.get_tags()]

    def to_dict(self, include_page_context: bool = False) -> "BlockData":
        """Convert block to dictionary with proper typing"""
        data: BlockData = {
            "uuid": str(self.uuid),
            "content": self.content,
            "content_type": self.content_type,
            "block_type": self.block_type,
            "order": self.order,
            "collapsed": self.collapsed,
            "parent_block_uuid": str(self.parent.uuid) if self.parent else None,
            "page_uuid": str(self.page.uuid),
            "user_uuid": str(self.user.uuid),
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "media_url": self.media_url,
            "properties": self.properties or {},
            "tags": [{"name": tag.slug, "color": "#007bff"} for tag in self.get_tags()],
            "children": None,
            # Page context fields (optional)
            "page_title": None,
            "page_type": None,
            "page_slug": None,
            "page_date": None,
        }

        # Add page context if requested
        if include_page_context and self.page:
            data["page_title"] = self.page.title
            data["page_type"] = self.page.page_type
            data["page_slug"] = self.page.slug
            data["page_date"] = self.page.date.isoformat() if self.page.date else None

        return data

    def to_dict_with_children(self, include_page_context: bool = False) -> "BlockData":
        """Convert block to dict with nested children"""
        block_data = self.to_dict(include_page_context=include_page_context)
        children = []
        for child in self.get_children():
            children.append(
                child.to_dict_with_children(include_page_context=include_page_context)
            )
        block_data["children"] = children
        return block_data


# API response type for Block data
class BlockData(TypedDict):
    uuid: str
    content: str
    content_type: str
    block_type: str
    order: int
    collapsed: bool
    parent_block_uuid: Optional[str]
    page_uuid: str
    user_uuid: str
    created_at: str
    modified_at: str
    media_url: str
    properties: dict
    tags: Optional[list]
    children: Optional[list["BlockData"]]
    # Page context fields (when included in API responses)
    page_title: Optional[str]
    page_type: Optional[str]
    page_slug: Optional[str]
    page_date: Optional[str]
