import dataclasses
import http.client
import json
import tempfile
import time
import uuid
from datetime import datetime
from typing import Optional, Type, List, Dict, Any

import boto3
import django.http.request
import jwt
import pytz
from PIL import ExifTags, Image
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition

from attractions2 import models, forms, base_models
from attractions2.trail import analyze_trail, FileEmpty


def _get_regions_last_modified(request):
    return base_models.Region.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_regions_last_modified)
def get_regions(request):
    return JsonResponse({
        "status": "ok",
        "regions": list(map(
            lambda x: x.to_json,
            base_models.Region.objects.order_by("name")
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

    if user.banned_until is not None and user.banned_until > datetime.now():
        return JsonResponse({
            "status": "error",
            "code": "Banned",
            "message": "This user is banned until:" + user.banned_until.isoformat()
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
        "user": {
            "token": jwt.encode(
                {
                    "id": str(user.id),
                    "exp": int(time.time()) + 60 * 60 * 24 * 7,
                    "aud": settings.AUDIENCE
                },
                settings.SECRET_KEY,
                algorithm="HS256"
            ),
            "id": str(user_id)
        }
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
def visit_trail(request: UserRequest):
    trail_id = request.data["id"]

    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    history_obj, created = models.TrailHistory.objects.get_or_create(
        user_id=request.user_id,
        trail=models.Trail.objects.get(id=trail_id),
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


def count_items(user_id: uuid.UUID, key: str) -> Dict[str, int]:
    attraction_filter = {
        key + "__user_id": user_id
    }

    trail_filter = {
        "trail" + key + "__user_id": user_id
    }

    return {
        "museums": models.Museum.objects.filter(**attraction_filter).count(),
        "wineries": models.Winery.objects.filter(**attraction_filter).count(),
        "zoos": models.Zoo.objects.filter(**attraction_filter).count(),
        "off_road": models.OffRoad.objects.filter(**attraction_filter).count(),
        "trails": models.Trail.objects.filter(**trail_filter).count(),
        "water_sports": models.WaterSports.objects.filter(**attraction_filter).count(),
        "rock_climbing": models.RockClimbing.objects.filter(**attraction_filter).count(),
    }


@with_user_id
def history(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "visited": count_items(request.user_id, "history")
    })


@with_user_id
def delete_history(request: UserRequest):
    models.History.objects.filter(user_id=request.user_id).delete()
    models.TrailHistory.objects.filter(user_id=request.user_id).delete()

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
def favorite_trail(request: UserRequest):
    trail_id = request.data["id"]

    # If value is given, update favorite status
    if "value" in request.data:
        if request.data["value"]:
            models.TrailFavorite.objects.get_or_create(
                user_id=request.user_id,
                trail_id=trail_id,
                defaults={
                    "created": datetime.utcnow().replace(tzinfo=pytz.UTC)
                }
            )
        else:
            models.TrailFavorite.objects.filter(
                user_id=request.user_id,
                trail_id=trail_id
            ).delete()

        return JsonResponse({
            "status": "ok",
        })
    else:
        return JsonResponse({
            "status": "ok",
            "value": models.TrailFavorite.objects.filter(
                user_id=request.user_id,
                trail_id=trail_id
            ).count() > 0
        })


@with_user_id
def favorites(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "favorites": count_items(request.user_id, "favorite")
    })


@with_user_id
def favorites_trails(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "trails": list(map(
            lambda x: x.to_short_json,
            models.Trail.objects.filter(trailfavorite__user_id=request.user_id).order_by("-trailfavorite__created")
        ))
    })


@with_user_id
def history_trails(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "trails": list(map(
            lambda x: x.to_short_json,
            models.Trail.objects.filter(trailhistory__user_id=request.user_id).order_by("-trailhistory__created")
        ))
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


@cache_page(60 * 60 * 24)
def get_attraction_filter(request, model: Type[models.AttractionFilter]):
    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): list(map(
            lambda x: x.to_json,
            model.objects.order_by("name")
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
    # For performance, read the correct thumbnail for all images at the same time
    for image in models.ImageAsset.objects.filter(
        request_width=900,
        parent__trail_additional_image=trail,
    ).select_related("parent").order_by("id"):
        additional_images.append(image.to_json)

    data = trail.to_short_json
    data.update({
        "points": _trail_points_url(trail.id),
        "owner": trail.owner.to_json,
        "additional_images": additional_images
    })

    if trail.main_image:
        data["main_image"] = trail.main_image.landscape_thumb(900).to_json

    data["activities"] = list(map(lambda x: x.to_json, trail.activities.all()))
    data["attractions"] = list(map(lambda x: x.to_json, trail.attractions.all()))
    data["suitabilities"] = list(map(lambda x: x.to_json, trail.suitabilities.all()))

    return JsonResponse({
        "status": "ok",
        "trail": data
    })


def _trails_query_set(request) -> Any:
    query_set = models.Trail.objects.all()

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

    try:
        trail_analysis = analyze_trail(request.FILES["file"])
    except FileEmpty:
        return HttpResponse("File has no records", status=http.client.BAD_REQUEST)

    name = request.POST.get("name", "").strip()

    if not name:
        return HttpResponse("Trail has no name", status=http.client.BAD_REQUEST)

    difficulty = request.POST.get("difficulty", "")
    if difficulty not in {"E", "M", "H"}:
        return HttpResponse("Difficulty must be E, M or H", status=http.client.BAD_REQUEST)

    images = []
    image_ids_str = request.POST.get("images", "")
    if image_ids_str:
        image_ids = list(map(int, image_ids_str.split(",")))
        images = list(models.UserImage.objects.filter(user_id=user_id, id__in=image_ids))

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
        name=name,
        difficulty=difficulty,
        length=int(trail_analysis.distance),
        elv_gain=int(trail_analysis.elevation_gain),
        lat=trail_analysis.center_latitude,
        long=trail_analysis.center_longitude,
        owner_id=str(user_id)
    )

    if images:
        trail.main_image = images[0].image

    trail.save()

    # Add any additional image to the trail
    for additional_image in images[1:]:
        trail.additional_images.add(additional_image.image)

    def get_tags(field_name: str, model: Type[models.AttractionFilter]) -> List[models.AttractionFilter]:
        str_ids = request.POST.get(field_name, "").strip()  # type: str

        if not str_ids:
            return []

        ids = map(int, str_ids.split(","))

        return list(model.objects.filter(pk__in=ids))

    for activity in get_tags("activities", models.TrailActivity):
        trail.activities.add(activity)

    for attraction in get_tags("attractions", models.TrailAttraction):
        trail.attractions.add(attraction)

    for suitability in get_tags("suitabilities", models.TrailSuitability):
        trail.suitabilities.add(suitability)

    return JsonResponse({
        "status": "ok",
        "trail": {
            "id": str(trail_id)
        }
    })


def rotate_image(image):
    """
    Make sure the images are rotated correctly in a way where we don't need to consider orientation
    exif, that makes thumbnail generation easier.
    """
    orientation = None

    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break

    exif = image.image._getexif()

    if exif[orientation] == 3:
        image = Image.open(image.file)
        return image.rotate(180, expand=True)
    elif exif[orientation] == 6:
        image = Image.open(image.file)
        return image.rotate(270, expand=True)
    elif exif[orientation] == 8:
        image = Image.open(image.file)
        return image.rotate(90, expand=True)
    else:
        return None


@csrf_exempt
def upload_image(request):
    if request.method != "POST":
        return HttpResponse("Only post requests allowed", status=http.client.METHOD_NOT_ALLOWED)

    user = jwt.decode(
        request.POST["token"],
        settings.SECRET_KEY,
        audience=settings.AUDIENCE,
        algorithms='HS256'
    )

    user_id = uuid.UUID(user["id"])

    form = forms.UserUploadImageForm(request.POST, request.FILES)

    if form.is_valid():
        image = form.cleaned_data["image"]
        trail_id = form.cleaned_data["trail_id"]
        trail = None

        if trail_id is not None:
            try:
                trail = models.Trail.objects.get(owner_id=user_id, id=trail_id)
            except models.Trail.DoesNotExist:
                return JsonResponse({
                    "status": "error",
                    "code": "MissingTrail",
                    "message": f"Trail with id: {trail_id} wasn't found or doesn't belong to user"
                })


        rotated = rotate_image(image)
        if rotated:
            image.file = tempfile.TemporaryFile()
            rotated.save(image.file, "JPEG")
            # Seek to start
            image.file.seek(0)

            image.image = rotated

        image_asset = models.ImageAsset.upload_file(
            image,
            old_asset=None
        )

        user_image = models.UserImage(
            user_id=user_id,
            image=image_asset
        )

        user_image.save()

        # Generate thumbnail to improve future performance
        image_asset.landscape_thumb(900)

        if trail is None:
            return JsonResponse({
                "status": "ok",
                "image_id": user_image.id
            })
        else:
            trail.additional_images.add(image_asset)

            return JsonResponse({
                "status": "ok"
            })
    else:
        return JsonResponse({
            "status": "error",
            "code": "BadRequest",
            "message": "Failed to validate image"
        })


def resolve_object_type(object_type) -> Optional[ContentType]:
    if object_type == "museum":
        return ContentType.objects.get(model="museum", app_label="attractions2")
    elif object_type == "winery":
        return ContentType.objects.get(model="winery", app_label="attractions2")
    elif object_type == "zoo":
        return ContentType.objects.get(model="zoo", app_label="attractions2")
    elif object_type == "trail":
        return ContentType.objects.get(model="trail", app_label="attractions2")
    elif object_type == "off_road_trip":
        return ContentType.objects.get(model="offroad", app_label="attractions2")

    return None


@with_user_id
def add_comment(request: UserRequest):
    object_type = request.data["object_type"]

    ct = resolve_object_type(object_type)
    if ct is None:
        return JsonResponse({
            "status": "error",
            "code": "NotFound",
            "message": f"Object of type: {object_type} is not found"
        })

    comment_text = request.data["comment_text"]

    if not comment_text:
        return JsonResponse({
            "status": "error",
            "code": "InvalidData",
            "message": "Comment text is not found"
        })

    content_id = request.data["content_id"]

    # Make sure the data we're referring a comment to actually exists
    if ct.model_class().objects.filter(id=content_id).count() == 0:
        return JsonResponse({
            "status": "error",
            "code": "InvalidData",
            "message": "Content for comment not found"
        })

    comment = models.UserComment(
        user_id=request.user_id,
        text=comment_text,
        content_type=ct,
        content_id=str(content_id)
    )

    comment.save()

    return JsonResponse({
        "status": "ok",
        "comment_id": comment.id
    })


def get_comments(request, object_type, content_id):
    ct = resolve_object_type(object_type)
    if ct is None:
        return JsonResponse({
            "status": "error",
            "code": "NotFound",
            "message": f"Object of type: {object_type} is not found"
        })

    return JsonResponse({
        "status": "ok",
        "comments": list(map(
            lambda x: x.to_json,
            models.UserComment.objects.filter(
                content_type=ct,
                content_id=content_id
            )
        ))
    })
