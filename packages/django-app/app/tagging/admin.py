from django.contrib import admin

from .models import Tag, TaggedItem


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "created_at", "modified_at")
    list_filter = ("created_at", "modified_at")
    search_fields = ("name",)
    readonly_fields = ("uuid", "created_at", "modified_at")
    ordering = ("name",)


@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ("tag", "content_type", "object_id", "created_by", "created_at")
    list_filter = ("content_type", "created_at")
    search_fields = ("tag__name",)
    readonly_fields = ("uuid", "created_at", "modified_at")
    raw_id_fields = ("created_by",)
