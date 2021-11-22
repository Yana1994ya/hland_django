# Register your models here.
from django.contrib import admin

from attractions2.models import Attraction, Suitability


class SuitabilityAdmin(admin.ModelAdmin):
    list_display = ("name", "museum", "winery", "zoo")
    list_filter = ("museum", "winery", "zoo")


admin.site.register(Suitability, SuitabilityAdmin)


class AttractionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Attraction, AttractionAdmin)
