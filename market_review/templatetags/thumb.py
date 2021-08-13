import io
import tempfile
import uuid

import boto3
from django import template
from django.conf import settings

from market_review import models, features
import requests
from PIL import Image

register = template.Library()


def get_thumb(parent: features.ImageAsset, requested, thumb_size) -> models.ImageAsset:
    try:
        return models.ImageAsset.objects.get(parent_id=parent.id, **requested)
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
                "ACL": "public-read",
                "CacheControl": "public, max-age=86400"
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

            return thumb


@register.filter
def thumb_width(asset: features.ImageAsset, width: int):

    if width >= asset.width:
        return asset.url

    for thumb in asset.thumbs:
        if thumb.request_width == width:
            return thumb.url

    thumb = get_thumb(asset, {
        "request_width": width
    }, (width, width * 20))

    # Important append to the list of thumbs to avoid duplicating if reused
    asset.thumbs.append(features.ImageAsset(
        id=thumb.id,
        key=thumb.key,
        bucket=thumb.bucket,
        width=thumb.width,
        height=thumb.height,
        request_width=thumb.request_width,
        request_height=thumb.request_height,
        thumbs=[]
    ))

    return thumb.url
