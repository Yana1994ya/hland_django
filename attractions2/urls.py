from django.urls import path

from attractions2 import api_views, models, views


def get_api_urls_for(model):
    return [
        path("api/" + model.api_multiple_key(), api_views.get_explore, {"model": model}),
        path(
            "api/" + model.api_multiple_key() + "/<int:attraction_id>",
            api_views.get_single,
            {"model": model}
        ),
        path(
            "api/history/" + model.api_multiple_key(),
            api_views.history_list,
            {"model": model}
        ),
        path(
            "api/favorites/" + model.api_multiple_key(),
            api_views.favorites_list,
            {"model": models.Museum}
        ),
    ]


urlpatterns = [
                  path("", views.homepage, name="homepage"),
                  path("add_museum", views.EditMuseum.as_view(), {"museum_id": None},
                       name="add_museum"),
                  path("edit_museum/<int:museum_id>", views.EditMuseum.as_view(),
                       name="edit_museum"),
                  path("museums", views.museums, {"page_number": 1}, name="museums"),
                  path("museums/page<int:page_number>", views.museums, name="museums"),
                  path("add_winery", views.EditWinery.as_view(), {"winery_id": None},
                       name="add_winery"),
                  path("edit_winery/<int:winery_id>", views.EditWinery.as_view(),
                       name="edit_winery"),
                  path("wineries", views.wineries, {"page_number": 1}, name="wineries"),
                  path("wineries/page<int:page_number>", views.wineries, name="wineries"),
                  path("api/regions", api_views.get_regions),
                  path("api/museum_domains", api_views.get_museum_domains),
                  path("api/visit", api_views.visit),
                  path("api/history", api_views.history),
                  path("api/history/delete", api_views.delete_history),
                  path("api/favorite", api_views.favorite),
                  path("api/favorites", api_views.favorites),
                  path("api/login", api_views.login),
              ] + get_api_urls_for(models.Museum) + get_api_urls_for(models.Winery)
