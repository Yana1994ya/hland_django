from django.urls import path

from attractions2 import api_views, models, views


def get_api_urls_for(model, edit_view):
    multi = model.api_multiple_key()
    single = model.api_single_key()

    return [
        path(f"api/{multi}", api_views.get_explore, {"model": model}),
        path(
            f"api/{multi}/<int:attraction_id>",
            api_views.get_single,
            {"model": model}
        ),
        path(
            f"api/history/{multi}",
            api_views.history_list,
            {"model": model}
        ),
        path(
            f"api/favorites/{multi}",
            api_views.favorites_list,
            {"model": model}
        ),
        path(f"add_{single}", edit_view, {f"{single}_id": None},
             name=f"add_{single}"),
        path(f"edit_{single}/<int:{single}_id>", edit_view,
             name=f"edit_{single}"),
        path(f"{multi}", views.display, {"page_number": 1, "model": model}, name=multi),
        path(f"{multi}/page<int:page_number>", views.display, {"model": model}, name=multi),
    ]


urlpatterns = [
                  path("", views.homepage, name="attractions_homepage"),
                  path("api/regions", api_views.get_regions),
                  path("api/museum_domains", api_views.get_museum_domains),
                  path("api/off_road_trip_types", api_views.get_off_road_trip_types),
                  path("api/visit", api_views.visit),
                  path("api/history", api_views.history),
                  path("api/history/delete", api_views.delete_history),
                  path("api/favorite", api_views.favorite),
                  path("api/favorites", api_views.favorites),
                  path("api/login", api_views.login),
                  path("api/map", api_views.map_attractions),
                  path("api/trail/<uuid:trail_id>", api_views.get_trail),
                  path("api/trail/upload", api_views.upload_start),
                  path("api/trails", api_views.get_trails),
              ] + \
              get_api_urls_for(models.Museum, views.EditMuseum.as_view()) + \
              get_api_urls_for(models.Winery, views.EditWinery.as_view()) + \
              get_api_urls_for(models.Zoo, views.EditZoo.as_view()) + \
              get_api_urls_for(models.OffRoad, views.EditOffRoad.as_view())
