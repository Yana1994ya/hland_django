from django.urls import path

from tenbis import views

urlpatterns = [
    path('', views.homepage, name="tenbis")
]
