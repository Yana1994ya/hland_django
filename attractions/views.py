import json
from typing import Optional

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from attractions import forms, models
from market_review import thumb_gen
from market_review.models import ImageAsset
from market_review.views import delete_asset, upload_file


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
            category.image = upload_file(
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


def main_image_thumb(image:Optional[ImageAsset]) -> Optional[ImageAsset]:
    if image is None:
        return None

    return thumb_gen.create_thumb(
        url=image.url,
        parent_id=image.id,
        requested={
            "request_width": 900
        },
        thumb_size=(900, 900)
    )


@staff_member_required
def attraction_image(request, attraction_id: int):
    attraction = get_object_or_404(models.Attraction, pk=attraction_id)

    if request.method == "GET":
        form = forms.AttractionImageForm()
    else:
        if "delete_additional" in request.POST:
            for additional_id in request.POST.getlist("delete_additional"):
                additional = attraction.additional_images.get(pk=int(additional_id))
                delete_asset(additional)
                attraction.additional_images.remove(additional)

            # Done, redirect back to get rid of the post and show the image
            return redirect(
                attraction_image,
                attraction_id=attraction_id
            )

        form = forms.AttractionImageForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            if form.cleaned_data["image"]:
                attraction.main_image = upload_file(
                    form.cleaned_data["image"],
                    old_asset=attraction.main_image
                )

                attraction.save()

            if form.cleaned_data["additional_image"]:
                attraction.additional_images.add(upload_file(
                    form.cleaned_data["additional_image"],
                    old_asset=None
                ))

            # Done, redirect back to get rid of the post and show the image
            return redirect(
                attraction_image,
                attraction_id=attraction_id
            )

    additional_images = []
    for image in attraction.additional_images.all():
        additional_images.append({
            "thumb": main_image_thumb(image),
            "image": image
        })

    return render(
        request,
        "attractions/attraction_image.html",
        {
            "attraction": attraction,
            "form": form,
            "category": "attractions",
            "thumb": main_image_thumb(attraction.main_image),
            "additional_images": additional_images
        }
    )


def list_categories(request, parent_id: Optional[int]):
    categories = models.Category.objects.filter(parent_id=parent_id).order_by("order")

    def to_json(cat):
        image = None

        if cat.image:
            image = cat.image.url

        return {"id": cat.pk, "name": cat.name, "image": image}

    return HttpResponse(
        json.dumps(list(map(to_json, categories))),
        content_type="application/json"
    )


def list_attractions(request, category_id: int):
    category = get_object_or_404(models.Category, pk=category_id)

    def to_json(attr:models.Attraction):
        image = None

        if attr.main_image:
            image = main_image_thumb(attr.main_image).to_json

        additional = []
        for add in attr.additional_images.all():
            additional.append(main_image_thumb(add).to_json)

        return {
            "id": attr.pk,
            "name": attr.name,
            "image": image,
            "additional": additional
        }

    return HttpResponse(
        json.dumps(list(map(to_json, category.attraction_set.all()))),
        content_type="application/json"
    )
