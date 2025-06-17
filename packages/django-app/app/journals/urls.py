from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/entries/', views.create_or_update_journal_entry, name='create_or_update_entry'),
    path('api/entries/get/', views.get_journal_entry, name='get_entry'),
    path('api/entries/list/', views.get_journal_entries, name='list_entries'),
    
    path('api/pages/', views.create_page, name='create_page'),
    path('api/pages/update/', views.update_page, name='update_page'),
    path('api/pages/delete/', views.delete_page, name='delete_page'),
    path('api/pages/list/', views.get_pages, name='list_pages'),
]