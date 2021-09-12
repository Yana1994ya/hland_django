from django.contrib import admin
from attractions import models


# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_filter = ["parent"]
    list_display = ["name", "order"]
    ordering = ["order"]


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Attraction)
