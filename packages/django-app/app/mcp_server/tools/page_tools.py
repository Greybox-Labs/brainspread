from typing import Any, Dict, Optional
from datetime import datetime

from mcp.types import Tool
from django.core.exceptions import ValidationError

from knowledge.commands.create_page_command import CreatePageCommand
from knowledge.commands.update_page_command import UpdatePageCommand
from knowledge.commands.get_user_pages_command import GetUserPagesCommand
from knowledge.forms.create_page_form import CreatePageForm
from knowledge.forms.update_page_form import UpdatePageForm
from knowledge.forms.get_user_pages_form import GetUserPagesForm
from knowledge.models import Page
from knowledge.repositories.page_repository import PageRepository

from ..utils.auth import get_current_user
from ..utils.serializers import serialize_page, serialize_page_with_blocks
from ..utils.validators import validate_page_type, validate_date_string


class PageTools:
    """MCP tools for page management"""
    
    def __init__(self, server):
        self.server = server
    
    def register_tools(self):
        """Register all page management tools with the MCP server"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="brainspread_create_page",
                    description="Create new pages or daily notes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Page title"},
                            "page_type": {
                                "type": "string", 
                                "enum": ["page", "daily", "template"],
                                "default": "page",
                                "description": "Page type"
                            },
                            "date": {
                                "type": "string", 
                                "description": "For daily notes (YYYY-MM-DD)",
                                "pattern": r"^\d{4}-\d{2}-\d{2}$"
                            },
                            "content": {
                                "type": "string", 
                                "default": "",
                                "description": "Initial page content"
                            }
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="brainspread_get_page",
                    description="Retrieve page with all nested blocks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_slug": {"type": "string", "description": "Page slug"},
                            "page_uuid": {"type": "string", "description": "Page UUID"},
                            "date": {
                                "type": "string", 
                                "description": "For daily notes (YYYY-MM-DD)",
                                "pattern": r"^\d{4}-\d{2}-\d{2}$"
                            }
                        }
                    }
                ),
                Tool(
                    name="brainspread_update_page",
                    description="Update page metadata and content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_uuid": {"type": "string", "description": "Page identifier"},
                            "title": {"type": "string", "description": "New title"},
                            "content": {"type": "string", "description": "New content"}
                        },
                        "required": ["page_uuid"]
                    }
                ),
                Tool(
                    name="brainspread_list_pages",
                    description="List user's pages with filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_type": {
                                "type": "string",
                                "enum": ["page", "daily", "template"],
                                "description": "Filter by page type"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Max results"
                            },
                            "search": {"type": "string", "description": "Search term"}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def brainspread_create_page(
            title: str, 
            page_type: str = "page", 
            date: Optional[str] = None, 
            content: str = ""
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate page type
                if not validate_page_type(page_type):
                    return {"success": False, "error": f"Invalid page type: {page_type}"}
                
                # Validate date if provided
                if date and not validate_date_string(date):
                    return {"success": False, "error": f"Invalid date format: {date}. Use YYYY-MM-DD"}
                
                # Create form data
                form_data = {"title": title, "content": content}
                if date:
                    form_data["date"] = date
                    if page_type == "page":  # Auto-set page_type to daily if date provided
                        page_type = "daily"
                
                form = CreatePageForm(form_data, user=current_user)
                command = CreatePageCommand(form, current_user)
                page = command.execute()
                
                # Update page_type if different from default
                if page_type != "page":
                    page.page_type = page_type
                    if date:
                        page.date = datetime.strptime(date, "%Y-%m-%d").date()
                    page.save()
                
                return {
                    "success": True, 
                    "page_uuid": str(page.uuid), 
                    "slug": page.slug,
                    "page": serialize_page(page)
                }
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_get_page(
            page_slug: Optional[str] = None,
            page_uuid: Optional[str] = None,
            date: Optional[str] = None
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                page = None
                
                if date:
                    # Get daily note for specific date
                    if not validate_date_string(date):
                        return {"success": False, "error": f"Invalid date format: {date}. Use YYYY-MM-DD"}
                    
                    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    try:
                        page = Page.objects.get(
                            user=current_user, 
                            page_type="daily", 
                            date=date_obj
                        )
                    except Page.DoesNotExist:
                        return {"success": False, "error": f"Daily note not found for date: {date}"}
                
                elif page_uuid:
                    try:
                        page = Page.objects.get(uuid=page_uuid, user=current_user)
                    except Page.DoesNotExist:
                        return {"success": False, "error": f"Page not found with UUID: {page_uuid}"}
                
                elif page_slug:
                    try:
                        page = Page.objects.get(slug=page_slug, user=current_user)
                    except Page.DoesNotExist:
                        return {"success": False, "error": f"Page not found with slug: {page_slug}"}
                
                else:
                    return {"success": False, "error": "Must provide page_slug, page_uuid, or date"}
                
                return {
                    "success": True,
                    "page": serialize_page_with_blocks(page, include_blocks=True)
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_update_page(
            page_uuid: str,
            title: Optional[str] = None,
            content: Optional[str] = None
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Get the page
                try:
                    page = Page.objects.get(uuid=page_uuid, user=current_user)
                except Page.DoesNotExist:
                    return {"success": False, "error": f"Page not found with UUID: {page_uuid}"}
                
                # Prepare update data
                form_data = {}
                if title is not None:
                    form_data["title"] = title
                if content is not None:
                    form_data["content"] = content
                
                if not form_data:
                    return {"success": False, "error": "No update data provided"}
                
                # Create form and command
                form = UpdatePageForm(form_data, user=current_user, instance=page)
                command = UpdatePageCommand(form, current_user)
                updated_page = command.execute()
                
                return {
                    "success": True,
                    "page_uuid": str(updated_page.uuid),
                    "page": serialize_page(updated_page)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_list_pages(
            page_type: Optional[str] = None,
            limit: int = 50,
            search: Optional[str] = None
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate page_type if provided
                if page_type and not validate_page_type(page_type):
                    return {"success": False, "error": f"Invalid page type: {page_type}"}
                
                # Create form data
                form_data = {"user": current_user.pk, "limit": limit}
                if page_type:
                    form_data["page_type"] = page_type
                if search:
                    form_data["search"] = search
                
                form = GetUserPagesForm(form_data)
                command = GetUserPagesCommand(form)
                pages = command.execute()
                
                return {
                    "success": True,
                    "pages": [serialize_page(page) for page in pages],
                    "count": len(pages)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}