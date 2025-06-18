from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .forms import CreatePageForm, UpdatePageForm, DeletePageForm, GetUserPagesForm
from .commands import (
    CreatePageCommand,
    UpdatePageCommand,
    DeletePageCommand,
    GetUserPagesCommand,
    CreateBlockCommand,
    UpdateBlockCommand,
    DeleteBlockCommand,
    ToggleBlockTodoCommand,
    GetHistoricalDataCommand,
)


def index(request, date=None):
    return render(request, "knowledge/index.html")


def model_to_dict(instance):
    """Convert model instance to dictionary"""
    data = {
        "id": str(instance.uuid),
        "created_at": instance.created_at.isoformat(),
        "modified_at": instance.modified_at.isoformat(),
    }

    if hasattr(instance, "user"):
        data["user_id"] = str(instance.user.uuid)

    if hasattr(instance, "date"):
        # Ensure date is serialized as YYYY-MM-DD format without timezone conversion
        data["date"] = instance.date.strftime("%Y-%m-%d") if instance.date else None

    if hasattr(instance, "content"):
        data["content"] = instance.content

    if hasattr(instance, "title"):
        data["title"] = instance.title

    if hasattr(instance, "slug"):
        data["slug"] = instance.slug

    if hasattr(instance, "page_type"):
        data["page_type"] = instance.page_type

    if hasattr(instance, "block_type"):
        data["block_type"] = instance.block_type

    if hasattr(instance, "content_type"):
        data["content_type"] = instance.content_type

    if hasattr(instance, "order"):
        data["order"] = instance.order

    if hasattr(instance, "collapsed"):
        data["collapsed"] = instance.collapsed

    if hasattr(instance, "parent"):
        data["parent_id"] = str(instance.parent.uuid) if instance.parent else None

    if hasattr(instance, "page"):
        data["page_id"] = str(instance.page.uuid) if instance.page else None

    if hasattr(instance, "media_url"):
        data["media_url"] = instance.media_url

    if hasattr(instance, "media_file"):
        data["media_file"] = instance.media_file.url if instance.media_file else None

    if hasattr(instance, "media_metadata"):
        data["media_metadata"] = instance.media_metadata

    if hasattr(instance, "properties"):
        data["properties"] = instance.properties

    # Add tags
    if hasattr(instance, "get_tags"):
        data["tags"] = [
            {"name": tag.name, "color": tag.color} for tag in instance.get_tags()
        ]

    return data


def block_to_dict_with_children(block):
    """Convert block to dict with nested children"""
    block_data = model_to_dict(block)
    children = []
    for child in block.get_children():
        children.append(block_to_dict_with_children(child))
    block_data["children"] = children
    return block_data


# Page management endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_page(request):
    """API endpoint to create page"""
    try:
        data = request.data
        form = CreatePageForm(data, request.user)

        if form.is_valid():
            command = CreatePageCommand(form, request.user)
            page = command.execute()
            return Response({"success": True, "data": model_to_dict(page)})
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_page(request):
    """API endpoint to update page"""
    try:
        data = request.data
        form = UpdatePageForm(data, request.user)

        if form.is_valid():
            command = UpdatePageCommand(form, request.user)
            page = command.execute()
            return Response({"success": True, "data": model_to_dict(page)})
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_page(request):
    """API endpoint to delete page"""
    try:
        data = request.data
        form = DeletePageForm(data, request.user)

        if form.is_valid():
            command = DeletePageCommand(form, request.user)
            result = command.execute()
            return Response({"success": True, "data": {"deleted": result}})
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pages(request):
    """API endpoint to get user's pages"""
    try:
        data = request.query_params
        form = GetUserPagesForm(data)

        if form.is_valid():
            command = GetUserPagesCommand(form, request.user)
            result = command.execute()
            return Response(
                {
                    "success": True,
                    "data": {
                        "pages": [model_to_dict(page) for page in result["pages"]],
                        "total_count": result["total_count"],
                        "has_more": result["has_more"],
                    },
                }
            )
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# New block-centric API endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_page_with_blocks(request):
    """Get a page with all its blocks"""
    try:
        from .models import Page
        from datetime import datetime

        # Support both page_id and date parameters
        page_id = request.query_params.get("page_id")
        date_param = request.query_params.get("date")

        if page_id:
            try:
                page = Page.objects.get(uuid=page_id, user=request.user)
            except Page.DoesNotExist:
                return Response(
                    {"success": False, "errors": {"page_id": ["Page not found"]}},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif date_param:
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {
                        "success": False,
                        "errors": {"date": ["Invalid date format. Use YYYY-MM-DD"]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            page, created = Page.get_or_create_daily_note(request.user, target_date)
        else:
            # Default to today's daily note (should not happen in normal flow)
            # Frontend should always pass a date, but fallback to user's timezone
            try:
                import pytz
                from datetime import datetime

                # Use user's stored timezone
                if request.user.timezone and request.user.timezone != "UTC":
                    user_tz = pytz.timezone(request.user.timezone)
                    now_user_tz = timezone.now().astimezone(user_tz)
                    today = now_user_tz.date()
                else:
                    today = timezone.now().date()
            except Exception:
                # Fallback to UTC if timezone is invalid
                today = timezone.now().date()

            page, created = Page.get_or_create_daily_note(request.user, today)

        # Get all root blocks with their nested children
        blocks = []
        for block in page.get_root_blocks():
            blocks.append(block_to_dict_with_children(block))

        return Response(
            {"success": True, "data": {"page": model_to_dict(page), "blocks": blocks}}
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_block(request):
    """Create a new block"""
    try:
        from .models import Block, Page

        data = request.data
        page_id = data.get("page_id")
        content = data.get("content", "")
        parent_id = data.get("parent_id")
        block_type = data.get("block_type", "bullet")
        content_type = data.get("content_type", "text")
        order = data.get("order", 0)
        media_url = data.get("media_url", "")
        media_metadata = data.get("media_metadata", {})
        properties = data.get("properties", {})

        # Validate page exists and belongs to user
        try:
            page = Page.objects.get(uuid=page_id, user=request.user)
        except Page.DoesNotExist:
            return Response(
                {"success": False, "errors": {"page_id": ["Page not found"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate parent if provided
        parent = None
        if parent_id:
            try:
                parent = Block.objects.get(uuid=parent_id, user=request.user, page=page)
            except Block.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "errors": {"parent_id": ["Parent block not found"]},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Use command to create block (includes tag extraction)
        command = CreateBlockCommand(
            user=request.user,
            page=page,
            content=content,
            content_type=content_type,
            block_type=block_type,
            order=order,
            parent=parent,
            media_url=media_url,
            media_metadata=media_metadata,
            properties=properties,
        )
        block = command.execute()

        return Response({"success": True, "data": model_to_dict(block)})

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_block(request):
    """Update a block"""
    try:
        from .models import Block

        data = request.data
        block_id = data.get("block_id")

        if not block_id:
            return Response(
                {"success": False, "errors": {"block_id": ["Block ID is required"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepare updates dict
        updates = {}
        for field in [
            "content",
            "block_type",
            "content_type",
            "order",
            "collapsed",
            "media_url",
            "media_metadata",
            "properties",
        ]:
            if field in data:
                updates[field] = data[field]

        # Use command to update block (includes tag extraction)
        command = UpdateBlockCommand(request.user, block_id, **updates)
        block = command.execute()

        return Response({"success": True, "data": model_to_dict(block)})

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_block(request):
    """Delete a block"""
    try:
        from .models import Block

        block_id = request.data.get("block_id")

        if not block_id:
            return Response(
                {"success": False, "errors": {"block_id": ["Block ID is required"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use command to delete block
        command = DeleteBlockCommand(request.user, block_id)
        result = command.execute()

        return Response({"success": True, "data": {"deleted": result}})

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_block_todo(request):
    """Toggle a block's todo status"""
    try:
        from .models import Block

        block_id = request.data.get("block_id")

        if not block_id:
            return Response(
                {"success": False, "errors": {"block_id": ["Block ID is required"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use command to toggle todo status
        command = ToggleBlockTodoCommand(request.user, block_id)
        block = command.execute()

        return Response({"success": True, "data": model_to_dict(block)})

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_historical_data(request):
    """Get historical pages and blocks"""
    try:
        # Get query parameters
        days_back = int(request.query_params.get("days_back", 30))
        limit = int(request.query_params.get("limit", 50))

        # Use command to get historical data
        command = GetHistoricalDataCommand(
            user=request.user, days_back=days_back, limit=limit
        )
        result = command.execute()

        # Format the data
        pages_data = []
        for page in result["pages"]:
            page_data = model_to_dict(page)
            # Get a few recent blocks from this page
            page_blocks = command.repository.get_page_recent_blocks(page, 3)
            page_data["recent_blocks"] = [model_to_dict(block) for block in page_blocks]
            pages_data.append(page_data)

        blocks_data = []
        for block in result["blocks"]:
            block_data = model_to_dict(block)
            block_data["page_title"] = block.page.title
            blocks_data.append(block_data)

        return Response(
            {
                "success": True,
                "data": {
                    "pages": pages_data,
                    "blocks": blocks_data,
                    "date_range": {
                        "start": result["date_range"]["start"].isoformat(),
                        "end": result["date_range"]["end"].isoformat(),
                        "days_back": result["date_range"]["days_back"],
                    },
                },
            }
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
