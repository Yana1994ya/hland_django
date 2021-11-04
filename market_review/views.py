from typing import Optional

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from market_review import forms, models

THUMB_WIDTH = 180


@staff_member_required
def upload_logo(request, app_id: str):
    application = get_object_or_404(models.Application, slug=app_id)

    if request.method == "GET":
        form = forms.ApplicationLogoForm()
    else:
        form = forms.ApplicationLogoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            application.logo = models.ImageAsset.upload_file(form.cleaned_data["logo"], application.logo)
            application.save()

            return redirect(
                "upload_logo",
                app_id=app_id
            )

    return render(
        request,
        "market_review/upload_logo.html",
        {
            "application": application,
            "form": form,
            "category": "market_review"
        }
    )


@staff_member_required
def feature_images(request, app_id, feature_slug):
    application = get_object_or_404(models.Application, slug=app_id)
    feature = get_object_or_404(application.notablefeature_set, slug=feature_slug)

    thumbs = []
    for image in models.FeatureImage.objects.filter(feature=feature):
        thumbs.append((
            image.caption,
            image.image.tall_thumb(THUMB_WIDTH)
        ))

    if request.method == "GET":
        form = forms.FeatureImageForm()
    else:
        form = forms.FeatureImageForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            image = models.FeatureImage(
                feature=feature,
                caption=form.cleaned_data["caption"],
                image=models.ImageAsset.upload_file(form.cleaned_data["image"], None)
            )
            image.save()

            # Done, redirect back to get rid of the post and show the image
            return redirect(
                "feature_images",
                app_id=app_id,
                feature_slug=feature_slug
            )

    return render(
        request,
        "market_review/feature_images.html",
        {
            "application": application,
            "feature": feature,
            "thumbs": thumbs,
            "form": form,
            "category": "market_review"
        }
    )


def application_page(request, app_id: Optional[str]):
    applications = list(models.Application.objects.select_related("logo").order_by('short_name'))
    application = None

    if app_id is None:
        application = applications[0]
    else:
        for app in applications:
            if app.slug == app_id:
                application = app
                break

    if application is None:
        raise Http404("application not found")

    return render(
        request,
        "market_review/application.html",
        {
            "application": application,
            "applications": applications,
            # "features": features.get_features(application.id),
            "missing": list(application.missingfeature_set.all()),
            "category": "market_review"
        }
    )


def summary(request):
    applications = list(models.Application.objects.order_by('short_name'))

    return render(
        request,
        "market_review/summary.html",
        {
            "applications": applications,
            "category": "market_review"
        }
    )
