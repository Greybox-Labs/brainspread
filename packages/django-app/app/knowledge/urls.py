from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Legacy API endpoints
    path('api/entries/', views.create_or_update_journal_entry, name='create_or_update_entry'),
    path('api/entries/get/', views.get_journal_entry, name='get_entry'),
    path('api/entries/list/', views.get_journal_entries, name='list_entries'),
    
    path('api/pages/', views.create_page, name='create_page'),
    path('api/pages/update/', views.update_page, name='update_page'),
    path('api/pages/delete/', views.delete_page, name='delete_page'),
    path('api/pages/list/', views.get_pages, name='list_pages'),
    
    # New block-centric API endpoints
    path('api/page/', views.get_page_with_blocks, name='get_page_with_blocks'),
    path('api/blocks/', views.create_block, name='create_block'),
    path('api/blocks/update/', views.update_block, name='update_block'),
    path('api/blocks/delete/', views.delete_block, name='delete_block'),
    path('api/blocks/toggle-todo/', views.toggle_block_todo, name='toggle_block_todo'),
]