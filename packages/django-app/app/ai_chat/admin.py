from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AIModel,
    AIProvider,
    APIKeyAudit,
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


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "display_name", "is_active", "created_at"]
    list_filter = ["provider", "is_active", "created_at"]
    search_fields = ["name", "display_name", "description"]
    readonly_fields = ["id", "created_at", "modified_at"]
    raw_id_fields = ["provider"]

    fieldsets = (
        (None, {"fields": ("name", "provider", "display_name", "is_active")}),
        (
            "Description",
            {"fields": ("description",), "classes": ("wide",)},
        ),
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
    list_display = ["user", "preferred_model", "created_at"]
    list_filter = ["created_at", "preferred_model__provider"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "preferred_model__name",
        "preferred_model__display_name",
    ]
    readonly_fields = ["id", "created_at", "modified_at"]
    raw_id_fields = ["user", "preferred_model"]

    fieldsets = (
        (None, {"fields": ("user", "preferred_model")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )


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
                "fields": ("api_key_status", "api_key"),
                "description": "API keys are encrypted and stored securely. Legacy plain-text field shown for migration purposes only.",
            },
        ),
        (
            "Model Configuration",
            {
                "fields": ("enabled_models",),
                "description": "Models that this user has enabled for this provider.",
            },
        ),
        (
            "Security Information",
            {
                "fields": ("encryption_status", "encrypted_api_key", "api_key_salt", "api_key_hash", "api_key_hash_salt"),
                "classes": ("collapse",),
                "description": "Encrypted storage fields - do not modify manually.",
            },
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "modified_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ["id", "created_at", "modified_at", "api_key_status", "encryption_status"]

    def has_api_key(self, obj):
        return obj.has_api_key()

    has_api_key.boolean = True
    has_api_key.short_description = "Has API Key"

    def api_key_status(self, obj):
        """Show secure status of API key."""
        if obj.has_api_key():
            if obj.encrypted_api_key and obj.api_key_salt:
                return format_html('<span style="color: green;">🔒 Encrypted</span>')
            elif obj.api_key_hash and obj.api_key_hash_salt:
                return format_html('<span style="color: blue;">🔐 Hash-only (verification)</span>')
            elif obj.api_key:
                return format_html('<span style="color: orange;">⚠️ Legacy (plain text)</span>')
        return format_html('<span style="color: gray;">❌ No key configured</span>')

    api_key_status.short_description = "API Key Status"

    def encryption_status(self, obj):
        """Show detailed encryption information."""
        status_parts = []
        
        if obj.encrypted_api_key and obj.api_key_salt:
            status_parts.append("✅ Encrypted data present")
        else:
            status_parts.append("❌ No encrypted data")
            
        if obj.api_key_hash and obj.api_key_hash_salt:
            status_parts.append("✅ Hash data present")
        else:
            status_parts.append("❌ No hash data")
            
        if obj.api_key:
            status_parts.append("⚠️ Legacy plain text present")
        else:
            status_parts.append("✅ No plain text data")
            
        return format_html("<br>".join(status_parts))

    encryption_status.short_description = "Encryption Details"

    def enabled_models_count(self, obj):
        return obj.enabled_models.count()

    enabled_models_count.short_description = "Enabled Models"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Mask the legacy API key field if it has a value
        if obj and obj.api_key:
            form.base_fields["api_key"].widget.attrs[
                "placeholder"
            ] = "*** Legacy API Key Set ***"
            
        # Make encrypted fields read-only to prevent manual modification
        encrypted_fields = ['encrypted_api_key', 'api_key_salt', 'api_key_hash', 'api_key_hash_salt']
        for field_name in encrypted_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].widget.attrs['readonly'] = True
                form.base_fields[field_name].help_text = "Read-only field - managed by system"
                
        return form


@admin.register(APIKeyAudit)
class APIKeyAuditAdmin(admin.ModelAdmin):
    """Admin interface for API key audit logs."""
    
    list_display = [
        "user_email",
        "provider_name", 
        "operation",
        "success",
        "ip_address",
        "created_at"
    ]
    list_filter = [
        "operation",
        "success", 
        "provider",
        "created_at"
    ]
    search_fields = [
        "user__email",
        "user__first_name", 
        "user__last_name",
        "provider__name",
        "ip_address",
        "error_message"
    ]
    readonly_fields = [
        "id", 
        "uuid",
        "user", 
        "provider",
        "operation",
        "ip_address",
        "user_agent", 
        "metadata",
        "success",
        "error_message",
        "created_at",
        "modified_at"
    ]
    
    fieldsets = (
        (None, {
            "fields": ("user", "provider", "operation", "success")
        }),
        (
            "Request Information", {
                "fields": ("ip_address", "user_agent"),
                "description": "Information about the request that triggered this audit log."
            }
        ),
        (
            "Operation Details", {
                "fields": ("metadata", "error_message"),
                "description": "Additional details about the operation."
            }
        ),
        (
            "Metadata", {
                "fields": ("id", "uuid", "created_at", "modified_at"),
                "classes": ("collapse",)
            }
        )
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"
    
    def provider_name(self, obj):
        return obj.provider.name  
    provider_name.short_description = "Provider"
    provider_name.admin_order_field = "provider__name"
    
    def has_add_permission(self, request):
        """Prevent adding audit logs through admin."""
        return False
        
    def has_change_permission(self, request, obj=None):
        """Prevent modifying audit logs through admin.""" 
        return False
        
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup purposes."""
        return request.user.is_superuser
