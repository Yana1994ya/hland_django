from django.contrib import admin
from market_review import models

# Register your models here.
admin.site.register(models.Application)
admin.site.register(models.NotableFeature)
admin.site.register(models.MissingFeature)