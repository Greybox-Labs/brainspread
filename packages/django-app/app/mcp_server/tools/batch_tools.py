from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.types import Tool
from django.core.exceptions import ValidationError
from django.db import transaction

from knowledge.commands.create_block_command import CreateBlockCommand
from knowledge.commands.update_block_command import UpdateBlockCommand
from knowledge.models import Page, Block

from ..utils.auth import get_current_user
from ..utils.serializers import serialize_block
from ..utils.validators import (
    validate_uuid, validate_block_type, validate_content_type, 
    validate_positive_integer, validate_date_string
)


class BatchTools:
    """MCP tools for batch operations"""
    
    def __init__(self, server):
        self.server = server
    
    def register_tools(self):
        """Register all batch operation tools with the MCP server"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="brainspread_bulk_create_blocks",
                    description="Create multiple blocks efficiently (for TODO lists)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_uuid": {"type": "string", "description": "Target page UUID"},
                            "blocks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "content": {"type": "string", "description": "Block content"},
                                        "block_type": {
                                            "type": "string",
                                            "enum": ["bullet", "todo", "done", "heading", "quote", "code", "divider"],
                                            "default": "bullet"
                                        },
                                        "content_type": {
                                            "type": "string",
                                            "enum": ["text", "markdown", "image", "video", "audio", "file", "embed", "code", "quote"],
                                            "default": "text"
                                        },
                                        "parent_uuid": {"type": "string", "description": "Parent block UUID"},
                                        "order": {"type": "integer", "minimum": 0, "default": 0}
                                    },
                                    "required": ["content"]
                                },
                                "description": "Array of block definitions"
                            }
                        },
                        "required": ["page_uuid", "blocks"]
                    }
                ),
                Tool(
                    name="brainspread_bulk_move_blocks",
                    description="Move multiple blocks while preserving relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "block_uuid": {"type": "string", "description": "Block to move"},
                                        "target_page_uuid": {"type": "string", "description": "New page UUID"},
                                        "new_parent_uuid": {"type": "string", "description": "New parent UUID"},
                                        "new_order": {"type": "integer", "minimum": 0}
                                    },
                                    "required": ["block_uuid"]
                                },
                                "description": "Array of move operations"
                            },
                            "preserve_hierarchy": {
                                "type": "boolean",
                                "default": True,
                                "description": "Maintain parent/child relationships"
                            }
                        },
                        "required": ["operations"]
                    }
                ),
                Tool(
                    name="brainspread_move_blocks_by_date",
                    description="Move blocks from one date to another (key use case)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_date": {
                                "type": "string",
                                "description": "Source date (YYYY-MM-DD)",
                                "pattern": r"^\d{4}-\d{2}-\d{2}$"
                            },
                            "target_date": {
                                "type": "string", 
                                "description": "Target date (YYYY-MM-DD)",
                                "pattern": r"^\d{4}-\d{2}-\d{2}$"
                            },
                            "block_uuids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific blocks to move (if empty, moves all)"
                            },
                            "preserve_hierarchy": {
                                "type": "boolean",
                                "default": True,
                                "description": "Keep parent/child relationships"
                            }
                        },
                        "required": ["source_date", "target_date"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def brainspread_bulk_create_blocks(
            page_uuid: str,
            blocks: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate page UUID
                if not validate_uuid(page_uuid):
                    return {"success": False, "error": f"Invalid page UUID: {page_uuid}"}
                
                # Get page object
                try:
                    page = Page.objects.get(uuid=page_uuid, user=current_user)
                except Page.DoesNotExist:
                    return {"success": False, "error": f"Page not found: {page_uuid}"}
                
                created_blocks = []
                errors = []
                
                with transaction.atomic():
                    for i, block_data in enumerate(blocks):
                        try:
                            # Extract and validate block data
                            content = block_data.get("content", "")
                            block_type = block_data.get("block_type", "bullet")
                            content_type = block_data.get("content_type", "text")
                            parent_uuid = block_data.get("parent_uuid")
                            order = block_data.get("order", i)  # Default to index
                            
                            # Validate types
                            if not validate_block_type(block_type):
                                errors.append(f"Block {i}: Invalid block type: {block_type}")
                                continue
                            
                            if not validate_content_type(content_type):
                                errors.append(f"Block {i}: Invalid content type: {content_type}")
                                continue
                            
                            # Get parent if specified
                            parent = None
                            if parent_uuid:
                                if not validate_uuid(parent_uuid):
                                    errors.append(f"Block {i}: Invalid parent UUID: {parent_uuid}")
                                    continue
                                try:
                                    parent = Block.objects.get(uuid=parent_uuid, user=current_user, page=page)
                                except Block.DoesNotExist:
                                    errors.append(f"Block {i}: Parent block not found: {parent_uuid}")
                                    continue
                            
                            # Create block
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
                            created_blocks.append(serialize_block(block))
                            
                        except Exception as e:
                            errors.append(f"Block {i}: {str(e)}")
                
                return {
                    "success": len(created_blocks) > 0,
                    "created_count": len(created_blocks),
                    "created_blocks": created_blocks,
                    "errors": errors
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_bulk_move_blocks(
            operations: List[Dict[str, Any]],
            preserve_hierarchy: bool = True
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                moved_blocks = []
                errors = []
                
                with transaction.atomic():
                    for i, operation in enumerate(operations):
                        try:
                            block_uuid = operation.get("block_uuid")
                            target_page_uuid = operation.get("target_page_uuid")
                            new_parent_uuid = operation.get("new_parent_uuid")
                            new_order = operation.get("new_order")
                            
                            # Validate block UUID
                            if not validate_uuid(block_uuid):
                                errors.append(f"Operation {i}: Invalid block UUID: {block_uuid}")
                                continue
                            
                            # Build updates
                            updates = {}
                            
                            if target_page_uuid:
                                if not validate_uuid(target_page_uuid):
                                    errors.append(f"Operation {i}: Invalid target page UUID: {target_page_uuid}")
                                    continue
                                try:
                                    target_page = Page.objects.get(uuid=target_page_uuid, user=current_user)
                                    updates["page"] = target_page
                                except Page.DoesNotExist:
                                    errors.append(f"Operation {i}: Target page not found: {target_page_uuid}")
                                    continue
                            
                            if new_parent_uuid:
                                updates["parent_id"] = new_parent_uuid
                            elif new_parent_uuid is None:
                                updates["parent_id"] = None
                            
                            if new_order is not None:
                                if validate_positive_integer(new_order) is None:
                                    errors.append(f"Operation {i}: Invalid order: {new_order}")
                                    continue
                                updates["order"] = new_order
                            
                            if updates:
                                command = UpdateBlockCommand(current_user, block_uuid, **updates)
                                block = command.execute()
                                moved_blocks.append(serialize_block(block))
                            
                        except Exception as e:
                            errors.append(f"Operation {i}: {str(e)}")
                
                return {
                    "success": len(moved_blocks) > 0,
                    "moved_count": len(moved_blocks),
                    "moved_blocks": moved_blocks,
                    "errors": errors
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.call_tool()
        async def brainspread_move_blocks_by_date(
            source_date: str,
            target_date: str,
            block_uuids: Optional[List[str]] = None,
            preserve_hierarchy: bool = True
        ) -> Dict[str, Any]:
            try:
                current_user = get_current_user()
                
                # Validate dates
                if not validate_date_string(source_date):
                    return {"success": False, "error": f"Invalid source date: {source_date}"}
                
                if not validate_date_string(target_date):
                    return {"success": False, "error": f"Invalid target date: {target_date}"}
                
                # Get source daily note
                source_date_obj = datetime.strptime(source_date, "%Y-%m-%d").date()
                try:
                    source_page = Page.objects.get(
                        user=current_user,
                        page_type="daily",
                        date=source_date_obj
                    )
                except Page.DoesNotExist:
                    return {"success": False, "error": f"Source daily note not found for {source_date}"}
                
                # Get or create target daily note
                target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
                try:
                    target_page = Page.objects.get(
                        user=current_user,
                        page_type="daily",
                        date=target_date_obj
                    )
                except Page.DoesNotExist:
                    # Create target daily note
                    from knowledge.forms.create_page_form import CreatePageForm
                    from knowledge.commands.create_page_command import CreatePageCommand
                    
                    form_data = {
                        "title": f"Daily Note - {target_date}",
                        "content": f"# {target_date}\n\n"
                    }
                    
                    form = CreatePageForm(form_data, user=current_user)
                    command = CreatePageCommand(form, current_user)
                    target_page = command.execute()
                    
                    target_page.page_type = "daily"
                    target_page.date = target_date_obj
                    target_page.save()
                
                # Get blocks to move
                if block_uuids:
                    # Validate UUIDs
                    for uuid_str in block_uuids:
                        if not validate_uuid(uuid_str):
                            return {"success": False, "error": f"Invalid block UUID: {uuid_str}"}
                    
                    blocks_to_move = Block.objects.filter(
                        uuid__in=block_uuids,
                        user=current_user,
                        page=source_page
                    )
                else:
                    # Move all blocks from source page
                    blocks_to_move = Block.objects.filter(
                        user=current_user,
                        page=source_page
                    )
                
                moved_blocks = []
                errors = []
                
                with transaction.atomic():
                    for block in blocks_to_move:
                        try:
                            # Move block to target page
                            updates = {"page": target_page}
                            
                            # If preserving hierarchy and parent is not being moved, 
                            # set parent to None to avoid cross-page references
                            if preserve_hierarchy and block.parent:
                                if block.parent.page != target_page:
                                    updates["parent_id"] = None
                            
                            command = UpdateBlockCommand(current_user, str(block.uuid), **updates)
                            moved_block = command.execute()
                            moved_blocks.append(serialize_block(moved_block))
                            
                        except Exception as e:
                            errors.append(f"Block {block.uuid}: {str(e)}")
                
                return {
                    "success": len(moved_blocks) > 0,
                    "moved_count": len(moved_blocks),
                    "moved_blocks": moved_blocks,
                    "source_date": source_date,
                    "target_date": target_date,
                    "target_page_uuid": str(target_page.uuid),
                    "errors": errors
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}