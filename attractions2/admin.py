# Register your models here.
from django.contrib import admin

from attractions2.models import Attraction


class AttractionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Attraction, AttractionAdmin)
