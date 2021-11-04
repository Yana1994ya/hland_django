import io
from os import path
import tempfile
from typing import Optional
import uuid

from PIL import Image
import boto3
from django.conf import settings
from django.db import models
import requests


class ImageAsset(models.Model):
    bucket = models.CharField(max_length=250)
    key = models.CharField(max_length=250)
    size = models.PositiveBigIntegerField()
    request_width = models.PositiveIntegerField(null=True)
    request_height = models.PositiveIntegerField(null=True)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    parent = models.ForeignKey('ImageAsset', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = [("bucket", "key")]

    def __str__(self):
        return f"s3://{self.bucket}/{self.key}"

    @property
    def to_json(self) -> dict:
        return {
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "size": self.size
        }

    def landscape_thumb(self, width: int) -> 'ImageAsset':
        if width > self.width:
            return self

        return self._create_thumb(
            requested={
                "request_width": width,
                "request_height": width
            },
            thumb_size=(width, width)
        )

    def tall_thumb(self, width: int) -> 'ImageAsset':
        if width > self.width:
            return self

        return self._create_thumb(
            requested={
                "request_width": width,
                "request_height": width * 20
            },
            thumb_size=(width, width * 20)
        )

    def thumb_600(self) -> 'ImageAsset':
        return self.landscape_thumb(600)

    def thumb_300(self) -> 'ImageAsset':
        return self.landscape_thumb(300)

    def _create_thumb(self, requested, thumb_size) -> 'ImageAsset':
        if self.parent_id is not None:
            raise Exception("thumb creation is only possible on the original image")

        try:
            return ImageAsset.objects.get(parent_id=self.id, **requested)
        except ImageAsset.DoesNotExist:
            im = Image.open(
                requests.get(self.url, stream=True).raw
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

                thumb = ImageAsset(
                    bucket=bucket,
                    key=key,
                    size=size,
                    width=im.width,
                    height=im.height,
                    parent_id=self.id,
                    **requested
                )

                thumb.save()

                return thumb

    def delete(self, *args, **kwargs):
        s3 = boto3.client("s3", **settings.ASSETS["config"])

        s3.delete_object(
            Bucket=self.bucket,
            Key=self.key
        )

        return super(ImageAsset, self).delete(*args, **kwargs)

    @staticmethod
    def upload_file(image, old_asset: Optional['ImageAsset']) -> 'ImageAsset':
        s3 = boto3.client("s3", **settings.ASSETS["config"])

        if old_asset is not None:
            old_asset.delete()

        _, ext = path.splitext(image.name)
        key = settings.ASSETS["prefix"] + "images/" + str(uuid.uuid4()) + ext
        bucket = settings.ASSETS["bucket"]

        width, height = image.image.size

        s3.upload_fileobj(image.file, bucket, key, ExtraArgs={
            "ContentType": image.content_type,
            "ACL": "public-read",
            "CacheControl": "public, max-age=86400"
        })

        asset = ImageAsset(
            bucket=bucket,
            key=key,
            size=image.size,
            width=width,
            height=height
        )

        asset.save()

        return asset

    @property
    def url(self):
        return f"https://{self.bucket}.s3.amazonaws.com/{self.key}"


# Create your models here.
class Application(models.Model):
    short_name = models.CharField(max_length=250)
    long_name = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)
    text = models.TextField()
    logo = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    @property
    def features(self):
        return self.notablefeature_set.prefetch_related(
            "featureimage_set",
            "featureimage_set__image",
            "featureimage_set__image__imageasset_set"
        )

    def __str__(self) -> str:
        return self.short_name


class NotableFeature(models.Model):
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=250)
    slug = models.SlugField()
    text = models.TextField()
    images = models.ManyToManyField(ImageAsset, through='FeatureImage')

    class Meta:
        unique_together = [("app", "slug")]

    def __str__(self):
        return f"{self.app.short_name}: {self.title}"


class FeatureImage(models.Model):
    feature = models.ForeignKey(NotableFeature, on_delete=models.CASCADE)
    caption = models.CharField(max_length=250)
    image = models.ForeignKey(ImageAsset, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("feature", "image")]


class MissingFeature(models.Model):
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE
    )

    slug = models.SlugField()
    title = models.CharField(max_length=250)
    text = models.TextField()

    class Meta:
        unique_together = [("app", "slug")]

    def __str__(self):
        return f"{self.app.short_name}: {self.title}"