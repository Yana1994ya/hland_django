import io
import tempfile
import uuid

import boto3
from django import template
from django.conf import settings

from market_review import models
import requests
from PIL import Image

register = template.Library()


def get_thumb(parent: models.ImageAsset, requested, thumb_size) -> models.ImageAsset:
    try:
        return parent.imageasset_set.get(**requested)
    except models.ImageAsset.DoesNotExist:
        im = Image.open(
            requests.get(parent.url, stream=True).raw
        )

        im.thumbnail(thumb_size, Image.BICUBIC)

        with tempfile.TemporaryFile(suffix=".png") as fh:
            im.save(fh, "PNG")
            fh.flush()
            size = fh.tell()
            fh.seek(0, io.SEEK_SET)

            s3 = boto3.client("s3", **settings.ASSETS["config"])

            key = settings.ASSETS["prefix"] + "images/" + str(uuid.uuid4()) + ".png"
            bucket = settings.ASSETS["bucket"]

            s3.upload_fileobj(fh, bucket, key, ExtraArgs={
                "ContentType": "image/png",
                "ACL": "public-read"
            })

            thumb = models.ImageAsset(
                bucket=bucket,
                key=key,
                size=size,
                width=im.width,
                height=im.height,
                parent=parent,
                **requested
            )
            thumb.save()


@register.filter
def thumb_width(asset: models.ImageAsset, width: int):

    if width >= asset.width:
        return asset.url
    else:
        return get_thumb(asset, {
            "request_width": width
        }, (width, width * 20)).url
