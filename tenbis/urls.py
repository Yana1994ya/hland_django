from django.urls import path

from tenbis import views

urlpatterns = [
    path('', views.homepage, name="tenbis"),
    path('print/<str:token>', views.show_print, name="tenbis_print"),
    path('used/<int:coupon_id>', views.mark_used, name="tenbis_used_coupon"),
]
