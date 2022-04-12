# Register your models here.

from django.contrib import admin

from attractions2 import models, base_models


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


class WaterSportAttractionTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.WaterSportsAttractionType, WaterSportAttractionTypeAdmin)


class RockClimbingTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.RockClimbingType, RockClimbingTypeAdmin)


class TrailAdmin(admin.ModelAdmin):
    list_display = ["name", "elv_gain", "length", "difficulty"]


admin.site.register(models.Trail, TrailAdmin)


class CommentsAdmin(admin.ModelAdmin):
    list_display = ["user_name", "text"]
    list_select_related = ["user"]


admin.site.register(base_models.AttractionComment, CommentsAdmin)


class ExtremeSportsTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.ExtremeSportsType, ExtremeSportsTypeAdmin)


class GoogleUserAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.GoogleUser, GoogleUserAdmin)


class PackageAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Package, PackageAdmin)


class TourDestinationAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TourDestination, TourDestinationAdmin)


class TourLanguageAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TourLanguage, TourLanguageAdmin)
