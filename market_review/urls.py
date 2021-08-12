from django.urls import path
from market_review import views

urlpatterns = [
    path('', views.home, name="market_review_home"),
    path('app/<str:app_id>', views.application_page, name="application"),
    path('app/<str:app_id>/logo', views.upload_logo, name="upload_logo"),
    path('app/<str:app_id>/features/<str:feature_slug>', views.feature_images, name="feature_images")
]
