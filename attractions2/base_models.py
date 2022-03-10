import io
from os import path
import tempfile
from typing import List, Optional
import uuid

from PIL import Image
import boto3
from django.conf import settings
import requests
from django.db import models
from django.contrib.contenttypes.models import ContentType


class ImageAsset(models.Model):
    bucket = models.CharField(max_length=250)
    key = models.CharField(max_length=250)
    size = models.PositiveBigIntegerField()
    request_width = models.PositiveIntegerField(null=True)
    request_height = models.PositiveIntegerField(null=True)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    parent = models.ForeignKey('ImageAsset', on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = [("bucket", "key"), ("parent_id", "request_width", "request_height")]

    def __str__(self):
        return f"s3://{self.bucket}/{self.key}"

    @property
    def to_json(self) -> dict:
        data = {
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "size": self.size
        }

        if self.parent is not None:
            data["parent"] = self.parent.to_json

        return data

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
                    "CacheControl": "public, max-age=2592000"
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
            "CacheControl": "public, max-age=2592000"
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
        cdn = settings.ASSETS.get("cdn")

        if cdn is not None:
            return f"https://{cdn}/{self.key}"
        else:
            return f"https://{self.bucket}.s3.amazonaws.com/{self.key}"


class Region(models.Model):
    name = models.CharField(max_length=25)

    image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date_modified = models.DateTimeField(auto_now=True)

    @property
    def to_json(self):
        res = self.to_short_json

        if self.image is None:
            res["image"] = None
        else:
            res["image"] = self.image.thumb_300().to_json

        return res

    @property
    def to_short_json(self):
        return {
            "id": self.id,
            "name": self.name
        }

    def __str__(self):
        return self.name


class Attraction(models.Model):
    name = models.CharField(max_length=250)

    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    main_image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    additional_images = models.ManyToManyField(
        ImageAsset,
        related_name="attraction_additional_image"
    )

    address = models.CharField(max_length=150)

    lat = models.FloatField()
    long = models.FloatField()

    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)

    date_modified = models.DateTimeField(auto_now=True)

    telephone = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)

    content_type = models.ForeignKey(
        ContentType,
        editable=False,
        null=True,
        on_delete=models.SET_NULL
    )

    def save(self, *args, **kwargs):
        if self.content_type is None:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(Attraction, self).save(*args, **kwargs)

    @classmethod
    def short_related(cls) -> List[str]:
        return ["region"]

    @classmethod
    def short_query(cls):
        return cls.objects \
            .defer("description", "website") \
            .select_related(*cls.short_related())

    @classmethod
    def favorite(cls, user_id: uuid.UUID):
        return cls.short_query() \
            .filter(favorite__user_id=user_id) \
            .order_by("-favorite__created")

    @classmethod
    def history(cls, user_id: uuid.UUID):
        return cls.short_query() \
            .filter(history__user_id=user_id) \
            .order_by("-history__last_visited")

    @classmethod
    def api_multiple_key(cls) -> str:
        raise NotImplementedError("api_multiple_key not implemented")

    @classmethod
    def api_single_key(cls) -> str:
        raise NotImplementedError("api_single_key not implemented")

    @classmethod
    def explore_filter(cls, qset, request):
        # https://hollyland.iywebs.cloudns.ph/attractions/api/museums?region_id=4
        if "region_id" in request.GET:
            qset = qset.filter(region_id__in=list(map(
                int,
                request.GET.getlist("region_id"),
            )))

        return qset

    @property
    def to_short_json(self):
        json_result = {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "long": self.long,
            "region": self.region.to_short_json,
            "address": self.address,
            "type": self.api_single_key(),
            "city": self.city,
            "telephone": self.telephone
        }

        if self.main_image is None:
            json_result["main_image"] = None
        else:
            json_result["main_image"] = self.main_image.thumb_600().to_json

        return json_result

    @property
    def to_json(self):
        json_result = self.to_short_json

        json_result.update({
            "description": self.description,
            "website": self.website,
        })

        if self.main_image is None:
            json_result["main_image"] = None
        else:
            json_result["main_image"] = self.main_image.landscape_thumb(900).to_json

        additional_images = []
        for image in self.additional_images.all():
            additional_images.append(image.landscape_thumb(900).to_json)

        json_result["additional_images"] = additional_images

        return json_result

    def __str__(self):
        return self.name


class AttractionFilter(models.Model):
    name = models.CharField(max_length=200)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return type(self).__name__ + ": " + self.name

    @property
    def to_json(self):
        return {
            "id": self.id,
            "name": self.name
        }

    @classmethod
    def api_multiple_key(cls) -> str:
        raise NotImplementedError("api_multiple_key not implemented")

    @classmethod
    def api_single_key(cls) -> str:
        raise NotImplementedError("api_single_key not implemented")

    class Meta:
        abstract = True
        ordering = ["name"]
