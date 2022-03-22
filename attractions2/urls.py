from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path, register_converter

from attractions2 import api_views, views
from attractions2.models import AttractionModelConverter


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
        path(f"add_{single}", staff_member_required(edit_view), {f"{single}_id": None},
             name=f"add_{single}"),
        path(f"edit_{single}/<int:{single}_id>", staff_member_required(edit_view),
             name=f"edit_{single}"),
        path(f"{multi}", views.display, {"page_number": 1, "model": model}, name=multi),
        path(f"{multi}/page<int:page_number>", views.display, {"model": model}, name=multi),
    ]


# urlpatterns = [
#                   path("", views.homepage, name="attractions_homepage"),
#                   path("api/regions", api_views.get_regions),
#                   path("api/museum_domains", api_views.get_attraction_filter, {"model": models.MuseumDomain}),
#                   path("api/off_road_trip_types", api_views.get_attraction_filter, {"model": models.OffRoadTripType}),
#                   path("api/water_sport_types", api_views.get_attraction_filter, {"model": models.WaterSportsAttractionType}),
#                   path("api/rock_climbing_types", api_views.get_attraction_filter, {"model": models.RockClimbingType}),
#                   path("api/visit", api_views.visit),
#                   path("api/visit/trail", api_views.visit_trail),
#                   path("api/history", api_views.history),
#                   path("api/history/trails", api_views.history_trails),
#                   path("api/history/delete", api_views.delete_history),
#                   path("api/favorite", api_views.favorite),
#                   path("api/favorite/trail", api_views.favorite_trail),
#                   path("api/favorites", api_views.favorites),
#                   path("api/favorites/trails", api_views.favorites_trails),
#                   path("api/login", api_views.login),
#                   path("api/map", api_views.map_attractions),
#                   path("api/trail/<uuid:trail_id>", api_views.get_trail),
#                   path("api/trail/upload", api_views.upload_start),
#                   path("api/trails", api_views.get_trails),
#                   path("api/trails/suitabilities", api_views.get_attraction_filter, {"model": models.TrailSuitability}),
#                   path("api/trails/attractions", api_views.get_attraction_filter, {"model": models.TrailAttraction}),
#                   path("api/trails/activities", api_views.get_attraction_filter, {"model": models.TrailActivity}),
#                   path("api/upload_image", api_views.upload_image),
#                   # attraction comment
#                   path("api/comments/attraction", api_views.add_comment),
#                   path("api/comments/attraction/<int:attraction_id>/<int:page_number>",
#                        api_views.get_attraction_comments),
#                   # trail comment
#                   path("api/comments/trail", api_views.add_trail_comment),
#                   path("api/comments/trail/<str:trail_id>/<int:page_number>", api_views.get_trail_comments),
#
#                   path(f"trails", views.display, {"page_number": 1, "model": models.Trail}, name="trail"),
#                   path(f"trails/page<int:page_number>", views.display, {"model": models.Trail}, name="trail"),
#                   path(f"trail/<uuid:trail_id>", views.edit_trail, name="edit_trail"),
#                   path(f"trail/<uuid:trail_id>/upload", views.trail_upload, name="trail_upload"),
#                   path(f"<int:attraction_id>/upload", views.attraction_upload, name="attraction_upload"),
#                   path(f"trail", views.edit_trail, name="add_trail"),
#               ] + \
#               get_api_urls_for(models.Museum, views.EditMuseum.as_view()) + \
#               get_api_urls_for(models.Winery, views.EditWinery.as_view()) + \
#               get_api_urls_for(models.Zoo, views.EditZoo.as_view()) + \
#               get_api_urls_for(models.OffRoad, views.EditOffRoad.as_view()) + \
#               get_api_urls_for(models.WaterSports, views.EditWaterSports.as_view()) + \
#               get_api_urls_for(models.RockClimbing, views.EditRockClimbing.as_view())

register_converter(AttractionModelConverter, "model")

urlpatterns = [
    path("api/<model:model>", api_views.get_explore),
    path("api/<model:model>/<int:attraction_id>", api_views.get_single),
    path("api/login", api_views.login),
    path("api/history", api_views.history),
    path("api/history/<model:model>", api_views.history_list),
    path("api/history/delete", api_views.delete_history),
    path("api/favorite", api_views.favorite),
    path("api/favorites", api_views.favorites),
    path("api/favorites/<model:model>", api_views.favorites_list),
    path("api/visit", api_views.visit),
]
