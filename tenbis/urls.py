from django.urls import path

from tenbis import views

urlpatterns = [
    path('', views.homepage, name="tenbis"),
    path('multiple/<str:token>', views.show_multiple, name="tenbis_multiple"),
    path('multiple_print/<str:token>', views.print_multiple, name="tenbis_multiple_print"),
]
