from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

from common.models.uuid_mixin import UUIDModelMixin
from common.models.crud_timestamps_mixin import CRUDTimestampsMixin


class Tag(UUIDModelMixin, CRUDTimestampsMixin):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    
    class Meta:
        db_table = 'tags'
        ordering = ('name',)
    
    def __str__(self):
        return f"#{self.name}"


class TaggedItem(UUIDModelMixin, CRUDTimestampsMixin):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tagged_items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )
    
    class Meta:
        db_table = 'tagged_items'
        unique_together = [('tag', 'content_type', 'object_id')]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.tag.name} -> {self.content_object}"


class TaggableMixin(models.Model):
    """
    Mixin to add tagging functionality to any model
    """
    
    class Meta:
        abstract = True
    
    def add_tag(self, tag_name, user):
        """Add a tag to this object"""
        tag, created = Tag.objects.get_or_create(name=tag_name)
        content_type = ContentType.objects.get_for_model(self)
        tagged_item, created = TaggedItem.objects.get_or_create(
            tag=tag,
            content_type=content_type,
            object_id=self.pk,
            defaults={'created_by': user}
        )
        return tagged_item, created
    
    def remove_tag(self, tag_name):
        """Remove a tag from this object"""
        try:
            tag = Tag.objects.get(name=tag_name)
            content_type = ContentType.objects.get_for_model(self)
            TaggedItem.objects.filter(
                tag=tag,
                content_type=content_type,
                object_id=self.pk
            ).delete()
            return True
        except Tag.DoesNotExist:
            return False
    
    def get_tags(self):
        """Get all tags for this object"""
        content_type = ContentType.objects.get_for_model(self)
        tagged_items = TaggedItem.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).select_related('tag')
        return [item.tag for item in tagged_items]
    
    def set_tags_from_content(self, content, user):
        """Extract hashtags from content and set them as tags"""
        import re
        hashtag_pattern = r'#([a-zA-Z0-9_]+)'
        hashtags = re.findall(hashtag_pattern, content)
        
        if hashtags:
            current_tag_names = {tag.name for tag in self.get_tags()}
            new_tag_names = set(hashtags)
            
            # Remove tags that are no longer in content
            for tag_name in current_tag_names - new_tag_names:
                self.remove_tag(tag_name)
            
            # Add new tags
            for tag_name in new_tag_names:
                self.add_tag(tag_name, user)
