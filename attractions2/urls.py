from django.urls import path, register_converter

from attractions2 import api_views, views
from attractions2.models import AttractionModelConverter, FilterModelConverter

register_converter(AttractionModelConverter, "model")
register_converter(FilterModelConverter, "filter")

urlpatterns = [
                  path("", views.homepage, name="attractions_homepage"),
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
                  path("api/comments/attraction", api_views.add_comment),
                  path("api/comments/attraction/<int:attraction_id>/<int:page_number>", api_views.get_comments),
                  path("api/<filter:model>", api_views.get_attraction_filter),
                  path("api/trail/upload", api_views.upload_start),
                  path("api/upload_image", api_views.upload_image),
                  path("api/map", api_views.map_attractions),
                  path("api/search", api_views.search),
                  path("api/tours/availability/<int:tour_id>/<int:year>/<int:month>", api_views.availability),
                  path("api/tours/available/<int:tour_id>/<int:year>/<int:month>", api_views.available),
                  path("api/tours/reserve", api_views.tour_reserve),
                  path("api/tours/reservations", api_views.tour_reservations),
                  # Admin display views
                  path("<model:model>", views.display, {"page_number": 1}, name="display"),
                  path("<model:model>/page<int:page_number>", views.display, name="display"),
                  path("<int:attraction_id>/upload", views.attraction_upload, name="attraction_upload"),
              ] + views.EditMuseum.urls() + \
              views.EditWinery.urls() + \
              views.EditZoo.urls() + \
              views.EditOffRoad.urls() + \
              views.EditRockClimbing.urls() + \
              views.EditWaterSports.urls() + \
              views.EditTrail.urls() + \
              views.EditExtremeSports.urls() + \
              views.EditHotAir.urls() + \
              views.EditTour.urls()
