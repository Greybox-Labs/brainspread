from django.contrib import admin
from .models import JournalEntry, Page


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'created_at', 'modified_at')
    list_filter = ('date', 'created_at', 'modified_at')
    search_fields = ('user__email', 'content')
    readonly_fields = ('uuid', 'created_at', 'modified_at')
    raw_id_fields = ('user',)
    date_hierarchy = 'date'
    ordering = ('-date',)
    
    def get_tags(self, obj):
        return ', '.join([f"#{tag.name}" for tag in obj.get_tags()])
    get_tags.short_description = 'Tags'


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'slug', 'is_published', 'created_at', 'modified_at')
    list_filter = ('is_published', 'created_at', 'modified_at')
    search_fields = ('title', 'user__email', 'content')
    readonly_fields = ('uuid', 'created_at', 'modified_at')
    raw_id_fields = ('user',)
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('title',)
    
    def get_tags(self, obj):
        return ', '.join([f"#{tag.name}" for tag in obj.get_tags()])
    get_tags.short_description = 'Tags'
