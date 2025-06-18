from django.urls import path
from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/pages/", views.create_page, name="create_page"),
    path("api/pages/update/", views.update_page, name="update_page"),
    path("api/pages/delete/", views.delete_page, name="delete_page"),
    path("api/pages/list/", views.get_pages, name="list_pages"),
    # Block-centric API endpoints
    path("api/page/", views.get_page_with_blocks, name="get_page_with_blocks"),
    path("api/blocks/", views.create_block, name="create_block"),
    path("api/blocks/update/", views.update_block, name="update_block"),
    path("api/blocks/delete/", views.delete_block, name="delete_block"),
    path("api/blocks/toggle-todo/", views.toggle_block_todo, name="toggle_block_todo"),
]
