import re
from typing import List, Type

from django.db import models
from django.utils.translation import gettext_lazy as _

from attractions2.base_models import Attraction, AttractionFilter, ImageAsset, GoogleUser, ManagedAttraction


class MuseumDomain(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "museum_domains"


class Museum(ManagedAttraction):
    domain = models.ForeignKey(MuseumDomain, on_delete=models.CASCADE)

    @property
    def to_short_json(self):
        result = super().to_short_json

        result.update({
            "domain": self.domain.to_json
        })

        return result

    @classmethod
    def short_related(cls) -> List[str]:
        return super().short_related() + ["domain"]

    @classmethod
    def api_multiple_key(cls) -> str:
        return "museums"

    @classmethod
    def api_single_key(cls) -> str:
        return "museum"

    @classmethod
    def explore_filter(cls, qset, request):
        # https://hollyland.iywebs.cloudns.ph/attractions/api/museums?region_id=4&domain_id=1
        qset = super().explore_filter(qset, request)

        if "domain_id" in request.GET:
            qset = qset.filter(domain_id__in=list(map(
                int,
                request.GET.getlist("domain_id"),
            )))

        return qset


class Winery(ManagedAttraction):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "wineries"

    @classmethod
    def api_single_key(cls) -> str:
        return "winery"


class Zoo(ManagedAttraction):
    @classmethod
    def api_single_key(cls) -> str:
        return "zoo"

    @classmethod
    def api_multiple_key(cls) -> str:
        return "zoos"


class OffRoadTripType(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "trip_types"

    @classmethod
    def api_single_key(cls) -> str:
        return "trip_type"

    class Meta:
        verbose_name_plural = "Off-Road Trip Types"


class OffRoad(ManagedAttraction):
    trip_type = models.ForeignKey(OffRoadTripType, on_delete=models.CASCADE)

    @classmethod
    def api_multiple_key(cls) -> str:
        return "offroad"

    @classmethod
    def api_single_key(cls) -> str:
        return "offroad"

    @classmethod
    def short_related(cls) -> List[str]:
        return super().short_related() + ["trip_type"]

    @property
    def to_short_json(self):
        result = super().to_short_json

        result.update({
            "trip_type": self.trip_type.to_json
        })

        return result

    @classmethod
    def explore_filter(cls, qset, request):
        qset = super().explore_filter(qset, request)

        if "trip_type_id" in request.GET:
            qset = qset.filter(trip_type_id__in=list(map(
                int,
                request.GET.getlist("trip_type_id"),
            )))

        return qset


class WaterSportsAttractionType(AttractionFilter):
    @classmethod
    def api_single_key(cls) -> str:
        return "water_sports_attraction_type"

    @classmethod
    def api_multiple_key(cls) -> str:
        return "water_sports_attraction_types"


class WaterSports(ManagedAttraction):
    attraction_type = models.ForeignKey(WaterSportsAttractionType, on_delete=models.CASCADE)

    @classmethod
    def api_multiple_key(cls) -> str:
        return "water_sports"

    @classmethod
    def api_single_key(cls) -> str:
        return "water_sports"

    @classmethod
    def short_related(cls) -> List[str]:
        return super().short_related() + ["attraction_type"]

    @property
    def to_short_json(self):
        result = super().to_short_json

        result.update({
            "attraction_type": self.attraction_type.to_json
        })

        return result

    @classmethod
    def explore_filter(cls, qset, request):
        qset = super().explore_filter(qset, request)

        if "attraction_type_id" in request.GET:
            qset = qset.filter(attraction_type_id__in=list(map(
                int,
                request.GET.getlist("attraction_type_id"),
            )))

        return qset


class RockClimbingType(AttractionFilter):
    @classmethod
    def api_single_key(cls) -> str:
        return "rock_climbing_type"

    @classmethod
    def api_multiple_key(cls) -> str:
        return "rock_climbing_types"


class RockClimbing(ManagedAttraction):
    attraction_type = models.ForeignKey(RockClimbingType, on_delete=models.CASCADE)

    @classmethod
    def api_multiple_key(cls) -> str:
        return "rock_climbing"

    @classmethod
    def api_single_key(cls) -> str:
        return "rock_climbing"

    @classmethod
    def short_related(cls) -> List[str]:
        return super().short_related() + ["attraction_type"]

    @property
    def to_short_json(self):
        result = super().to_short_json

        result.update({
            "attraction_type": self.attraction_type.to_json
        })

        return result

    @classmethod
    def explore_filter(cls, qset, request):
        qset = super().explore_filter(qset, request)

        if "attraction_type_id" in request.GET:
            qset = qset.filter(attraction_type_id__in=list(map(
                int,
                request.GET.getlist("attraction_type_id"),
            )))

        return qset


class TrailDifficulty(models.TextChoices):
    EASY = "E", _("Easy")
    NORMAL = "N", _("Normal")
    HARD = "H", _("Hard")


class TrailSuitability(AttractionFilter):

    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_suitabilities"

    @classmethod
    def api_single_key(cls) -> str:
        return "trail_suitability"

    class Meta:
        verbose_name_plural = "Trail Suitabilities"


class TrailAttraction(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_attractions"

    @classmethod
    def api_single_key(cls) -> str:
        return "trail_attraction"

    class Meta:
        verbose_name_plural = "Trail Attractions"


class TrailActivity(AttractionFilter):

    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_activities"

    @classmethod
    def api_single_key(cls) -> str:
        return "trail_activity"

    class Meta:
        verbose_name_plural = "Trail Activities"


class Trail(models.Model):
    id = models.UUIDField(primary_key=True)

    @classmethod
    def api_multiple_key(cls) -> str:
        return "trails"

    @classmethod
    def api_single_key(cls) -> str:
        return "trail"

    difficulty = models.CharField(
        max_length=1,
        choices=TrailDifficulty.choices
    )

    # In meters
    length = models.PositiveIntegerField()
    elv_gain = models.PositiveIntegerField()

    name = models.CharField(max_length=250)
    lat = models.FloatField()
    long = models.FloatField()

    owner = models.ForeignKey(
        'GoogleUser',
        on_delete=models.CASCADE
    )

    main_image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    additional_images = models.ManyToManyField(
        ImageAsset,
        related_name="trail_additional_image"
    )

    suitabilities = models.ManyToManyField(
        TrailSuitability,
        related_name="suitable_trails"
    )

    attractions = models.ManyToManyField(
        TrailAttraction,
        related_name="trails_with_attraction"
    )

    activities = models.ManyToManyField(
        TrailActivity,
        related_name="trails_with_activity"
    )

    date_modified = models.DateTimeField(auto_now=True)

    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    @property
    def to_short_json(self):
        json_result = {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "long": self.long,
            "type": self.api_single_key(),
            "difficulty": self.difficulty,
            "length": self.length,
            "elevation_gain": self.elv_gain,
            "owner_id": str(self.owner_id),
            "avg_rating": str(self.avg_rating),
            "rating_count": self.rating_count
        }

        if self.main_image is None:
            json_result["main_image"] = None
        else:
            json_result["main_image"] = self.main_image.thumb_600().to_json

        return json_result


class History(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    # When the user first visited an attraction
    created = models.DateTimeField()
    # When the user last visited an attraction
    last_visited = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-last_visited']),
        ]

        unique_together = [('user', 'attraction')]


class TrailHistory(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    trail = models.ForeignKey(Trail, on_delete=models.CASCADE)
    # When the user first visited an attraction
    created = models.DateTimeField()
    # When the user last visited an attraction
    last_visited = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-last_visited']),
        ]

        unique_together = [('user', 'trail')]


class Favorite(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    created = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created']),
        ]

        unique_together = [('user', 'attraction')]


class TrailFavorite(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    trail = models.ForeignKey(Trail, on_delete=models.CASCADE)
    created = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created']),
        ]

        unique_together = [('user', 'trail')]


class UserImage(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    image = models.ForeignKey(ImageAsset, on_delete=models.CASCADE)


class TrailComment(models.Model):
    trail = models.ForeignKey(Trail, on_delete=models.CASCADE)
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)

    text = models.TextField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField()

    images = models.ManyToManyField(
        ImageAsset,
        related_name="trail_comment_image"
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['trail', '-created']),
        ]

    @property
    def to_json(self):
        return {
            "user": self.user.to_json,
            "rating": self.rating,
            "text": self.text,
            "created": self.created.isoformat("T")
        }

    @property
    def user_name(self) -> str:
        return self.user.name


def get_attraction_classes():
    for subclass in Attraction.__subclasses__() + ManagedAttraction.__subclasses__():
        if not subclass == ManagedAttraction:
            yield subclass


def _generate_regex() -> str:
    parts = []
    for subclass in get_attraction_classes():
        parts.append(re.escape(subclass.api_multiple_key()))

    return "|".join(parts)


class AttractionModelConverter:
    regex = _generate_regex()

    def to_python(self, value: str) -> Type[Attraction]:
        for subclass in get_attraction_classes():
            if value == subclass.api_multiple_key():
                return subclass

    def to_url(self, value: Type[Attraction]):
        return value.api_multiple_key()
