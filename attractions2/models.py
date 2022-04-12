import re
from typing import List, Type, Union, Optional

from django.conf import settings
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
    def explore_filter(cls, query_set, request):
        # https://hollyland.iywebs.cloudns.ph/attractions/api/museums?region_id=4&domain_id=1
        query_set = super().explore_filter(query_set, request)

        if "domain_id" in request.GET:
            query_set = query_set.filter(domain_id__in=list(map(
                int,
                request.GET.getlist("domain_id"),
            )))

        return query_set


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
        return "offroad_trip_types"

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
    def explore_filter(cls, query_set, request):
        query_set = super().explore_filter(query_set, request)

        if "trip_type_id" in request.GET:
            query_set = query_set.filter(trip_type_id__in=list(map(
                int,
                request.GET.getlist("trip_type_id"),
            )))

        return query_set


class WaterSportsAttractionType(AttractionFilter):
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
    def explore_filter(cls, query_set, request):
        query_set = super().explore_filter(query_set, request)

        if "attraction_type_id" in request.GET:
            query_set = query_set.filter(attraction_type_id__in=list(map(
                int,
                request.GET.getlist("attraction_type_id"),
            )))

        return query_set


class RockClimbingType(AttractionFilter):
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
    def explore_filter(cls, query_set, request):
        query_set = super().explore_filter(query_set, request)

        if "attraction_type_id" in request.GET:
            query_set = query_set.filter(attraction_type_id__in=list(map(
                int,
                request.GET.getlist("attraction_type_id"),
            )))

        return query_set


class ExtremeSportsType(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "extreme_sports_types"


class ExtremeSports(ManagedAttraction):
    sport_type = models.ForeignKey(ExtremeSportsType, on_delete=models.CASCADE)

    @classmethod
    def api_multiple_key(cls) -> str:
        return "extreme_sports"

    @classmethod
    def api_single_key(cls) -> str:
        return "extreme_sports"

    @classmethod
    def short_related(cls) -> List[str]:
        return super().short_related() + ["sport_type"]

    @property
    def to_short_json(self):
        result = super().to_short_json

        result.update({
            "sport_type": self.sport_type.to_json
        })

        return result

    @classmethod
    def explore_filter(cls, query_set, request):
        query_set = super().explore_filter(query_set, request)

        if "sport_type_id" in request.GET:
            query_set = query_set.filter(sport_type_id__in=list(map(
                int,
                request.GET.getlist("sport_type_id"),
            )))

        return query_set


class HotAir(ManagedAttraction):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "hot_air"

    @classmethod
    def api_single_key(cls) -> str:
        return "hot_air"


class TrailDifficulty(models.TextChoices):
    EASY = "E", _("Easy")
    NORMAL = "N", _("Normal")
    HARD = "H", _("Hard")


class TrailSuitability(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_suitabilities"

    class Meta:
        verbose_name_plural = "Trail Suitabilities"


class TrailAttraction(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_attractions"

    class Meta:
        verbose_name_plural = "Trail Attractions"


class TrailActivity(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "trail_activities"

    class Meta:
        verbose_name_plural = "Trail Activities"


class Trail(Attraction):
    @classmethod
    def short_related(cls) -> List[str]:
        return []

    @classmethod
    def explore_filter(cls, query_set, request):
        if "length_start" in request.GET:
            query_set = query_set.filter(length__gte=int(request.GET["length_start"]))

        if "length_end" in request.GET:
            query_set = query_set.filter(length__lte=int(request.GET["length_end"]))

        if "elevation_gain_start" in request.GET:
            query_set = query_set.filter(elv_gain__gte=int(request.GET["elevation_gain_start"]))

        if "elevation_gain_end" in request.GET:
            query_set = query_set.filter(elv_gain__lte=int(request.GET["elevation_gain_end"]))

        if "difficulty" in request.GET:
            query_set = query_set.filter(difficulty__in=request.GET.getlist("difficulty"))

        if "activities" in request.GET:
            query_set = query_set.filter(activities__pk__in=request.GET.getlist("activities"))

        if "attractions" in request.GET:
            query_set = query_set.filter(attractions__pk__in=request.GET.getlist("attractions"))

        if "suitabilities" in request.GET:
            query_set = query_set.filter(suitabilities__pk__in=request.GET.getlist("suitabilities"))

        # For map
        if "lon_min" in request.GET:
            query_set = query_set.filter(long__gte=float(request.GET["lon_min"]))

        if "lon_max" in request.GET:
            query_set = query_set.filter(long__lte=float(request.GET["lon_max"]))

        if "lat_min" in request.GET:
            query_set = query_set.filter(lat__gte=float(request.GET["lat_min"]))

        if "lat_max" in request.GET:
            query_set = query_set.filter(lat__lte=float(request.GET["lat_max"]))

        return query_set

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

    owner = models.ForeignKey(
        'GoogleUser',
        on_delete=models.CASCADE
    )

    suitabilities = models.ManyToManyField(
        TrailSuitability,
        related_name="suitable_trails",
        blank=True
    )

    attractions = models.ManyToManyField(
        TrailAttraction,
        related_name="trails_with_attraction",
        blank=True
    )

    activities = models.ManyToManyField(
        TrailActivity,
        related_name="trails_with_activity",
        blank=True
    )

    @property
    def to_short_json(self):
        json_result = super(Trail, self).to_short_json

        json_result.update({
            "difficulty": self.difficulty,
            "length": self.length,
            "elevation_gain": self.elv_gain,
            "owner_id": str(self.owner_id),
        })

        return json_result

    @property
    def to_json(self):
        document = self.to_short_json

        document["suitabilities"] = list(map(
            lambda x: x.to_json,
            self.suitabilities.all()
        ))

        document["attractions"] = list(map(
            lambda x: x.to_json,
            self.attractions.all()
        ))

        document["activities"] = list(map(
            lambda x: x.to_json,
            self.activities.all()
        ))

        document["owner"] = self.owner.to_json

        cdn = settings.ASSETS.get("cdn")
        bucket = settings.ASSETS["bucket"]
        prefix = settings.ASSETS["prefix"]

        if cdn is not None:
            document["points"] = f"https://{cdn}/{prefix}trails/{self.id}.csv.gz"
        else:
            document["points"] = f"https://{bucket}.s3.amazonaws.com/{prefix}trails/{self.id}.csv.gz"

        return document


class Package(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "packages"


class TourDestination(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "tour_destinations"


class TourLanguage(AttractionFilter):
    @classmethod
    def api_multiple_key(cls) -> str:
        return "tour_languages"


def filter_to_json(instance: Optional[AttractionFilter]) -> Optional[dict]:
    if instance is None:
        return None
    else:
        return instance.to_json


class Tour(Attraction):
    @classmethod
    def short_related(cls) -> List[str]:
        return [
            "package",
            "language"
        ]

    @classmethod
    def api_multiple_key(cls) -> str:
        return "tours"

    @classmethod
    def api_single_key(cls) -> str:
        return "tour"

    @classmethod
    def explore_filter(cls, query_set, request):
        # For each of the related fields(which a plenty), filter the field name
        # for example tour_type_id, with the filter tour_type_id__in = {ids from get}
        for related in cls.short_related():
            id_field = related + "_id"

            if id_field in request.GET:
                query_set = query_set.filter(**{
                    id_field + "__in": list(map(
                        int,
                        request.GET.getlist(id_field),
                    ))
                })

        if "destination_id" in request.GET:
            query_set = query_set.filter(destinations__id__in=list(map(
                int,
                request.GET.getlist("destination_id"),
            )))

        return query_set

    @property
    def to_short_json(self):
        data = super(Tour, self).to_short_json

        # Add all the related fields
        for related in self.short_related():
            data[related] = filter_to_json(getattr(self, related))

        data.update({
            "length": str(self.tour_length),
            "price": str(self.price),
            "group": self.group,
        })

        return data

    @property
    def to_json(self):
        data = self.to_short_json

        data.update({
            "description": self.description,
            "destinations": list(map(
                lambda destination: destination.to_json,
                self.destinations.all()
            ))
        })

        return data

    @classmethod
    def short_query(cls):
        return cls.objects \
            .defer("description") \
            .select_related(*cls.short_related())

    @classmethod
    def short_related(cls) -> List[str]:
        return ["package", "language"]

    destinations = models.ManyToManyField(
        TourDestination
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    price = models.DecimalField(
        max_digits=9,
        decimal_places=2
    )

    language = models.ForeignKey(
        TourLanguage,
        on_delete=models.CASCADE
    )

    tour_length = models.DecimalField(
        max_digits=5,
        decimal_places=1
    )

    description = models.TextField()
    group = models.BooleanField(default=False, blank=True)


class TourAvailability(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    day = models.DateField()

    class Meta:
        unique_together = [("tour", "day")]


class TourReservation(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    day = models.DateField()
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    payment_confirmation_id = models.CharField(max_length=50)


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

    @staticmethod
    def to_python(value: str) -> Type[Attraction]:
        for subclass in get_attraction_classes():
            if value == subclass.api_multiple_key():
                return subclass

    @staticmethod
    def to_url(value: Union[str, Type[Attraction]]):
        if isinstance(value, str):
            return value
        return value.api_multiple_key()


def _generate_filter_regex() -> str:
    parts = []
    for subclass in AttractionFilter.__subclasses__():
        parts.append(re.escape(subclass.api_multiple_key()))

    return "|".join(parts)


class FilterModelConverter:
    regex = _generate_filter_regex()

    @staticmethod
    def to_python(value: str) -> Type[AttractionFilter]:
        for subclass in AttractionFilter.__subclasses__():
            if value == subclass.api_multiple_key():
                return subclass

    @staticmethod
    def to_url(value: Type[Attraction]):
        return value.api_multiple_key()
