from django.contrib import admin
from .models import Page, Block, PageLink, BlockReference


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "slug",
        "page_type",
        "date",
        "created_at",
        "modified_at",
    )
    list_filter = ("page_type", "created_at", "modified_at")
    search_fields = ("title", "user__email", "slug")
    readonly_fields = ("uuid", "created_at", "modified_at")
    raw_id_fields = ("user",)
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("title",)

    def get_tags(self, obj):
        return ", ".join([f"#{tag.name}" for tag in obj.get_tags()])

    get_tags.short_description = "Tags"


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = (
        "content_preview",
        "user",
        "page",
        "parent",
        "block_type",
        "content_type",
        "order",
        "created_at",
    )
    list_filter = ("block_type", "content_type", "created_at", "modified_at")
    search_fields = ("content", "user__email", "page__title")
    readonly_fields = ("uuid", "created_at", "modified_at")
    raw_id_fields = ("user", "parent", "page")
    ordering = ("page", "order")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "page", "parent", "order", "collapsed")},
        ),
        ("Content", {"fields": ("content", "content_type", "block_type")}),
        (
            "Properties",
            {
                "fields": ("properties",),
                "description": 'Key-value properties as JSON (e.g., {"priority": "high", "due": "2023-12-31"})',
            },
        ),
        (
            "Media",
            {
                "fields": ("media_url", "media_file", "media_metadata"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("uuid", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def content_preview(self, obj):
        if obj.content:
            return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        elif obj.media_url or obj.media_file:
            return f"[{obj.content_type}] {obj.media_url or 'file'}"
        else:
            return "[empty block]"

    content_preview.short_description = "Content Preview"

    def get_tags(self, obj):
        return ", ".join([f"#{tag.name}" for tag in obj.get_tags()])

    get_tags.short_description = "Tags"


@admin.register(PageLink)
class PageLinkAdmin(admin.ModelAdmin):
    list_display = ("source_block", "target_page", "created_at")
    list_filter = ("created_at",)
    search_fields = ("source_block__content", "target_page__title")
    readonly_fields = ("uuid", "created_at", "modified_at")
    raw_id_fields = ("source_block", "target_page")


@admin.register(BlockReference)
class BlockReferenceAdmin(admin.ModelAdmin):
    list_display = ("source_block", "target_block", "created_at")
    list_filter = ("created_at",)
    search_fields = ("source_block__content", "target_block__content")
    readonly_fields = ("uuid", "created_at", "modified_at")
    raw_id_fields = ("source_block", "target_block")
