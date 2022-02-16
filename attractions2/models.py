from typing import List

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from attractions2.base_models import Attraction, AttractionFilter, ImageAsset


class MuseumDomain(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "museum_domains"

    @classmethod
    def api_single_key(cls) -> str:
        return "museum_domain"


class Museum(Attraction):
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


class Winery(Attraction):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "wineries"

    @classmethod
    def api_single_key(cls) -> str:
        return "winery"


class Zoo(Attraction):
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


class OffRoad(Attraction):
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
            "elevation_gain": self.elv_gain
        }

        if self.main_image is None:
            json_result["main_image"] = None
        else:
            json_result["main_image"] = self.main_image.thumb_600().to_json

        return json_result


class GoogleUser(models.Model):
    id = models.UUIDField(primary_key=True)
    # Identifier in google
    sub = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(blank=True, null=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    given_name = models.CharField(max_length=250, blank=True, null=True)
    family_name = models.CharField(max_length=250, blank=True, null=True)
    picture = models.CharField(max_length=250, blank=True, null=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Keep user anonymous by *not* updating name/given_name/email when logging in.
    anonymized = models.BooleanField()

    banned_until = models.DateTimeField(blank=True, null=True)

    @property
    def to_json(self):
        data = {
            "id": self.id,
            "name": self.name
        }

        if self.picture:
            data["picture"] = self.picture

        return data

    def __str__(self):
        return self.name


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


class Favorite(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    created = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created']),
        ]

        unique_together = [('user', 'attraction')]


class UserImage(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    image = models.ForeignKey(ImageAsset, on_delete=models.CASCADE)


class UserComment(models.Model):
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)
    content_type = models.ForeignKey(
        ContentType,
        editable=False,
        null=True,
        on_delete=models.SET_NULL
    )

    # Must be char field because it can either be UUID for trail or int for the rest
    content_id = models.CharField(max_length=50)
    text = models.TextField()

    images = models.ManyToManyField(
        ImageAsset,
        related_name="comment_images"
    )

    @property
    def to_json(self):
        return {
            "id": self.id,
            "text": self.text,
            "user": self.user.to_json
        }
