from typing import NoReturn, Optional

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

    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Attraction(models.Model):
    name = models.CharField(max_length=250)

    main_image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    additional_images = models.ManyToManyField(
        ImageAsset,
        related_name="attraction_additional_image"
    )

    categories = models.ManyToManyField(Category)

    long = models.FloatField()
    lat = models.FloatField()

    @classmethod
    def qset_from_request(cls, request):
        query_set = cls.objects.all()

        for category_id in request.GET.getlist("category_id"):
            query_set = query_set.filter(categories__id=int(category_id))

        return query_set

    def get_category(self, parent_id: int) -> Optional[int]:
        try:
            return self.categories.get(parent_id=parent_id).id
        except Category.DoesNotExist:
            return None

    def set_category(self, parent_id: int, category_id: int) -> NoReturn:
        # check if attraction_type is correct
        found = False

        for type_category in self.categories.filter(parent_id=parent_id):
            if type_category.id != category_id:
                self.categories.remove(type_category)
            else:
                found = True

        if not found:
            self.categories.add(Category.objects.get(
                parent_id=parent_id,
                id=category_id
            ))

    def __str__(self):
        return self.name
