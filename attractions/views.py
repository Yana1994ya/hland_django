import json
from typing import Optional

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from attractions import forms, models
from market_review.models import ImageAsset
from market_review.views import upload_file

# Create your views here.
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