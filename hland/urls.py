"""hland URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from hland.views import homepage
from django.conf import settings

urlpatterns = [
    path('', homepage, name="homepage"),
    path('market_review/', include('market_review.urls')),
    path('attractions/', include('attractions.urls')),
    path('10bis/', include('tenbis.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    from debug_toolbar import urls
    urlpatterns.append(path('__debug__/', include(urls)))
