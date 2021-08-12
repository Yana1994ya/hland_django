import uuid

import boto3
from django.shortcuts import get_object_or_404, redirect, render
from market_review import models, forms
from django.conf import settings
from os import path


def upload_file(image, old_asset):
    s3 = boto3.client("s3", **settings.ASSETS["config"])

    if old_asset is not None:
        s3.delete_object(
            Bucket=old_asset.bucket,
            Key=old_asset.key
        )
        old_asset.delete()

    _, ext = path.splitext(image.name)
    key = settings.ASSETS["prefix"] + "images/" + str(uuid.uuid4()) + ext
    bucket = settings.ASSETS["bucket"]

    height, width = image.image.size

    s3.upload_fileobj(image.file, bucket, key, ExtraArgs={
        "ContentType": image.content_type,
        "ACL": "public-read",
        "CacheControl": "public, max-age=86400"
    })

    asset = models.ImageAsset(
        bucket=bucket,
        key=key,
        size=image.size,
        width=width,
        height=height
    )
    asset.save()

    return asset


# Create your views here.
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
            application.logo = upload_file(form.cleaned_data["logo"], application.logo)
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


def feature_images(request, app_id, feature_slug):
    application = get_object_or_404(models.Application, slug=app_id)
    feature = get_object_or_404(application.notablefeature_set, slug=feature_slug)

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
                image=upload_file(form.cleaned_data["image"], None)
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
            "form": form,
            "category": "market_review"
        }
    )


def application_page(request, app_id):
    application = get_object_or_404(models.Application, slug=app_id)
    applications = list(models.Application.objects.order_by('short_name'))

    return render(
        request,
        "market_review/application.html",
        {
            "application": application,
            "applications": applications,
            "category": "market_review"
        }
    )


def home(request):
    applications = list(models.Application.objects.order_by('short_name'))
    application = applications[0]

    return render(
        request,
        "market_review/application.html",
        {
            "application": application,
            "applications": applications,
            "category": "market_review"
        }
    )
