# Register your models here.
from django.contrib import admin

from attractions2 import models


class AttractionAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Attraction, AttractionAdmin)


class OffRoadTripTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.OffRoadTripType, OffRoadTripTypeAdmin)


class TrailSuitabilityAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TrailSuitability, TrailSuitabilityAdmin)


class TrailAttractionAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TrailAttraction, TrailAttractionAdmin)


class TrailActivityAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TrailActivity, TrailActivityAdmin)
