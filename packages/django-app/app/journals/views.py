from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .forms import (
    CreateOrUpdateJournalEntryForm,
    GetJournalEntryForm,
    CreatePageForm,
    UpdatePageForm,
    DeletePageForm,
    GetUserJournalEntriesForm,
    GetUserPagesForm
)
from .commands import (
    CreateOrUpdateJournalEntryCommand,
    GetJournalEntryCommand,
    CreatePageCommand,
    UpdatePageCommand,
    DeletePageCommand,
    GetUserJournalEntriesCommand,
    GetUserPagesCommand
)


def index(request):
    return render(request, 'journals/index.html')


def model_to_dict(instance):
    """Convert model instance to dictionary"""
    data = {
        'id': str(instance.uuid),
        'created_at': instance.created_at.isoformat(),
        'modified_at': instance.modified_at.isoformat(),
    }
    
    if hasattr(instance, 'user'):
        data['user_id'] = str(instance.user.uuid)
    
    if hasattr(instance, 'date'):
        data['date'] = instance.date.isoformat()
    
    if hasattr(instance, 'content'):
        data['content'] = instance.content
    
    if hasattr(instance, 'title'):
        data['title'] = instance.title
    
    if hasattr(instance, 'slug'):
        data['slug'] = instance.slug
    
    if hasattr(instance, 'is_published'):
        data['is_published'] = instance.is_published
    
    # Add tags
    if hasattr(instance, 'get_tags'):
        data['tags'] = [{'name': tag.name, 'color': tag.color} for tag in instance.get_tags()]
    
    return data


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_or_update_journal_entry(request):
    """API endpoint to create or update journal entry"""
    try:
        data = request.data
        form = CreateOrUpdateJournalEntryForm(data)
        
        if form.is_valid():
            command = CreateOrUpdateJournalEntryCommand(form, request.user)
            entry = command.execute()
            return Response({
                'success': True,
                'data': model_to_dict(entry)
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_journal_entry(request):
    """API endpoint to get journal entry"""
    try:
        data = request.query_params
        form = GetJournalEntryForm(data)
        
        if form.is_valid():
            command = GetJournalEntryCommand(form, request.user)
            entry = command.execute()
            if entry:
                return Response({
                    'success': True,
                    'data': model_to_dict(entry)
                })
            else:
                return Response({
                    'success': True,
                    'data': None
                })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_journal_entries(request):
    """API endpoint to get user's journal entries"""
    try:
        data = request.query_params
        form = GetUserJournalEntriesForm(data)
        
        if form.is_valid():
            command = GetUserJournalEntriesCommand(form, request.user)
            result = command.execute()
            return Response({
                'success': True,
                'data': {
                    'entries': [model_to_dict(entry) for entry in result['entries']],
                    'total_count': result['total_count'],
                    'has_more': result['has_more']
                }
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_page(request):
    """API endpoint to create page"""
    try:
        data = request.data
        form = CreatePageForm(data, request.user)
        
        if form.is_valid():
            command = CreatePageCommand(form, request.user)
            page = command.execute()
            return Response({
                'success': True,
                'data': model_to_dict(page)
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_page(request):
    """API endpoint to update page"""
    try:
        data = request.data
        form = UpdatePageForm(data, request.user)
        
        if form.is_valid():
            command = UpdatePageCommand(form, request.user)
            page = command.execute()
            return Response({
                'success': True,
                'data': model_to_dict(page)
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_page(request):
    """API endpoint to delete page"""
    try:
        data = request.data
        form = DeletePageForm(data, request.user)
        
        if form.is_valid():
            command = DeletePageCommand(form, request.user)
            result = command.execute()
            return Response({
                'success': True,
                'data': {'deleted': result}
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pages(request):
    """API endpoint to get user's pages"""
    try:
        data = request.query_params
        form = GetUserPagesForm(data)
        
        if form.is_valid():
            command = GetUserPagesCommand(form, request.user)
            result = command.execute()
            return Response({
                'success': True,
                'data': {
                    'pages': [model_to_dict(page) for page in result['pages']],
                    'total_count': result['total_count'],
                    'has_more': result['has_more']
                }
            })
        else:
            return Response({
                'success': False,
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'non_field_errors': [str(e)]}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
