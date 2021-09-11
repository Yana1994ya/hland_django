from django.db import models

# Create your models here.
from market_review.models import ImageAsset


class Category(models.Model):
    # app visible properties
    name = models.CharField(max_length=250)
    image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # background properties
    parent = models.ForeignKey(
        'attractions.Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    exclusive = models.BooleanField(default=False)

    def __str__(self):
        return self.name

