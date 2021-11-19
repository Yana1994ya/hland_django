# Register your models here.
from django.contrib import admin

from attractions2.models import Suitability


class SuitabilityAdmin(admin.ModelAdmin):
    list_display = ("name", "museum", "winery")
    list_filter = ("museum", "winery")


admin.site.register(Suitability, SuitabilityAdmin)
