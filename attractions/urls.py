from django.urls import path

from attractions import views
urlpatterns = [
    path('category/<int:category_id>/image', views.category_image, name="category_image"),
    path('<int:attraction_id>/image', views.attraction_image, name="attraction_image"),
    path('category/root.json', views.list_categories,  {"parent_id": None}),
    path('category/<int:parent_id>.json', views.list_categories),
    path('category/<int:category_id>.attractions.json', views.list_attractions),
]
