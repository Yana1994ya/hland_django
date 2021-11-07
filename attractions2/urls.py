from django.urls import path

from attractions2 import views

urlpatterns = [
    path("add_museum", views.EditMuseum.as_view(), {"museum_id": None}, name="add_museum"),
    path("edit_museum/<int:museum_id>", views.EditMuseum.as_view(), name="edit_museum"),
    path("museums", views.museums, {"page_number": 1}, name="museums"),
    path("museums/page<int:page_number>", views.museums, name="museums"),

]
