from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AIProvider,
    ChatMessage,
    ChatSession,
    UserAISettings,
    UserProviderConfig,
)


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ["name", "base_url", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "modified_at"]

    fieldsets = (
        (None, {"fields": ("name", "base_url")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["id", "created_at", "content_preview"]
    fields = ["role", "content_preview", "created_at"]

    def content_preview(self, obj):
        if obj.content:
            preview = (
                obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
            )
            return format_html(
                '<div style="max-width: 300px; white-space: pre-wrap;">{}</div>',
                preview,
            )
        return "-"

    content_preview.short_description = "Content Preview"


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["title_or_id", "user", "message_count", "created_at", "modified_at"]
    list_filter = ["created_at", "modified_at"]
    search_fields = ["title", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["id", "created_at", "modified_at", "message_count"]
    raw_id_fields = ["user"]
    inlines = [ChatMessageInline]

    fieldsets = (
        (None, {"fields": ("user", "title")}),
        (
            "Statistics",
            {
                "fields": ("message_count",),
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def title_or_id(self, obj):
        return obj.title or f"Session {str(obj.id)[:8]}..."

    title_or_id.short_description = "Title"

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Messages"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["session_title", "role", "content_preview", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["content", "session__title", "session__user__email"]
    readonly_fields = ["id", "created_at", "modified_at"]
    raw_id_fields = ["session"]

    fieldsets = (
        (None, {"fields": ("session", "role", "content")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def session_title(self, obj):
        return obj.session.title or f"Session {str(obj.session.id)[:8]}..."

    session_title.short_description = "Session"

    def content_preview(self, obj):
        if obj.content:
            preview = (
                obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
            )
            return format_html(
                '<div style="max-width: 400px; white-space: pre-wrap;">{}</div>',
                preview,
            )
        return "-"

    content_preview.short_description = "Content Preview"


@admin.register(UserAISettings)
class UserAISettingsAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "default_model", "has_api_key", "created_at"]
    list_filter = ["provider", "created_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "default_model",
    ]
    readonly_fields = ["id", "created_at", "modified_at"]
    raw_id_fields = ["user", "provider"]

    fieldsets = (
        (None, {"fields": ("user", "provider", "default_model")}),
        (
            "API Configuration",
            {
                "fields": ("api_key",),
                "description": "API key is stored securely and masked in the admin interface.",
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def has_api_key(self, obj):
        return bool(obj.api_key)

    has_api_key.boolean = True
    has_api_key.short_description = "Has API Key"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.api_key:
            form.base_fields["api_key"].widget.attrs[
                "placeholder"
            ] = "*** API Key Set ***"
        return form


@admin.register(UserProviderConfig)
class UserProviderConfigAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "provider",
        "is_enabled",
        "has_api_key",
        "enabled_models_count",
        "created_at",
    ]
    list_filter = ["provider", "is_enabled", "created_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "provider__name",
    ]
    readonly_fields = ["id", "created_at", "modified_at"]
    raw_id_fields = ["user", "provider"]

    fieldsets = (
        (None, {"fields": ("user", "provider", "is_enabled")}),
        (
            "API Configuration",
            {
                "fields": ("api_key",),
                "description": "API key is stored securely and masked in the admin interface.",
            },
        ),
        (
            "Model Configuration",
            {
                "fields": ("enabled_models",),
                "description": "JSON list of enabled models for this provider.",
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    def has_api_key(self, obj):
        return bool(obj.api_key)

    has_api_key.boolean = True
    has_api_key.short_description = "Has API Key"

    def enabled_models_count(self, obj):
        return len(obj.enabled_models) if obj.enabled_models else 0

    enabled_models_count.short_description = "Enabled Models"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.api_key:
            form.base_fields["api_key"].widget.attrs[
                "placeholder"
            ] = "*** API Key Set ***"
        return form
