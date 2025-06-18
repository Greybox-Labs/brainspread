from datetime import date
from typing import Any, Dict, Optional
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand
from .models import Page, Block




class CreatePageCommand(AbstractBaseCommand):
    """Command to create a new page"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form
        
        page = Page.objects.create(
            user=self.user,
            title=self.form.cleaned_data['title'],
            slug=self.form.cleaned_data.get('slug') or slugify(self.form.cleaned_data['title']),
            content=self.form.cleaned_data.get('content', ''),
            is_published=self.form.cleaned_data.get('is_published', True)
        )
        
        if page.content:
            page.set_tags_from_content(page.content, self.user)
        
        return page


class UpdatePageCommand(AbstractBaseCommand):
    """Command to update an existing page"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Page:
        """Execute the command"""
        super().execute()  # This validates the form
        
        page = Page.objects.get(uuid=self.form.cleaned_data['page_id'], user=self.user)
        
        # Update fields if provided
        if 'title' in self.form.cleaned_data and self.form.cleaned_data['title'] is not None:
            page.title = self.form.cleaned_data['title']
        
        if 'content' in self.form.cleaned_data and self.form.cleaned_data['content'] is not None:
            page.content = self.form.cleaned_data['content']
        
        if 'slug' in self.form.cleaned_data and self.form.cleaned_data['slug'] is not None:
            page.slug = self.form.cleaned_data['slug']
        
        if 'is_published' in self.form.cleaned_data and self.form.cleaned_data['is_published'] is not None:
            page.is_published = self.form.cleaned_data['is_published']
        
        page.save()
        
        if page.content:
            page.set_tags_from_content(page.content, self.user)
        
        return page


class DeletePageCommand(AbstractBaseCommand):
    """Command to delete a page"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> bool:
        """Execute the command"""
        super().execute()  # This validates the form
        
        page = Page.objects.get(uuid=self.form.cleaned_data['page_id'], user=self.user)
        page.delete()
        return True




class GetUserPagesCommand(AbstractBaseCommand):
    """Command to get user's pages"""
    
    def __init__(self, form, user):
        self.form = form
        self.user = user
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command"""
        super().execute()  # This validates the form
        
        published_only = self.form.cleaned_data.get('published_only', True)
        limit = self.form.cleaned_data.get('limit', 10)
        offset = self.form.cleaned_data.get('offset', 0)
        
        queryset = Page.objects.filter(user=self.user)
        if published_only:
            queryset = queryset.filter(is_published=True)
        
        pages = queryset[offset:offset + limit]
        total_count = queryset.count()
        
        return {
            'pages': list(pages),
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        }


class CreateBlockCommand(AbstractBaseCommand):
    """Command to create a new block"""
    
    def __init__(self, user, page, content='', content_type='text', block_type='bullet', 
                 order=0, parent=None, media_url='', media_metadata=None, properties=None):
        self.user = user
        self.page = page
        self.content = content
        self.content_type = content_type
        self.block_type = block_type
        self.order = order
        self.parent = parent
        self.media_url = media_url
        self.media_metadata = media_metadata or {}
        self.properties = properties or {}
    
    def execute(self) -> Block:
        """Execute the command"""
        # Create the block
        block = Block.objects.create(
            user=self.user,
            page=self.page,
            parent=self.parent,
            content=self.content,
            content_type=self.content_type,
            block_type=self.block_type,
            order=self.order,
            media_url=self.media_url,
            media_metadata=self.media_metadata,
            properties=self.properties
        )
        
        # Extract and set tags from content (business logic)
        if block.content:
            block.set_tags_from_content(block.content, self.user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()
        
        return block


class UpdateBlockCommand(AbstractBaseCommand):
    """Command to update an existing block"""
    
    def __init__(self, user, block_id, **updates):
        self.user = user
        self.block_id = block_id
        self.updates = updates
    
    def execute(self) -> Block:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
        except Block.DoesNotExist:
            raise ValidationError("Block not found")
        
        # Update fields
        content_updated = False
        for field, value in self.updates.items():
            if hasattr(block, field):
                setattr(block, field, value)
                if field == 'content':
                    content_updated = True
        
        block.save()
        
        # Extract and set tags if content was updated (business logic)
        if content_updated and block.content:
            block.set_tags_from_content(block.content, self.user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()
        
        return block


class DeleteBlockCommand(AbstractBaseCommand):
    """Command to delete a block"""
    
    def __init__(self, user, block_id):
        self.user = user
        self.block_id = block_id
    
    def execute(self) -> bool:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
            block.delete()
            return True
        except Block.DoesNotExist:
            raise ValidationError("Block not found")


class ToggleBlockTodoCommand(AbstractBaseCommand):
    """Command to toggle a block's todo status"""
    
    def __init__(self, user, block_id):
        self.user = user
        self.block_id = block_id
    
    def execute(self) -> Block:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
        except Block.DoesNotExist:
            raise ValidationError("Block not found")
        
        # Toggle todo status (business logic)
        if block.block_type == 'todo':
            block.block_type = 'done'
        elif block.block_type == 'done':
            block.block_type = 'bullet'
        else:
            block.block_type = 'todo'
        
        block.save()
        return block