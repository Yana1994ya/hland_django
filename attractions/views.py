import json
from typing import Optional

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from attractions import forms, models
from market_review.views import upload_file


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


@staff_member_required
def attraction_image(request, attraction_id: int):
    attraction = get_object_or_404(models.Attraction, pk=attraction_id)

    if request.method == "GET":
        form = forms.AttractionImageForm()
    else:
        form = forms.AttractionImageForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            attraction.main_image = upload_file(
                form.cleaned_data["image"],
                attraction.main_image
            )

            attraction.save()

            # Done, redirect back to get rid of the post and show the image
            return redirect(
                attraction_image,
                attraction_id=attraction_id
            )

    return render(
        request,
        "attractions/attraction_image.html",
        {
            "attraction": attraction,
            "form": form,
            "category": "attractions"
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

    def to_json(attr):
        image = None

        if attr.main_image:
            image = attr.main_image.url

        return {
            "id": attr.pk,
            "name": attr.name,
            "image": image
        }

    return HttpResponse(
        json.dumps(list(map(to_json, category.attraction_set.all()))),
        content_type="application/json"
    )
