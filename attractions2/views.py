import uuid
from typing import NoReturn, Optional
from uuid import UUID

import boto3
from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from attractions2 import forms, models
from attractions2.base_views import EditView
from attractions2.pager import Pager


@staff_member_required
def display(request, model, page_number: int):
    paginator = Paginator(model.objects.all().only("name").order_by("name"), 30)
    page = paginator.page(page_number)

    return render(
        request,
        f"attractions/{model.api_multiple_key()}.html",
        {
            "page": page,
            "pager": Pager(page, model, display)
        }
    )


@staff_member_required
def homepage(request):
    return render(
        request,
        "attractions/homepage.html"
    )


class EditMuseum(EditView):
    form_class = forms.MuseumForm
    model = models.Museum

    def success_message(self, instance: models.Museum) -> str:
        return f"Museum {instance.name} was saved successfully"

    def get_initial(self, instance: models.Museum) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["domain"] = instance.domain

        return initial

    def update_instance(self, instance: models.Museum, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.domain = cleaned_data["domain"]


class EditWinery(EditView):
    form_class = forms.WineryForm
    model = models.Winery

    def success_message(self, instance: models.Winery) -> str:
        return f"Winery {instance.name} was saved successfully"


class EditZoo(EditView):
    form_class = forms.ZooForm
    model = models.Zoo

    def success_message(self, instance: models.Zoo) -> str:
        return f"Zoo {instance.name} was saved successfully"


class EditOffRoad(EditView):
    form_class = forms.OffRoadForm
    model = models.OffRoad

    def success_message(self, instance: models.OffRoad) -> str:
        return f"OffRoad trip {instance.name} was saved successfully"

    def get_initial(self, instance: models.OffRoad) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["trip_type"] = instance.trip_type

        return initial

    def update_instance(self, instance: models.OffRoad, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.trip_type = cleaned_data["trip_type"]

    @classmethod
    def template_name(cls) -> str:
        return "attractions/edit_offroad.html"


class EditWaterSports(EditView):
    form_class = forms.WaterSportsForm
    model = models.WaterSports

    def success_message(self, instance: models.OffRoad) -> str:
        return f"Water sports attraction {instance.name} was saved successfully"

    def get_initial(self, instance: models.WaterSports) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["attraction_type"] = instance.attraction_type

        return initial

    def update_instance(self, instance: models.WaterSports, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.attraction_type = cleaned_data["attraction_type"]

    @classmethod
    def template_name(cls) -> str:
        return "attractions/edit_water_sports.html"


class EditRockClimbing(EditView):
    form_class = forms.RockClimbingForm
    model = models.RockClimbing

    def success_message(self, instance: models.RockClimbing) -> str:
        return f"Rock climbing attraction {instance.name} was saved successfully"

    def get_initial(self, instance: models.RockClimbing) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["attraction_type"] = instance.attraction_type

        return initial

    def update_instance(self, instance: models.RockClimbing, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.attraction_type = cleaned_data["attraction_type"]

    @classmethod
    def template_name(cls) -> str:
        return "attractions/edit_rock_climbing.html"


@staff_member_required
def edit_trail(request, trail_id: Optional[UUID] = None):
    if trail_id is None:
        trail = models.Trail()
        initial = {}
        action = reverse(edit_trail)
    else:
        trail = models.Trail.objects.get(id=trail_id)

        initial = {
            "name": trail.name,
            "difficulty": trail.difficulty,
            "owner": trail.owner,
            "suitabilities": trail.suitabilities.all(),
            "attractions": trail.attractions.all(),
            "activities": trail.activities.all(),
            "length": trail.length,
            "elevation_gain": trail.elv_gain,
            "long": trail.long,
            "lat": trail.lat
        }

        action = reverse(edit_trail, kwargs={"trail_id": trail_id})

    if request.method == "POST":
        form = forms.TrailForm(request.POST, request.FILES, initial=initial)

        for additional_image_id in request.POST.getlist("delete_additional"):
            try:
                image = trail.additional_images.get(id=int(additional_image_id))
                image.delete()
            except models.ImageAsset.DoesNotExist:
                pass

        if form.is_valid():
            if trail.id is None:
                trail.id = uuid.uuid4()

            coordinates = form.cleaned_data["coordinates"]
            if coordinates is not None:
                s3 = boto3.client("s3", **settings.ASSETS["config"])
                key = settings.ASSETS["prefix"] + "trails/" + str(trail.id) + ".csv.gz"
                bucket = settings.ASSETS["bucket"]

                coordinates.seek(0)
                s3.upload_fileobj(coordinates, bucket, key, ExtraArgs={
                    "ContentType": "text/csv",
                    "ContentEncoding": "gzip",
                    "ACL": "public-read",
                    "CacheControl": "public, max-age=2592000"
                })

                trail.long = form.cleaned_data["long"]
                trail.lat = form.cleaned_data["lat"]
                trail.length = form.cleaned_data["length"]
                trail.elv_gain = form.cleaned_data["elevation_gain"]

            trail.owner = form.cleaned_data["owner"]
            trail.difficulty = form.cleaned_data["difficulty"]
            trail.name = form.cleaned_data["name"]

            main_image = form.cleaned_data["image"]
            if main_image:
                trail.main_image = models.ImageAsset.upload_file(
                    main_image,
                    old_asset=trail.main_image
                )

            trail.save()

            trail.suitabilities.set(form.cleaned_data["suitabilities"], clear=True)
            trail.activities.set(form.cleaned_data["activities"], clear=True)
            trail.attractions.set(form.cleaned_data["attractions"], clear=True)

            additional_image = form.cleaned_data["additional_image"]
            if additional_image:
                trail.additional_images.add(models.ImageAsset.upload_file(
                    additional_image,
                    old_asset=None
                ))

            messages.add_message(request, messages.INFO, f"Trail {trail.name} was updated/created successfully")

            if request.POST.get("next") == "exit":
                return reverse("trail")
            else:
                return HttpResponseRedirect(reverse(edit_trail, kwargs={"trail_id": trail.id}))

    else:
        form = forms.TrailForm(initial=initial)

    return render(
        request,
        "attractions/trail.html",
        {
            "form": form,
            "instance": trail,
            "action": action
        }
    )


@staff_member_required
@csrf_exempt
def trail_upload(request, trail_id: UUID):
    trail = models.Trail.objects.get(id=trail_id)

    if request.method != "POST":
        return HttpResponse(status=405, body="Only post requests are allowed")
    else:
        form = forms.UserUploadImageForm(request.POST, request.FILES)

        if form.is_valid():
            image = models.ImageAsset.upload_file(
                form.cleaned_data["image"],
                old_asset=None
            )

            image.save()

            trail.additional_images.add(image)

            image_data = image.to_json
            image_data["id"] = image.id

            return JsonResponse({
                "status": "ok",
                "image": image_data
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": str(form.errors)
            })


@staff_member_required
@csrf_exempt
def attraction_upload(request, attraction_id: int):
    attraction = models.Attraction.objects.get(id=attraction_id)

    if request.method != "POST":
        return HttpResponse(status=405, body="Only post requests are allowed")
    else:
        form = forms.UserUploadImageForm(request.POST, request.FILES)

        if form.is_valid():
            image = models.ImageAsset.upload_file(
                form.cleaned_data["image"],
                old_asset=None
            )

            image.save()

            attraction.additional_images.add(image)

            image_data = image.to_json
            image_data["id"] = image.id

            return JsonResponse({
                "status": "ok",
                "image": image_data
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": str(form.errors)
            })

