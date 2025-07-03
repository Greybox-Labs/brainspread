from typing import Dict, List, Optional, TypedDict

from django.core.exceptions import ValidationError
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from knowledge.commands import (
    CreateBlockCommand,
    CreatePageCommand,
    DeleteBlockCommand,
    DeletePageCommand,
    GetHistoricalDataCommand,
    GetPageWithBlocksCommand,
    GetUserPagesCommand,
    MoveUndoneTodosCommand,
    ToggleBlockTodoCommand,
    UpdateBlockCommand,
    UpdatePageCommand,
)
from knowledge.commands.get_historical_data_command import HistoricalData
from knowledge.commands.move_undone_todos_command import MoveUndoneTodosData
from knowledge.forms import (
    CreateBlockForm,
    CreatePageForm,
    DeleteBlockForm,
    DeletePageForm,
    GetHistoricalDataForm,
    GetPageWithBlocksForm,
    GetUserPagesForm,
    MoveUndoneTodosForm,
    ToggleBlockTodoForm,
    UpdateBlockForm,
    UpdatePageForm,
)
from knowledge.models import BlockData, PageData
from tagging.commands import GetTagContentCommand
from tagging.forms import GetTagContentForm
from tagging.models import TagContentData


# Data type definitions for response data fields
class GetPagesData(TypedDict):
    pages: List[PageData]
    total_count: int
    has_more: bool


class GetPageWithBlocksData(TypedDict):
    page: PageData
    blocks: List[BlockData]


# API Response Types with specific data types
class CreatePageResponse(TypedDict):
    success: bool
    data: Optional[PageData]
    errors: Optional[Dict[str, List[str]]]


class UpdatePageResponse(TypedDict):
    success: bool
    data: Optional[PageData]
    errors: Optional[Dict[str, List[str]]]


class GetUserPagesResponse(TypedDict):
    success: bool
    data: Optional[GetPagesData]
    errors: Optional[Dict[str, List[str]]]


class DeletePageResponse(TypedDict):
    success: bool
    data: Optional[Dict[str, str]]
    errors: Optional[Dict[str, List[str]]]


class CreateBlockResponse(TypedDict):
    success: bool
    data: Optional[BlockData]
    errors: Optional[Dict[str, List[str]]]


class UpdateBlockResponse(TypedDict):
    success: bool
    data: Optional[BlockData]
    errors: Optional[Dict[str, List[str]]]


class ToggleBlockTodoResponse(TypedDict):
    success: bool
    data: Optional[BlockData]
    errors: Optional[Dict[str, List[str]]]


class DeleteBlockResponse(TypedDict):
    success: bool
    data: Optional[Dict[str, str]]
    errors: Optional[Dict[str, List[str]]]


class GetHistoricalDataResponse(TypedDict):
    success: bool
    data: Optional[HistoricalData]
    errors: Optional[Dict[str, List[str]]]


class GetTagContentResponse(TypedDict):
    success: bool
    data: Optional[TagContentData]
    errors: Optional[Dict[str, List[str]]]


class GetPagesResponse(TypedDict):
    success: bool
    data: Optional[GetPagesData]
    errors: Optional[Dict[str, List[str]]]


class GetPageWithBlocksResponse(TypedDict):
    success: bool
    data: Optional[GetPageWithBlocksData]
    errors: Optional[Dict[str, List[str]]]


class MoveUndoneTodosResponse(TypedDict):
    success: bool
    data: Optional[MoveUndoneTodosData]
    errors: Optional[Dict[str, List[str]]]


def index(request, date=None, tag_name=None, slug=None):
    return render(request, "knowledge/index.html")


# Page management endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_page(request):
    """API endpoint to create page"""
    try:
        data = request.data
        data["user"] = request.user.id
        form = CreatePageForm(data)

        if form.is_valid():
            command = CreatePageCommand(form)
            page = command.execute()

            response: CreatePageResponse = {
                "success": True,
                "data": page.to_dict(),
                "errors": None,
            }

            return Response(response)
        else:
            response: CreatePageResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        response: CreatePageResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response: CreatePageResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tag_content(request, tag_name):
    """Get all content (blocks and pages) associated with a specific tag"""
    try:
        # Use command to get tag content
        data = {"user": request.user.id, "tag_name": tag_name}
        form = GetTagContentForm(data)

        if not form.is_valid():
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        command = GetTagContentCommand(form)
        result = command.execute()

        if not result:
            return Response(
                {"success": False, "errors": {"tag": ["Tag not found"]}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Format the response data
        blocks_data = []
        for block in result["blocks"]:
            blocks_data.append(block.to_dict(include_page_context=True))

        pages_data = []
        for page in result["pages"]:
            pages_data.append(page.to_dict())

        tag_content_data: TagContentData = {
            "tag": result["tag"].to_dict(),
            "blocks": blocks_data,
            "pages": pages_data,
            "total_blocks": len(blocks_data),
            "total_pages": len(pages_data),
            "total_content": len(blocks_data) + len(pages_data),
        }

        response: GetTagContentResponse = {
            "success": True,
            "data": tag_content_data,
            "errors": None,
        }

        return Response(response)

    except Exception as e:
        response: GetTagContentResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_page(request):
    """API endpoint to update page"""
    try:
        data = request.data
        data["user"] = request.user.id
        form = UpdatePageForm(data)

        if form.is_valid():
            command = UpdatePageCommand(form)
            page = command.execute()

            response: UpdatePageResponse = {
                "success": True,
                "data": page.to_dict(),
                "errors": None,
            }

            return Response(response)
        else:
            response: UpdatePageResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        response: UpdatePageResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_page(request):
    """API endpoint to delete page"""
    try:
        data = request.data
        data["user"] = request.user.id
        form = DeletePageForm(data)

        if form.is_valid():
            command = DeletePageCommand(form)
            command.execute()

            response: DeletePageResponse = {
                "success": True,
                "data": {"message": "Page deleted successfully"},
                "errors": None,
            }

            return Response(response)
        else:
            response: DeletePageResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        response: DeletePageResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response: DeletePageResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pages(request):
    """API endpoint to get user's pages"""
    try:
        data = request.query_params.copy()
        data["user"] = request.user.id
        form = GetUserPagesForm(data)

        if form.is_valid():
            command = GetUserPagesCommand(form)
            result = command.execute()

            pages_data: GetPagesData = {
                "pages": [page.to_dict() for page in result["pages"]],
                "total_count": result["total_count"],
                "has_more": result["has_more"],
            }

            response: GetPagesResponse = {
                "success": True,
                "data": pages_data,
                "errors": None,
            }

            return Response(response)
        else:
            response: GetPagesResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response: GetPagesResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# New block-centric API endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_page_with_blocks(request):
    """Get a page with all its blocks"""
    try:
        data = request.query_params.copy()
        data["user"] = request.user.id
        form = GetPageWithBlocksForm(data)

        if form.is_valid():
            command = GetPageWithBlocksCommand(form)
            page, blocks = command.execute()

            page_with_blocks_data: GetPageWithBlocksData = {
                "page": page.to_dict(),
                "blocks": [block.to_dict_with_children() for block in blocks],
            }

            response: GetPageWithBlocksResponse = {
                "success": True,
                "data": page_with_blocks_data,
                "errors": None,
            }

            return Response(response)
        else:
            response: GetPageWithBlocksResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        response: GetPageWithBlocksResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_block(request):
    """Create a new block"""
    try:
        data = request.data.copy()
        data["user"] = request.user.id

        form = CreateBlockForm(data)

        if form.is_valid():
            command = CreateBlockCommand(form)
            block = command.execute()

            response: CreateBlockResponse = {
                "success": True,
                "data": block.to_dict(),
                "errors": None,
            }

            return Response(response)
        else:
            response: CreateBlockResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response: CreateBlockResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_block(request):
    """Update a block"""
    try:
        data = request.data.copy()
        data["user"] = request.user.id

        form = UpdateBlockForm(data)

        if form.is_valid():
            command = UpdateBlockCommand(form)
            block = command.execute()

            response: UpdateBlockResponse = {
                "success": True,
                "data": block.to_dict(),
                "errors": None,
            }

            return Response(response)
        else:
            response: UpdateBlockResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        response: UpdateBlockResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_block(request):
    """Delete a block"""
    try:
        data = request.data.copy()
        data["user"] = request.user.id

        form = DeleteBlockForm(data)

        if form.is_valid():
            command = DeleteBlockCommand(form)
            command.execute()

            response: DeleteBlockResponse = {
                "success": True,
                "data": {"message": "Block deleted successfully"},
                "errors": None,
            }

            return Response(response)
        else:
            response: DeleteBlockResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        response: DeleteBlockResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        response: DeleteBlockResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_block_todo(request):
    """Toggle a block's todo status"""
    try:
        data = request.data.copy()
        data["user"] = request.user.id

        form = ToggleBlockTodoForm(data)

        if form.is_valid():
            command = ToggleBlockTodoCommand(form)
            block = command.execute()

            response: ToggleBlockTodoResponse = {
                "success": True,
                "data": block.to_dict(),
                "errors": None,
            }

            return Response(response)
        else:
            response: ToggleBlockTodoResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        response: ToggleBlockTodoResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_historical_data(request):
    """Get historical pages and blocks"""
    try:
        # Create and validate form
        form_data = request.query_params.copy()
        form_data["user"] = request.user.pk
        form = GetHistoricalDataForm(form_data)
        if not form.is_valid():
            response: GetHistoricalDataResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Use command to get historical data
        command = GetHistoricalDataCommand(form=form)
        result: HistoricalData = command.execute()

        response: GetHistoricalDataResponse = {
            "success": True,
            "data": result,
            "errors": None,
        }

        return Response(response)

    except Exception as e:
        response: GetHistoricalDataResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def move_undone_todos(request):
    """Move past undone TODOs to current day or specified date"""
    try:
        form_data = {"user": request.user}

        # Check if target_date is provided in request data
        if hasattr(request, "data") and "target_date" in request.data:
            form_data["target_date"] = request.data["target_date"]

        form = MoveUndoneTodosForm(form_data)

        if not form.is_valid():
            response: MoveUndoneTodosResponse = {
                "success": False,
                "data": None,
                "errors": form.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        command = MoveUndoneTodosCommand(form)
        result = command.execute()

        todos_data: MoveUndoneTodosData = {
            "moved_count": result["moved_count"],
            "target_page": result["target_page"],
            "moved_blocks": result["moved_blocks"],
            "message": result["message"],
        }

        response: MoveUndoneTodosResponse = {
            "success": True,
            "data": todos_data,
            "errors": None,
        }

        return Response(response)

    except Exception as e:
        response: MoveUndoneTodosResponse = {
            "success": False,
            "data": None,
            "errors": {"non_field_errors": [str(e)]},
        }
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
