import csv
import dataclasses
import gzip
import http.client
from datetime import datetime
import json
import time
import uuid
from math import radians, sin, cos, sqrt, atan2
from statistics import mean
from typing import Optional

import boto3
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import django.http.request
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
import jwt
import pytz

from attractions2 import models


def _get_regions_last_modified(request):
    return models.Region.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_regions_last_modified)
def get_regions(request):
    return JsonResponse({
        "status": "ok",
        "regions": list(map(
            lambda x: x.to_json,
            models.Region.objects.order_by("name")
        ))
    })


def _get_museum_domains_last_modified(request):
    return models.MuseumDomain.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_museum_domains_last_modified)
def get_museum_domains(request):
    return JsonResponse({
        "status": "ok",
        "domains": list(map(
            lambda x: x.to_json,
            models.MuseumDomain.objects.order_by("name")
        ))
    })


def _get_explore_qset(request, model, short: bool):
    if short:
        qset = model.short_query()
    else:
        qset = model.objects.all()

    return model.explore_filter(qset, request)


def _get_explore_last_modified(request, model):
    try:
        return _get_explore_qset(request, model, False).latest("date_modified").date_modified
    except model.DoesNotExist:
        return None


# cache explore for 2 hours
@cache_control(public=True, max_age=60 * 60 * 2)
@condition(last_modified_func=_get_explore_last_modified)
def get_explore(request, model):
    items = []

    for item in _get_explore_qset(request, model, True) \
            .order_by("name"):
        items.append(item.to_short_json)

    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): items
    })


def _get_single_last_modified(request, model, attraction_id: int):
    try:
        return model.objects.get(id=attraction_id).date_modified
    except model.DoesNotExist:
        return None


# cache single for 2 hours
@cache_control(public=True, max_age=60 * 60 * 2)
@condition(last_modified_func=_get_single_last_modified)
def get_single(request, model, attraction_id: int):
    try:
        return JsonResponse({
            "status": "ok",
            model.api_single_key(): model.objects.get(id=attraction_id).to_json
        })
    except model.DoesNotExist:
        resp = JsonResponse({
            "status": "error",
            "code": "NotFound",
            "message": "The requested " + model.api_single_key() + " doesn't exist"
        })
        resp.status_code = 404

        return resp


@csrf_exempt
def login(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    data = json.loads(request.body)
    token = data["token"]

    jwks_client = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    data = jwt.decode(
        token,
        signing_key.key,
        audience="1085250225192-bk570909cie3spgronk2dfu6rrv041jd.apps.googleusercontent.com",
        algorithms='RS256'
    )

    # Allow possibility of anonymized users by keying by a
    # hashed sub, rather than the original sub
    user_id = uuid.uuid5(settings.USER_ID_NAMESPACE, data["sub"])

    user, _created = models.GoogleUser.objects.get_or_create(id=user_id, defaults={
        # All users start as non anonymized
        "anonymized": False
    })

    # Only update details if user is not anonymized
    if not user.anonymized:
        user.sub = data["sub"]
        user.email = data.get("email")
        user.email_verified = data.get("email_verified")
        user.name = data["name"]
        user.given_name = data.get("given_name")
        user.family_name = data.get("family_name")
        user.picture = data.get("picture")

    # save in any case, to indicate a login
    user.save()

    return JsonResponse({
        "status": "ok",
        "token": jwt.encode(
            {
                "id": str(user.id),
                "exp": int(time.time()) + 60 * 60 * 24 * 7,
                "aud": settings.AUDIENCE
            },
            settings.SECRET_KEY,
            algorithm="HS256"
        )
    })


@dataclasses.dataclass(frozen=True)
class UserRequest:
    request: django.http.request.HttpRequest
    user_id: uuid.UUID
    data: dict


def with_user_id(fn):
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            return HttpResponse(status=405)

        data = json.loads(request.body)
        token = data["token"]

        user = jwt.decode(
            token,
            settings.SECRET_KEY,
            audience=settings.AUDIENCE,
            algorithms='HS256'
        )

        user_id = uuid.UUID(user["id"])

        return fn(UserRequest(
            request=request,
            user_id=user_id,
            data=data
        ), *args, **kwargs)

    return csrf_exempt(wrapped)


@with_user_id
def visit(request: UserRequest):
    attraction_id = int(request.data["id"])

    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    history_obj, created = models.History.objects.get_or_create(
        user_id=request.user_id,
        attraction=models.Attraction.objects.get(id=attraction_id),
        defaults={
            "created": now,
            "last_visited": now
        }
    )

    if not created:
        history_obj.last_visited = now
        history_obj.save()

    return JsonResponse({
        "status": "ok"
    })


@with_user_id
def history(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "visited": {
            "museums": models.Museum.objects.filter(history__user_id=request.user_id).count(),
            "wineries": models.Winery.objects.filter(history__user_id=request.user_id).count(),
            "zoos": models.Zoo.objects.filter(history__user_id=request.user_id).count(),
            "off_road": models.OffRoad.objects.filter(history__user_id=request.user_id).count(),
        }
    })


@with_user_id
def delete_history(request: UserRequest):
    models.History.objects.filter(user_id=request.user_id).delete()

    return JsonResponse({
        "status": "ok"
    })


@with_user_id
def favorite(request: UserRequest):
    attraction_id = int(request.data["id"])

    # If value is given, update favorite status
    if "value" in request.data:
        if request.data["value"]:
            models.Favorite.objects.get_or_create(
                user_id=request.user_id,
                attraction_id=attraction_id,
                defaults={
                    "created": datetime.utcnow().replace(tzinfo=pytz.UTC)
                }
            )
        else:
            models.Favorite.objects.filter(
                user_id=request.user_id,
                attraction_id=attraction_id
            ).delete()

        return JsonResponse({
            "status": "ok",
        })
    else:
        return JsonResponse({
            "status": "ok",
            "value": models.Favorite.objects.filter(
                user_id=request.user_id,
                attraction_id=attraction_id
            ).count() > 0
        })


@with_user_id
def favorites(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "favorites": {
            "museums": models.Museum.objects.filter(favorite__user_id=request.user_id).count(),
            "wineries": models.Winery.objects.filter(favorite__user_id=request.user_id).count(),
            "zoos": models.Zoo.objects.filter(favorite__user_id=request.user_id).count(),
            "off_road": models.OffRoad.objects.filter(favorite__user_id=request.user_id).count()
        }
    })


@with_user_id
def history_list(request: UserRequest, model):
    result = []

    for item in model.history(request.user_id):
        result.append(item.to_short_json)

    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): result
    })


@with_user_id
def favorites_list(request: UserRequest, model):
    result = []

    for item in model.favorite(request.user_id):
        result.append(item.to_short_json)

    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): result
    })


@never_cache
def map_attractions(request):
    lon_min = float(request.GET["lon_min"])
    lon_max = float(request.GET["lon_max"])
    lat_min = float(request.GET["lat_min"])
    lat_max = float(request.GET["lat_max"])

    attractions = []
    for attraction in models.Attraction.objects.filter(
            long__gte=lon_min,
            long__lte=lon_max,
            lat__gte=lat_min,
            lat__lte=lat_max,
            content_type__isnull=False
    ).select_related("content_type"):
        attractions.append({
            "id": attraction.id,
            "name": attraction.name,
            "long": attraction.long,
            "lat": attraction.lat,
            "type": attraction.content_type.model_class().api_single_key()
        })

    return JsonResponse({
        "status": "ok",
        "attractions": attractions
    })


def _get_off_road_trip_types_last_modified(request):
    return models.OffRoadTripType.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_off_road_trip_types_last_modified)
def get_off_road_trip_types(request):
    return JsonResponse({
        "status": "ok",
        "trip_types": list(map(
            lambda x: x.to_json,
            models.OffRoadTripType.objects.order_by("name")
        ))
    })


def _get_trail_modified_date(_request, trail_id: str) -> Optional[datetime]:
    try:
        return models.Trail.objects.get(id=trail_id).date_modified
    except models.Trail.DoesNotExist:
        return None


def _trail_points_url(trail_id: str) -> str:
    cdn = settings.ASSETS.get("cdn")
    prefix = settings.ASSETS["prefix"]
    bucket = settings.ASSETS["bucket"]

    if cdn is not None:
        return f"https://{cdn}/{prefix}trails/{trail_id}.csv.gz"
    else:
        return f"https://{bucket}.s3.amazonaws.com/{prefix}trails/{trail_id}.csv.gz"


@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_trail_modified_date)
def get_trail(request, trail_id: str):
    trail = get_object_or_404(models.Trail, id=trail_id)

    additional_images = []
    for image in trail.additional_images.all():
        additional_images.append(image.landscape_thumb(900).to_json)

    data = trail.to_short_json
    data.update({
        "points": _trail_points_url(trail.id),
        "owner": trail.owner.to_json,
        "additional_images": additional_images
    })

    return JsonResponse({
        "status": "ok",
        "trail": data
    })


def _trails_query_set(request) -> Optional[datetime]:
    return models.Trail.objects.all()


def _trails_modified(request):
    try:
        return _trails_query_set(request).latest("date_modified").date_modified
    except models.Trail.DoesNotExist:
        return None


@cache_page(60 * 60)
@condition(last_modified_func=_trails_modified)
def get_trails(request):
    trails = _trails_query_set(request)

    data = []

    for trail in trails:
        data.append(trail.to_short_json)

    return JsonResponse({
        "status": "ok",
        "trails": data
    })


def get_distance(point1, point2):
    R = 6370
    lat1 = radians(point1[0])
    lon1 = radians(point1[1])
    lat2 = radians(point2[0])
    lon2 = radians(point2[1])

    dlon = lon2 - lon1
    dlat = lat2- lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance


@csrf_exempt
def upload_start(request):
    if request.method != "POST":
        return HttpResponse("Only post requests allowed", status=http.client.METHOD_NOT_ALLOWED)

    user = jwt.decode(
        request.POST["token"],
        settings.SECRET_KEY,
        audience=settings.AUDIENCE,
        algorithms='HS256'
    )

    user_id = uuid.UUID(user["id"])

    with gzip.open(request.FILES["file"], "rt") as gh:
        reader = csv.reader(gh)
        header = {}
        index = 0

        data = []

        for col in next(reader):
            header[col] = index
            index += 1

        for row in reader:
            data.append({
                "Latitude": float(row[header["Latitude"]]),
                "Longitude": float(row[header["Longitude"]]),
                "Altitude": float(row[header["Altitude"]])
            })

    if len(data) == 0:
        return HttpResponse("File has no records", status=http.client.BAD_REQUEST)

    elv_gain = 0
    last_elv = data[0]["Altitude"]

    for point in data:
        if point["Altitude"] > last_elv:
            elv_gain += point["Altitude"] - last_elv
        last_elv = point["Altitude"]

    lat = mean(map(lambda x: x["Latitude"], data))
    long = mean(map(lambda x: x["Longitude"], data))

    distance = 0.0

    last_point = data[0]
    for point in data[1:]:
        distance += get_distance(
            (last_point["Latitude"], last_point["Longitude"]),
            (point["Latitude"], point["Longitude"])
        )
        last_point = point

    trail_id = uuid.uuid4()

    s3 = boto3.client("s3", **settings.ASSETS["config"])
    key = settings.ASSETS["prefix"] + "trails/" + str(trail_id) + ".csv.gz"
    bucket = settings.ASSETS["bucket"]

    request.FILES["file"].seek(0)
    s3.upload_fileobj(request.FILES["file"], bucket, key, ExtraArgs={
        "ContentType": "text/csv",
        "ContentEncoding": "gzip",
        "ACL": "public-read",
        "CacheControl": "public, max-age=2592000"
    })

    trail = models.Trail(
        id=trail_id,
        name="upload",
        difficulty="M",
        length=int(distance),
        elv_gain=int(elv_gain),
        lat=lat,
        long=long,
        owner_id=str(user_id)
    )

    trail.save()

    return JsonResponse({
        "status": "ok",
        "trail": {
            "id": str(trail_id)
        }
    })

