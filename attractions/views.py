import json
from typing import Optional

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from attractions import forms, models


@staff_member_required
def category_image(request, category_id: int):
    category = get_object_or_404(models.Category, pk=category_id)

    if request.method == "GET":
        form = forms.CategoryImageForm()
    else:
        form = forms.CategoryImageForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            category.image = models.ImageAsset.upload_file(
                form.cleaned_data["image"],
                category.image
            )

            category.save()

            # Done, redirect back to get rid of the post and show the image
            return redirect(
                category_image,
                category_id=category_id
            )

    return render(
        request,
        "attractions/category_image.html",
        {
            "cat": category,
            "form": form,
            "category": "attractions"
        }
    )


@staff_member_required
def edit_attraction(request, attraction_id: Optional[int]):
    initial = {}

    if attraction_id is not None:
        attraction = get_object_or_404(models.Attraction, pk=attraction_id)

        initial.update({
            "name": attraction.name,
            "long": attraction.long,
            "lat": attraction.lat,
        })

        attraction_type = attraction.get_category(parent_id=6)
        if attraction_type is not None:
            initial["attraction_type"] = attraction_type

        region = attraction.get_category(parent_id=1)
        if region is not None:
            initial["region"] = region
    else:
        attraction = models.Attraction()

    if request.method == "GET":
        form = forms.AttractionImageForm(initial=initial)
    else:
        form = forms.AttractionImageForm(
            request.POST,
            request.FILES,
            initial=initial
        )

        if form.is_valid():
            if form.cleaned_data["image"]:
                attraction.main_image = models.ImageAsset.upload_file(
                    form.cleaned_data["image"],
                    old_asset=attraction.main_image
                )

            attraction.name = form.cleaned_data["name"]
            attraction.long = form.cleaned_data["long"]
            attraction.lat = form.cleaned_data["lat"]

            attraction.save()

            # check if attraction_type is correct
            attraction.set_category(
                parent_id=6,
                category_id=form.cleaned_data["attraction_type"]
            )

            attraction.set_category(
                parent_id=1,
                category_id=form.cleaned_data["region"]
            )

            if form.cleaned_data["additional_image"]:
                attraction.additional_images.add(models.ImageAsset.upload_file(
                    form.cleaned_data["additional_image"],
                    old_asset=None
                ))

            # Delete any additional image chosen for delete
            for additional_id in request.POST.getlist("delete_additional"):
                additional = attraction.additional_images.get(pk=int(additional_id))
                attraction.additional_images.remove(additional)

                additional.delete()

            # Done, redirect back to get rid of the post and show the image
            messages.add_message(request, messages.INFO, f'Attraction {attraction.name} is saved')

            if request.POST.get("next") == "exit":
                return redirect(view_attractions)
            else:
                return redirect(
                    edit_attraction,
                    attraction_id=attraction.id
                )

    return render(
        request,
        "attractions/edit_attraction.html",
        {
            "attraction": attraction,
            "form": form,
            "category": "attractions"
        }
    )


def view_attractions(request, page_number: int = 1):
    paginator = Paginator(models.Attraction.objects.all(), 30)
    page = paginator.page(page_number)

    return render(
        request,
        "attractions/attractions.html",
        {
            "page": page
        }
    )


def fetch_categories(request, parent_id: Optional[int]):
    if parent_id is None:
        # Root categories don't have any attractions directly
        categories = models.Category.objects.filter(parent_id__isnull=True)
    else:
        # When not root, filter out categories that have attractions in them
        categories = models.Category.objects.filter(
            parent_id=parent_id,
            attraction__in=models.Attraction.qset_from_request(request)
        ).order_by("order").distinct()

    def to_json(cat):
        image = None

        if cat.image:
            image = cat.image.landscape_thumb(300).to_json

        return {"id": cat.pk, "name": cat.name, "image": image}

    return HttpResponse(
        json.dumps(list(map(to_json, categories))),
        content_type="application/json"
    )


def fetch_attractions(request):
    def to_json(attr: models.Attraction):
        image = None

        if attr.main_image:
            image = attr.main_image.landscape_thumb(900).to_json

        additional = []
        for add in attr.additional_images.all():
            additional.append(add.landscape_thumb(900).to_json)

        return {
            "id": attr.pk,
            "name": attr.name,
            "image": image,
            "additional": additional
        }

    return HttpResponse(
        json.dumps(list(map(
            to_json,
            models.Attraction.qset_from_request(request)
        ))),
        content_type="application/json"
    )
