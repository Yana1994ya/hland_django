import uuid

import boto3
from django.shortcuts import get_object_or_404, render
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
        "ContentType": image.content_type
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
            assert False, application.logo

    return render(
        request,
        "market_review/upload_logo.html",
        {
            "application": application,
            "form": form
        }
    )