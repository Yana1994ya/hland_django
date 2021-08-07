from django.urls import path
from market_review import views

urlpatterns = [
    path('app/<str:app_id>/logo', views.upload_logo, name="upload_logo")
]
