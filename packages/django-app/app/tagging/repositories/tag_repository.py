from django.contrib.contenttypes.models import ContentType

from common.repositories.base_repository import BaseRepository
from knowledge.models import Block, Page

from ..models import Tag, TaggedItem


class TagRepository(BaseRepository):
    """Repository for tag-related data operations"""

    model = Tag

    def get_tag_by_name(self, name: str, user):
        """Get a tag by name if user has tagged content with it"""
        try:
            # Check if the user has any tagged items with this tag
            tag = Tag.objects.get(name=name)
            if TaggedItem.objects.filter(tag=tag, created_by=user).exists():
                return tag
            return None
        except Tag.DoesNotExist:
            return None

    def get_all_user_tags(self, user):
        """Get all tags for a user"""
        # Get all tags that the user has created tagged items for
        tag_ids = (
            TaggedItem.objects.filter(created_by=user)
            .values_list("tag_id", flat=True)
            .distinct()
        )
        return Tag.objects.filter(id__in=tag_ids).order_by("name")

    def get_tagged_blocks(self, tag_name: str, user):
        """Get all blocks tagged with a specific tag for a user"""
        try:
            tag = Tag.objects.get(name=tag_name)
            block_content_type = ContentType.objects.get_for_model(Block)

            # Get TaggedItem objects for this tag and Block content type created by user
            tagged_items = TaggedItem.objects.filter(
                tag=tag, content_type=block_content_type, created_by=user
            )

            # Get the actual Block objects
            block_ids = [item.object_id for item in tagged_items]
            return Block.objects.filter(id__in=block_ids, user=user).order_by(
                "-modified_at"
            )

        except Tag.DoesNotExist:
            return Block.objects.none()

    def get_tagged_pages(self, tag_name: str, user):
        """Get all pages tagged with a specific tag for a user"""
        try:
            tag = Tag.objects.get(name=tag_name)
            page_content_type = ContentType.objects.get_for_model(Page)

            # Get TaggedItem objects for this tag and Page content type created by user
            tagged_items = TaggedItem.objects.filter(
                tag=tag, content_type=page_content_type, created_by=user
            )

            # Get the actual Page objects
            page_ids = [item.object_id for item in tagged_items]
            return Page.objects.filter(id__in=page_ids, user=user).order_by(
                "-modified_at"
            )

        except Tag.DoesNotExist:
            return Page.objects.none()

    def get_tag_with_content(self, tag_name: str, user):
        """Get a tag along with all its associated content"""
        tag = self.get_tag_by_name(tag_name, user)
        if not tag:
            return None

        return {
            "tag": tag,
            "blocks": self.get_tagged_blocks(tag_name, user),
            "pages": self.get_tagged_pages(tag_name, user),
        }

    def get_tag_stats(self, user):
        """Get statistics about tag usage for a user"""
        user_tags = self.get_all_user_tags(user)
        stats = []

        for tag in user_tags:
            block_count = self.get_tagged_blocks(tag.name, user).count()
            page_count = self.get_tagged_pages(tag.name, user).count()

            stats.append(
                {
                    "tag": tag,
                    "block_count": block_count,
                    "page_count": page_count,
                    "total_count": block_count + page_count,
                }
            )

        return sorted(stats, key=lambda x: x["total_count"], reverse=True)

    def search_tags(self, query: str, user):
        """Search for tags by name"""
        # Get all tags that the user has created tagged items for
        tag_ids = (
            TaggedItem.objects.filter(created_by=user)
            .values_list("tag_id", flat=True)
            .distinct()
        )
        return Tag.objects.filter(id__in=tag_ids, name__icontains=query).order_by(
            "name"
        )
