import dataclasses
import http.client
import json
import logging
import tempfile
import time
import uuid
from datetime import datetime
from typing import Type, List, Dict

import boto3
import django.http.request
import jwt
import pytz
from PIL import ExifTags, Image
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition

from attractions2 import models, forms, base_models
from attractions2.trail import analyze_trail, FileEmpty

log = logging.getLogger(__name__)


def _get_attraction_filter_last_modified(request, model: Type[models.AttractionFilter]):
    return model.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60 * 60 * 24)
@condition(last_modified_func=_get_attraction_filter_last_modified)
def get_attraction_filter(request, model: Type[models.AttractionFilter]):
    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): list(map(
            lambda x: x.to_json,
            model.objects.order_by("name")
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


def query_set_to_json(qset):
    attractions = list(qset)

    image_ids = set(map(
        lambda x: x.main_image_id,
        filter(
            lambda x: x.main_image_id is not None,
            attractions
        )
    ))

    images = models.ImageAsset.resolve_thumbs(image_ids, 600)

    items = []

    for attraction in attractions:
        document = attraction.to_short_json

        if attraction.main_image_id is None:
            document["main_image"] = None
        else:
            document["main_image"] = images[attraction.main_image_id].to_json

        items.append(document)

    return items


# cache explore for 2 hours
@cache_control(public=True, max_age=60 * 60 * 2)
@condition(last_modified_func=_get_explore_last_modified)
def get_explore(request, model):
    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): query_set_to_json(
            _get_explore_qset(request, model, True)
                .order_by("name")
        )
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
        single = model.objects.get(id=attraction_id)
        document = single.to_json

        image_ids = set()
        if single.main_image_id is not None:
            image_ids.add(single.main_image_id)

        additional_images = list(single.additional_images.values_list('pk', flat=True))
        image_ids.update(additional_images)

        images = models.ImageAsset.resolve_thumbs(image_ids, 900)

        if single.main_image_id is None:
            document["main_image"] = None
        else:
            document["main_image"] = images[single.main_image_id].to_json

        document["additional_images"] = list(map(
            lambda image_id: images[image_id].to_json,
            additional_images
        ))

        return JsonResponse({
            "status": "ok",
            model.api_single_key(): document
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

    counts = models.Attraction.objects.filter(**attraction_filter) \
        .values("content_type__model") \
        .annotate(count=Count("id"))

    counts = dict(map(lambda x: (x["content_type__model"], x["count"]), counts))

    results = {}

    for model in models.get_attraction_classes():
        results[model.api_multiple_key()] = counts.get(model._meta.model_name, 0)

    return results


@with_user_id
def history(request: UserRequest):
    return JsonResponse({
        "status": "ok",
        "visited": count_items(request.user_id, "history")
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
        "favorites": count_items(request.user_id, "favorite")
    })


@with_user_id
def history_list(request: UserRequest, model):
    result = []

    for item in model.history(request.user_id):
        result.append(item.to_short_json)

    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): query_set_to_json(
            model.history(request.user_id)
        )
    })


@with_user_id
def favorites_list(request: UserRequest, model):
    return JsonResponse({
        "status": "ok",
        model.api_multiple_key(): query_set_to_json(
            model.favorite(request.user_id)
        )
    })


@never_cache
def map_attractions(request):
    lon_min = float(request.GET["lon_min"])
    lon_max = float(request.GET["lon_max"])
    lat_min = float(request.GET["lat_min"])
    lat_max = float(request.GET["lat_max"])

    qset = models.Attraction.objects.filter(
        long__gte=lon_min,
        long__lte=lon_max,
        lat__gte=lat_min,
        lat__lte=lat_max,
        content_type__isnull=False
    )

    if request.GET.get("objects") == "attractions":
        qset = qset.exclude(content_type=ContentType.objects.get_for_model(models.Trail))
    elif request.GET.get("objects") == "trails":
        qset = qset.filter(content_type=ContentType.objects.get_for_model(models.Trail))

    attractions = list(qset.select_related("content_type"))

    image_ids = set(map(
        lambda x: x.main_image_id,
        filter(
            lambda x: x.main_image_id is not None,
            attractions
        )
    ))

    images = models.ImageAsset.resolve_thumbs(image_ids, 600)

    result = []
    for attraction in attractions:
        json_doc = {
            "id": attraction.id,
            "name": attraction.name,
            "long": attraction.long,
            "lat": attraction.lat,
            "type": attraction.content_type.model_class().api_single_key(),
            "avg_rating": attraction.avg_rating,
            "rating_count": attraction.rating_count
        }

        if attraction.main_image_id is None:
            json_doc["main_image"] = None
        else:
            json_doc["main_image"] = images[attraction.main_image_id].to_json

        result.append(json_doc)

    return JsonResponse({
        "status": "ok",
        "attractions": result
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
        images = list(models.ImageAsset.objects.filter(
            id__in=image_ids,
            userimage__user_id=user_id,
        ))

    trail = models.Trail(
        name=name,
        difficulty=difficulty,
        length=int(trail_analysis.distance),
        elv_gain=int(trail_analysis.elevation_gain),
        lat=trail_analysis.center_latitude,
        long=trail_analysis.center_longitude,
        owner_id=str(user_id)
    )

    if images:
        trail.main_image = images[0]

    trail.save()

    s3 = boto3.client("s3", **settings.ASSETS["config"])
    key = settings.ASSETS["prefix"] + "trails/" + str(trail.id) + ".csv.gz"
    bucket = settings.ASSETS["bucket"]

    request.FILES["file"].seek(0)
    s3.upload_fileobj(request.FILES["file"], bucket, key, ExtraArgs={
        "ContentType": "text/csv",
        "ContentEncoding": "gzip",
        "ACL": "public-read",
        "CacheControl": "public, max-age=2592000"
    })

    # Add any additional image to the trail
    for additional_image in images[1:]:
        trail.additional_images.add(additional_image)

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
            "id": trail.id
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
        thumbs = [
            image_asset.landscape_thumb(900).to_json,
            image_asset.landscape_thumb(64).to_json
        ]

        if trail is None:
            return JsonResponse({
                "status": "ok",
                "image": {
                    "image_id": image_asset.id,
                    "thumbs": thumbs
                }
            })
        else:
            if trail.main_image is None:
                trail.main_image = image_asset
                trail.save()
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


@with_user_id
def add_comment(request: UserRequest):
    comment_text = None
    if "text" in request.data:
        comment_text = request.data["text"]

    attraction_id = request.data["attraction_id"]

    # Make sure the data we're referring a comment to actually exists
    if models.Attraction.objects.filter(id=attraction_id).count() == 0:
        return JsonResponse({
            "status": "error",
            "code": "InvalidData",
            "message": "Attraction for comment not found"
        })

    rating = int(request.data["rating"])

    if rating < 1:
        return JsonResponse({
            "status": "error",
            "code": "InvalidData",
            "message": "Rating can't be less than 1"
        })
    elif rating > 5:
        return JsonResponse({
            "status": "error",
            "code": "InvalidData",
            "message": "Rating can't be more than 1"
        })

    comment = base_models.AttractionComment(
        attraction_id=attraction_id,
        user_id=request.user_id,
        text=comment_text,
        rating=rating
    )
    comment.save()

    if "image_ids" in request.data:
        image_ids = request.data["image_ids"]
        for image in models.ImageAsset.objects.filter(id__in=image_ids, userimage__user_id=request.user_id):
            comment.images.add(image)

    # Recalculate the denormalized fields
    attraction = models.Attraction.objects.annotate(
        calc_avg_rating=Avg("attractioncomment__rating"),
        calc_count=Count("attractioncomment__id")
    ).get(id=attraction_id)

    attraction.avg_rating = attraction.calc_avg_rating
    attraction.rating_count = attraction.calc_count
    attraction.save()

    return JsonResponse({
        "status": "ok",
        "comment_id": comment.id
    })


def get_comments(_request, attraction_id: int, page_number: int) -> JsonResponse:
    qset = base_models.AttractionComment.objects.filter(
        attraction_id=attraction_id
    )

    paginator = Paginator(
        qset.order_by("-created")
            .select_related("user")
            .prefetch_related("images"),
        30
    )

    page = paginator.page(page_number)
    # Load the thumbs in an efficient manner so many comments don't bring the application to a crawl
    image_ids = set()

    for comment in page.object_list:
        for image in comment.images.all():
            image_ids.add(image.id)

    thumbs = {}
    for thumb in models.ImageAsset.objects.filter(parent__id__in=image_ids, request_width=64, request_height=64):
        thumbs[thumb.parent_id] = thumb

    result = []
    for comment in page.object_list:
        comment_json = {
            "id": comment.id,
            "user": comment.user.to_json,
            "rating": comment.rating,
            "text": comment.text,
            "created": comment.created.strftime("%Y-%m-%d %H:%M:%S"),
            "images": []
        }

        for image in comment.images.all():
            if image.id not in thumbs:
                thumb = image.landscape_thumb(64)
            else:
                thumb = thumbs[image.id]

            thumb.parent = image

            comment_json["images"].append(thumb.to_json)

        result.append(comment_json)

    return JsonResponse({
        "status": "ok",
        "comments": {
            "pages": paginator.num_pages,
            "page": page_number,
            "items": result
        }
    })


def search(request):
    q = request.GET.get("q", "")
    page_number = 1

    if "page" in request.GET:
        page_number = int(request.GET["page"])

    paginator = Paginator(
        models.Attraction.objects.filter(name__icontains=q)
            .select_related("content_type"),
        30
    )

    page = paginator.page(page_number)
    # Load the thumbs in an efficient manner so many comments don't bring the application to a crawl
    image_ids = set()

    for item in page.object_list:
        if item.main_image_id is not None:
            image_ids.add(item.main_image_id)

    images = models.ImageAsset.resolve_thumbs(image_ids, 600)

    items = []

    for attraction in page.object_list:
        document = {
            "id": attraction.id,
            "name": attraction.name,
            "long": attraction.long,
            "lat": attraction.lat,
            "type": attraction.content_type.model_class().api_single_key(),
            "avg_rating": attraction.avg_rating,
            "rating_count": attraction.rating_count
        }

        if attraction.main_image_id is None:
            document["main_image"] = None
        else:
            document["main_image"] = images[attraction.main_image_id].to_json

        items.append(document)

    return JsonResponse({
        "status": "ok",
        "page": {
            "items": items,
            "num_pages": paginator.num_pages
        }
    })
