from django.urls import path

from attractions2 import api_views, views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("add_museum", views.EditMuseum.as_view(), {"museum_id": None}, name="add_museum"),
    path("edit_museum/<int:museum_id>", views.EditMuseum.as_view(), name="edit_museum"),
    path("museums", views.museums, {"page_number": 1}, name="museums"),
    path("museums/page<int:page_number>", views.museums, name="museums"),
    path("add_winery", views.EditWinery.as_view(), {"winery_id": None}, name="add_winery"),
    path("edit_winery/<int:winery_id>", views.EditWinery.as_view(), name="edit_winery"),
    path("wineries", views.wineries, {"page_number": 1}, name="wineries"),
    path("wineries/page<int:page_number>", views.wineries, name="wineries"),
    path("api/regions", api_views.get_regions),
    path("api/museum_domains", api_views.get_museum_domains),
    path("api/museums", api_views.get_museums),
    path("api/museums/<int:museum_id>", api_views.get_museum),
    path("api/wineries", api_views.get_wineries),
    path("api/wineries/<int:winery_id>", api_views.get_winery),
    path("api/visit", api_views.visit),
    path("api/history", api_views.history),
    path("api/history/delete", api_views.delete_history),
    path("api/history/museums", api_views.history_museums),
    path("api/history/wineries", api_views.history_wineries),
    path("api/favorite", api_views.favorite),
    path("api/favorites", api_views.favorites),
    path("api/favorites/museums", api_views.favorites_museums),
    path("api/favorites/wineries", api_views.favorites_wineries),
    path("api/login", api_views.login),
]
