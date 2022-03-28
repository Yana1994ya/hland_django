from typing import NoReturn

import boto3
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from attractions2 import forms, models
from attractions2.base_views import EditView, ManagedEditView
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


class EditMuseum(ManagedEditView):
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


class EditWinery(ManagedEditView):
    form_class = forms.WineryForm
    model = models.Winery

    def success_message(self, instance: models.Winery) -> str:
        return f"Winery {instance.name} was saved successfully"


class EditZoo(ManagedEditView):
    form_class = forms.ZooForm
    model = models.Zoo

    def success_message(self, instance: models.Zoo) -> str:
        return f"Zoo {instance.name} was saved successfully"


class EditOffRoad(ManagedEditView):
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


class EditWaterSports(ManagedEditView):
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


class EditRockClimbing(ManagedEditView):
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


class EditExtremeSports(ManagedEditView):
    form_class = forms.ExtremeSportsForm
    model = models.ExtremeSports

    def success_message(self, instance: models.ExtremeSports) -> str:
        return f"Extreme sports attraction {instance.name} was saved successfully"

    def get_initial(self, instance: models.ExtremeSports) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["sport_type"] = instance.sport_type

        return initial

    def update_instance(self, instance: models.ExtremeSports, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.sport_type = cleaned_data["sport_type"]

    @classmethod
    def template_name(cls) -> str:
        return "attractions/edit_extreme_sports.html"


class EditTrail(EditView):
    form_class = forms.TrailForm
    model = models.Trail

    def success_message(self, instance: models.Trail) -> str:
        return f"Trail {instance.name} was saved successfully"

    def get_initial(self, instance: models.Trail) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["difficulty"] = instance.difficulty
            initial["owner"] = instance.owner
            initial["length"] = instance.length
            initial["elevation_gain"] = instance.elv_gain

            initial["suitabilities"] = instance.suitabilities.all()
            initial["activities"] = instance.activities.all()
            initial["attractions"] = instance.attractions.all()

        return initial

    def update_instance(self, instance: models.Trail, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)

        instance.difficulty = cleaned_data["difficulty"]
        instance.owner = cleaned_data["owner"]
        instance.length = cleaned_data["length"]
        instance.elv_gain = cleaned_data["elevation_gain"]

    def handle_m2m(self, instance: models.Trail, cleaned_data: dict) -> NoReturn:
        instance.suitabilities.set(cleaned_data["suitabilities"], clear=True)
        instance.activities.set(cleaned_data["activities"], clear=True)
        instance.attractions.set(cleaned_data["attractions"], clear=True)

        # Update the coordinates in the handle_m2m function because this requires the
        # id of the trail to be set
        coordinates = cleaned_data["coordinates"]
        if coordinates is not None:
            s3 = boto3.client("s3", **settings.ASSETS["config"])
            key = settings.ASSETS["prefix"] + "trails/" + str(instance.id) + ".csv.gz"
            bucket = settings.ASSETS["bucket"]

            coordinates.seek(0)
            s3.upload_fileobj(coordinates, bucket, key, ExtraArgs={
                "ContentType": "text/csv",
                "ContentEncoding": "gzip",
                "ACL": "public-read",
                "CacheControl": "public, max-age=2592000"
            })

            instance.long = cleaned_data["long"]
            instance.lat = cleaned_data["lat"]
            instance.length = cleaned_data["length"]
            instance.elv_gain = cleaned_data["elevation_gain"]

            # And finally, save the trail with the new specs
            instance.save()


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
