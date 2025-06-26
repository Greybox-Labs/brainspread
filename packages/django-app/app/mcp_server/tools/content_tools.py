from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from mcp.types import Tool
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from knowledge.models import Page, Block
from tagging.commands.get_tag_content_command import GetTagContentCommand
from knowledge.commands import GetHistoricalDataCommand
from knowledge.forms.get_historical_data_form import GetHistoricalDataForm

from ..utils.auth import get_current_user
from ..utils.serializers import serialize_page, serialize_block, serialize_search_results
from ..utils.validators import validate_uuid, validate_positive_integer, validate_date_string, sanitize_search_query


class ContentTools:
    """MCP tools for content organization and search"""
    
    def __init__(self, server):
        self.server = server
    
    def register_tools(self):
        """Register all content organization tools with the MCP server"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="brainspread_search_content",
                    description="Search across pages and blocks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search term"},
                            "content_type": {
                                "type": "string",
                                "enum": ["text", "markdown", "image", "video", "audio", "file", "embed", "code", "quote"],
                                "description": "Filter by content type"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by tags"
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                                    "end": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                                },
                                "description": "Date range filter"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="brainspread_get_tag_content",
                    description="Retrieve all content with specific tags",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tag_name": {"type": "string", "description": "Tag to search for"},
                            "limit": {
                                "type": "integer",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Max results"
                            }
                        },
                        "required": ["tag_name"]
                    }
                ),
                Tool(
                    name="brainspread_get_backlinks",
                    description="Find all references to a page or block",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_uuid": {"type": "string", "description": "Page or block UUID"},
                            "type": {
                                "type": "string",
                                "enum": ["page", "block"],
                                "description": "Target type"
                            }
                        },
                        "required": ["target_uuid", "type"]
                    }
                ),
                Tool(
                    name="brainspread_get_daily_note",
                    description="Get or create daily note for specific date",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format",
                                "pattern": r"^\d{4}-\d{2}-\d{2}$"
                            },
                            "create_if_missing": {
                                "type": "boolean",
                                "default": True,
                                "description": "Auto-create if not exists"
                            }
                        },
                        "required": ["date"]
                    }
                ),
                Tool(
                    name="brainspread_get_historical_data",
                    description="Retrieve content from specific time periods",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "default": 30,
                                "minimum": 1,
                                "maximum": 365,
                                "description": "Days to look back"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Max results"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def brainspread_search_content(
            query: str,
            content_type: Optional[str] = None,
            tags: Optional[List[str]] = None,
            date_range: Optional[Dict[str, str]] = None
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                query = sanitize_search_query(query)
                
                if not query:
                    return {"success": False, "error": "Search query cannot be empty"}
                
                # Build search filters
                page_filters = Q(user=current_user)
                block_filters = Q(user=current_user)
                
                # Text search
                page_filters &= (Q(title__icontains=query) | Q(content__icontains=query))
                block_filters &= Q(content__icontains=query)
                
                # Content type filter
                if content_type:
                    block_filters &= Q(content_type=content_type)
                
                # Date range filter
                if date_range:
                    start_date = date_range.get("start")
                    end_date = date_range.get("end")
                    
                    if start_date and validate_date_string(start_date):
                        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                        page_filters &= Q(created_at__gte=start_datetime)
                        block_filters &= Q(created_at__gte=start_datetime)
                    
                    if end_date and validate_date_string(end_date):
                        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                        # Add one day to include the full end date
                        end_datetime = end_datetime + timedelta(days=1)
                        page_filters &= Q(created_at__lt=end_datetime)
                        block_filters &= Q(created_at__lt=end_datetime)
                
                # Execute searches
                pages = Page.objects.filter(page_filters)[:50]
                blocks = Block.objects.filter(block_filters)[:50]
                
                # Tag filtering (post-query since tags are handled differently)
                if tags:
                    # Filter pages and blocks that have any of the specified tags
                    tagged_page_ids = set()
                    tagged_block_ids = set()
                    
                    for tag in tags:
                        # This would need to be implemented based on your tagging system
                        # For now, we'll do a simple content-based tag search
                        tag_pattern = f"#{tag}"
                        tagged_pages = pages.filter(content__icontains=tag_pattern)
                        tagged_blocks = blocks.filter(content__icontains=tag_pattern)
                        
                        tagged_page_ids.update(p.id for p in tagged_pages)
                        tagged_block_ids.update(b.id for b in tagged_blocks)
                    
                    pages = pages.filter(id__in=tagged_page_ids)
                    blocks = blocks.filter(id__in=tagged_block_ids)
                
                return {
                    "success": True,
                    "results": serialize_search_results(pages, blocks)
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_get_tag_content(tag_name: str, limit: int = 50) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                command = GetTagContentCommand(current_user, tag_name)
                result = command.execute()
                
                return {
                    "success": True, 
                    "data": result,
                    "tag_name": tag_name
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_get_backlinks(target_uuid: str, type: str) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUID
                if not validate_uuid(target_uuid):
                    return {"success": False, "error": f"Invalid UUID: {target_uuid}"}
                
                if type == "page":
                    try:
                        page = Page.objects.get(uuid=target_uuid, user=current_user)
                        backlinks = page.get_backlinks()
                        return {
                            "success": True,
                            "target": serialize_page(page),
                            "backlinks": [serialize_block(block) for block in backlinks]
                        }
                    except Page.DoesNotExist:
                        return {"success": False, "error": f"Page not found: {target_uuid}"}
                
                elif type == "block":
                    try:
                        block = Block.objects.get(uuid=target_uuid, user=current_user)
                        # Find blocks that reference this block using ((uuid)) pattern
                        backlinks = Block.objects.filter(
                            user=current_user,
                            content__icontains=f"(({target_uuid}))"
                        ).exclude(uuid=target_uuid)
                        
                        return {
                            "success": True,
                            "target": serialize_block(block),
                            "backlinks": [serialize_block(bl) for bl in backlinks]
                        }
                    except Block.DoesNotExist:
                        return {"success": False, "error": f"Block not found: {target_uuid}"}
                
                else:
                    return {"success": False, "error": f"Invalid type: {type}. Must be 'page' or 'block'"}
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_get_daily_note(
            date: str, 
            create_if_missing: bool = True
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate date
                if not validate_date_string(date):
                    return {"success": False, "error": f"Invalid date format: {date}. Use YYYY-MM-DD"}
                
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                
                try:
                    # Try to get existing daily note
                    page = Page.objects.get(
                        user=current_user,
                        page_type="daily",
                        date=date_obj
                    )
                    return {
                        "success": True,
                        "found_existing": True,
                        "page": serialize_page(page)
                    }
                    
                except Page.DoesNotExist:
                    if create_if_missing:
                        # Create new daily note
                        from knowledge.forms.create_page_form import CreatePageForm
                        from knowledge.commands.create_page_command import CreatePageCommand
                        
                        form_data = {
                            "title": f"Daily Note - {date}",
                            "content": f"# {date}\n\n"
                        }
                        
                        form = CreatePageForm(form_data, user=current_user)
                        command = CreatePageCommand(form, current_user)
                        page = command.execute()
                        
                        # Set as daily note
                        page.page_type = "daily"
                        page.date = date_obj
                        page.save()
                        
                        return {
                            "success": True,
                            "found_existing": False,
                            "created": True,
                            "page": serialize_page(page)
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Daily note not found for {date} and create_if_missing is False"
                        }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_get_historical_data(
            days_back: int = 30, 
            limit: int = 50
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                form_data = {
                    "user": current_user.pk, 
                    "days_back": days_back, 
                    "limit": limit
                }
                form = GetHistoricalDataForm(form_data)
                command = GetHistoricalDataCommand(form)
                result = command.execute()
                
                return {
                    "success": True, 
                    "data": result
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}