import io
import tempfile

from PIL import Image
import boto3
from django.conf import settings
import requests

from market_review import models


def create_thumb(url: str, parent_id: int, requested, thumb_size) -> models.ImageAsset:
    try:
        return models.ImageAsset.objects.get(parent_id=parent_id, **requested)
    except models.ImageAsset.DoesNotExist:
        im = Image.open(
            requests.get(url, stream=True).raw
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
                parent_id=parent_id,
                **requested
            )
            thumb.save()

            return thumb
