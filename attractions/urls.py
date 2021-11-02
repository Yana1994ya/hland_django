from django.urls import path

from attractions import views

urlpatterns = [
    path('', views.view_attractions, {"page_number": 1}, name="view_attractions"),
    path('page<int:page_number>', views.view_attractions, name="view_attractions"),
    path('category/<int:category_id>/image', views.category_image, name="category_image"),
    path('create', views.edit_attraction, {"attraction_id": None}, name="create_attraction"),
    path('<int:attraction_id>', views.edit_attraction, name="edit_attraction"),
    path('category/root.json', views.list_categories, {"parent_id": None}),
    path('category/<int:parent_id>.json', views.list_categories),
    path('attractions.json', views.fetch_attractions),
]
