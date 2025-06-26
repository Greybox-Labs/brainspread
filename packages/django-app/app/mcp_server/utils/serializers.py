from typing import Any, Dict, List


def serialize_page(page) -> Dict[str, Any]:
    """Serialize a Page object for MCP responses"""
    return {
        "uuid": str(page.uuid),
        "title": page.title,
        "slug": page.slug,
        "content": page.content,
        "is_published": page.is_published,
        "page_type": page.page_type,
        "date": page.date.isoformat() if page.date else None,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat(),
        "user_uuid": str(page.user.uuid),
    }


def serialize_block(block) -> Dict[str, Any]:
    """Serialize a Block object for MCP responses"""
    return {
        "uuid": str(block.uuid),
        "content": block.content,
        "content_type": block.content_type,
        "block_type": block.block_type,
        "order": block.order,
        "collapsed": block.collapsed,
        "parent_block_uuid": str(block.parent.uuid) if block.parent else None,
        "page_uuid": str(block.page.uuid),
        "user_uuid": str(block.user.uuid),
        "created_at": block.created_at.isoformat(),
        "updated_at": block.updated_at.isoformat(),
        "media_url": block.media_url,
        "properties": block.properties,
    }


def serialize_page_with_blocks(page, include_blocks: bool = True) -> Dict[str, Any]:
    """Serialize a Page with its nested blocks"""
    page_data = serialize_page(page)
    
    if include_blocks:
        # Get top-level blocks (no parent) ordered by order
        top_level_blocks = page.blocks.filter(parent=None).order_by('order')
        page_data["blocks"] = [serialize_block_with_children(block) for block in top_level_blocks]
    
    return page_data


def serialize_block_with_children(block) -> Dict[str, Any]:
    """Serialize a Block with its nested children"""
    block_data = serialize_block(block)
    
    # Get children blocks ordered by order  
    children = block.children.all().order_by('order')
    if children:
        block_data["children"] = [serialize_block_with_children(child) for child in children]
    
    return block_data


def serialize_search_results(pages: List, blocks: List) -> Dict[str, Any]:
    """Serialize search results containing pages and blocks"""
    return {
        "pages": [serialize_page(page) for page in pages],
        "blocks": [serialize_block(block) for block in blocks],
        "total_results": len(pages) + len(blocks)
    }