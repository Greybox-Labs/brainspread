from typing import Any, Dict, Optional

from mcp.types import Tool
from django.core.exceptions import ValidationError

from knowledge.commands.create_block_command import CreateBlockCommand
from knowledge.commands.update_block_command import UpdateBlockCommand
from knowledge.commands.delete_block_command import DeleteBlockCommand
from knowledge.commands.toggle_block_todo_command import ToggleBlockTodoCommand
from knowledge.models import Page, Block

from ..utils.auth import get_current_user
from ..utils.serializers import serialize_block
from ..utils.validators import validate_uuid, validate_block_type, validate_content_type, validate_positive_integer


class BlockTools:
    """MCP tools for block management"""
    
    def __init__(self, server):
        self.server = server
    
    def register_tools(self):
        """Register all block management tools with the MCP server"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="brainspread_create_block",
                    description="Create new blocks with hierarchy support",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_uuid": {"type": "string", "description": "Target page UUID"},
                            "content": {"type": "string", "description": "Block content"},
                            "parent_uuid": {"type": "string", "description": "Parent block UUID for nesting"},
                            "block_type": {
                                "type": "string",
                                "enum": ["bullet", "todo", "done", "heading", "quote", "code", "divider"],
                                "default": "bullet",
                                "description": "Block type"
                            },
                            "content_type": {
                                "type": "string",
                                "enum": ["text", "markdown", "image", "video", "audio", "file", "embed", "code", "quote"],
                                "default": "text",
                                "description": "Content type"
                            },
                            "order": {
                                "type": "integer",
                                "default": 0,
                                "minimum": 0,
                                "description": "Position within parent/page"
                            }
                        },
                        "required": ["page_uuid", "content"]
                    }
                ),
                Tool(
                    name="brainspread_update_block",
                    description="Edit block content and properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "block_uuid": {"type": "string", "description": "Block identifier"},
                            "content": {"type": "string", "description": "New content"},
                            "block_type": {
                                "type": "string",
                                "enum": ["bullet", "todo", "done", "heading", "quote", "code", "divider"],
                                "description": "New block type"
                            },
                            "properties": {
                                "type": "object",
                                "description": "Key-value properties"
                            }
                        },
                        "required": ["block_uuid"]
                    }
                ),
                Tool(
                    name="brainspread_move_block",
                    description="Move blocks between pages or change hierarchy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "block_uuid": {"type": "string", "description": "Block to move"},
                            "target_page_uuid": {"type": "string", "description": "New page UUID"},
                            "new_parent_uuid": {"type": "string", "description": "New parent UUID (null for top-level)"},
                            "new_order": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Position in new location"
                            }
                        },
                        "required": ["block_uuid"]
                    }
                ),
                Tool(
                    name="brainspread_delete_block",
                    description="Delete blocks and their children",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "block_uuid": {"type": "string", "description": "Block to delete"}
                        },
                        "required": ["block_uuid"]
                    }
                ),
                Tool(
                    name="brainspread_toggle_todo",
                    description="Toggle block between todo/done states",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "block_uuid": {"type": "string", "description": "Block identifier"}
                        },
                        "required": ["block_uuid"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def brainspread_create_block(
            page_uuid: str,
            content: str,
            parent_uuid: Optional[str] = None,
            block_type: str = "bullet",
            content_type: str = "text",
            order: int = 0
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUIDs
                if not validate_uuid(page_uuid):
                    return {"success": False, "error": f"Invalid page UUID: {page_uuid}"}
                
                if parent_uuid and not validate_uuid(parent_uuid):
                    return {"success": False, "error": f"Invalid parent UUID: {parent_uuid}"}
                
                # Validate types
                if not validate_block_type(block_type):
                    return {"success": False, "error": f"Invalid block type: {block_type}"}
                
                if not validate_content_type(content_type):
                    return {"success": False, "error": f"Invalid content type: {content_type}"}
                
                # Validate order
                if validate_positive_integer(order) is None:
                    return {"success": False, "error": f"Invalid order value: {order}"}
                
                # Get page object
                try:
                    page = Page.objects.get(uuid=page_uuid, user=current_user)
                except Page.DoesNotExist:
                    return {"success": False, "error": f"Page not found: {page_uuid}"}
                
                # Get parent if specified
                parent = None
                if parent_uuid:
                    try:
                        parent = Block.objects.get(uuid=parent_uuid, user=current_user, page=page)
                    except Block.DoesNotExist:
                        return {"success": False, "error": f"Parent block not found: {parent_uuid}"}
                
                # Use command directly with signature from codebase
                command = CreateBlockCommand(
                    user=current_user,
                    page=page,
                    content=content,
                    content_type=content_type,
                    block_type=block_type,
                    order=order,
                    parent=parent
                )
                block = command.execute()
                
                return {
                    "success": True, 
                    "block_uuid": str(block.uuid),
                    "block": serialize_block(block)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_update_block(block_uuid: str, **updates) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUID
                if not validate_uuid(block_uuid):
                    return {"success": False, "error": f"Invalid block UUID: {block_uuid}"}
                
                # Validate block_type if provided
                if "block_type" in updates and not validate_block_type(updates["block_type"]):
                    return {"success": False, "error": f"Invalid block type: {updates['block_type']}"}
                
                command = UpdateBlockCommand(current_user, block_uuid, **updates)
                block = command.execute()
                
                return {
                    "success": True, 
                    "block_uuid": str(block.uuid),
                    "block": serialize_block(block)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_move_block(
            block_uuid: str,
            target_page_uuid: Optional[str] = None,
            new_parent_uuid: Optional[str] = None,
            new_order: Optional[int] = None
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUIDs
                if not validate_uuid(block_uuid):
                    return {"success": False, "error": f"Invalid block UUID: {block_uuid}"}
                
                if target_page_uuid and not validate_uuid(target_page_uuid):
                    return {"success": False, "error": f"Invalid target page UUID: {target_page_uuid}"}
                
                if new_parent_uuid and not validate_uuid(new_parent_uuid):
                    return {"success": False, "error": f"Invalid parent UUID: {new_parent_uuid}"}
                
                # Build updates dictionary
                updates = {}
                
                if target_page_uuid:
                    try:
                        target_page = Page.objects.get(uuid=target_page_uuid, user=current_user)
                        updates["page"] = target_page
                    except Page.DoesNotExist:
                        return {"success": False, "error": f"Target page not found: {target_page_uuid}"}
                
                if new_parent_uuid:
                    updates["parent_id"] = new_parent_uuid
                elif new_parent_uuid is None and "parent_id" not in updates:
                    # Explicitly setting parent to None (top-level)
                    updates["parent_id"] = None
                
                if new_order is not None:
                    if validate_positive_integer(new_order) is None:
                        return {"success": False, "error": f"Invalid order value: {new_order}"}
                    updates["order"] = new_order
                
                if not updates:
                    return {"success": False, "error": "No move parameters provided"}
                
                command = UpdateBlockCommand(current_user, block_uuid, **updates)
                block = command.execute()
                
                return {
                    "success": True, 
                    "block_uuid": str(block.uuid),
                    "block": serialize_block(block)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_delete_block(block_uuid: str) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUID
                if not validate_uuid(block_uuid):
                    return {"success": False, "error": f"Invalid block UUID: {block_uuid}"}
                
                command = DeleteBlockCommand(current_user, block_uuid)
                command.execute()
                
                return {
                    "success": True,
                    "message": f"Block {block_uuid} and its children have been deleted"
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_toggle_todo(block_uuid: str) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate UUID
                if not validate_uuid(block_uuid):
                    return {"success": False, "error": f"Invalid block UUID: {block_uuid}"}
                
                command = ToggleBlockTodoCommand(current_user, block_uuid)
                block = command.execute()
                
                return {
                    "success": True, 
                    "block_uuid": str(block.uuid), 
                    "new_type": block.block_type,
                    "block": serialize_block(block)
                }
                
            except ValidationError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}