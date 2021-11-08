from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

from attractions2 import models


def _get_regions_last_modified(request):
    return models.Region.objects.latest("date_modified").date_modified


# cache regions for 1 day
@cache_page(60*60*24)
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
@cache_page(60*60*24)
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
        qset = qset.filter(region_id=int(request.GET["region_id"]))

    return qset


def _get_museums_last_modified(request):
    return _get_museums_qset(request).latest("date_modified").date_modified


# TODO: don't cache for now, rapidly changing
@condition(last_modified_func=_get_museums_last_modified)
def get_museums(request):
    museums = []

    for museum in _get_museums_qset(request)\
            .defer("description", "website")\
            .select_related("domain", "region")\
            .order_by("name"):
        museums.append(museum.to_short_json)

    return JsonResponse({
        "status": "ok",
        "museums": museums
    })
