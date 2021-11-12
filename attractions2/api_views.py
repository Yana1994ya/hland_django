from datetime import datetime
import json
import time
import uuid

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_page
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


def _get_museums_qset(request):
    qset = models.Museum.objects.all()

    if "region_id" in request.GET:
        qset = qset.filter(region_id__in=list(map(
            int,
            request.GET.getlist("region_id"),
        )))

    if "domain_id" in request.GET:
        qset = qset.filter(domain_id__in=list(map(
            int,
            request.GET.getlist("domain_id"),
        )))

    return qset


def _get_museums_last_modified(request):
    try:
        return _get_museums_qset(request).latest("date_modified").date_modified
    except models.Museum.DoesNotExist:
        return None


# TODO: don't cache for now, rapidly changing
@condition(last_modified_func=_get_museums_last_modified)
def get_museums(request):
    museums = []

    for museum in _get_museums_qset(request) \
            .defer("description", "website") \
            .select_related("domain", "region") \
            .order_by("name"):
        museums.append(museum.to_short_json)

    return JsonResponse({
        "status": "ok",
        "museums": museums
    })


def _get_museum_last_modified(request, museum_id: int):
    try:
        return models.Museum.objects.get(id=museum_id).date_modified
    except models.Museum.DoesNotExist:
        return None


@condition(last_modified_func=_get_museum_last_modified)
def get_museum(request, museum_id: int):
    try:
        return JsonResponse({
            "status": "ok",
            "museum": models.Museum.objects.get(id=museum_id).to_json
        })
    except models.Museum.DoesNotExist:
        resp = JsonResponse({
            "status": "error",
            "code": "NotFound",
            "message": "The requested museum doesn't exist"
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

    user, created = models.GoogleUser.objects.get_or_create(id=user_id, defaults={
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
                "exp": int(time.time()) + 60*60*24*7,
                "aud": settings.AUDIENCE
            },
            settings.SECRET_KEY,
            algorithm="HS256"
        )
    })


@csrf_exempt
def visit(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    data = json.loads(request.body)
    token = data["token"]
    attraction_id = int(data["id"])

    user = jwt.decode(
        token,
        settings.SECRET_KEY,
        audience=settings.AUDIENCE,
        algorithms='HS256'
    )

    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    history, created = models.History.objects.get_or_create(
        user_id=uuid.UUID(user["id"]),
        attraction=models.Attraction.objects.get(id=attraction_id),
        defaults={
            "created": now,
            "last_visited": now
        }
    )

    if not created:
        history.last_visited = now
        history.save()

    return JsonResponse({
        "status": "ok"
    })

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

        return fn(request, user_id, *args, **kwargs)
    return csrf_exempt(wrapped)


@with_user_id
def history(request, user_id: uuid.UUID):
    return JsonResponse({
        "status": "ok",
        "visited": {
            "museums": models.Museum.objects.filter(history__user_id=user_id).count()
        }
    })


@with_user_id
def history_museums(request, user_id: uuid.UUID):
    museums = []

    for museum in _get_museums_qset(request) \
            .defer("description", "website") \
            .select_related("domain", "region") \
            .filter(history__user_id=user_id) \
            .order_by("-history__last_visited"):
        museums.append(museum.to_short_json)

    return JsonResponse({
        "status": "ok",
        "museums": museums
    })