import io
import logging
import tempfile
import uuid
from abc import ABC
from os import path
from typing import List, Optional, Set, Dict

import boto3
import requests
from PIL import Image
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

log = logging.getLogger(__name__)


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
        unique_together = [
            ("bucket", "key"),
            ("parent_id", "request_width", "request_height")
        ]

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

    @classmethod
    def resolve_thumbs(cls, image_ids: Set[int], thumb_size: int) -> Dict[int, "ImageAsset"]:
        images = {}

        if image_ids:
            for image in cls.objects.filter(
                    Q(
                        parent__id__in=image_ids,
                        request_width=thumb_size,
                        request_height=thumb_size,
                    ) | Q(
                        id__in=image_ids,
                        width__lte=thumb_size,
                        height__lte=thumb_size
                    )
            ).select_related("parent"):
                if image.parent_id is not None:
                    images[image.parent.id] = image
                else:
                    images[image.id] = image

            missing = image_ids - images.keys()

            log.info("%s images are missing thumbnails", len(missing))
            if missing:
                for image in cls.objects.filter(id__in=missing):
                    images[image.id] = image.landscape_thumb(thumb_size)
                    images[image.id].parent = image
        return images


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

    class Meta:
        abstract = True
        ordering = ["name"]


class Region(AttractionFilter):

    @classmethod
    def api_multiple_key(cls) -> str:
        return "regions"


class GoogleUser(models.Model):
    id = models.UUIDField(primary_key=True)
    # Identifier in google
    sub = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(blank=True, null=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    given_name = models.CharField(max_length=250, blank=True, null=True)
    family_name = models.CharField(max_length=250, blank=True, null=True)
    picture = models.CharField(max_length=250, blank=True, null=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Keep user anonymous by *not* updating name/given_name/email when logging in.
    anonymized = models.BooleanField()

    banned_until = models.DateTimeField(blank=True, null=True)

    @property
    def to_json(self):
        data = {
            "id": self.id,
            "name": self.name
        }

        if self.picture:
            data["picture"] = self.picture

        return data

    def __str__(self):
        return self.name


class Attraction(models.Model):
    name = models.CharField(max_length=250)

    main_image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    additional_images = models.ManyToManyField(
        ImageAsset,
        related_name="attraction_additional_image",
        blank=True
    )

    lat = models.FloatField()
    long = models.FloatField()

    date_modified = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(
        ContentType,
        editable=False,
        null=True,
        on_delete=models.SET_NULL
    )

    # Denormalized fields
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.content_type is None:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(Attraction, self).save(*args, **kwargs)

    @classmethod
    def short_related(cls) -> List[str]:
        raise NotImplementedError("short_related not implemented")

    @classmethod
    def short_query(cls):
        return cls.objects \
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
    def explore_filter(cls, query_set, request):
        raise NotImplementedError("explore_filter not implemented")

    @property
    def to_short_json(self):
        try:
            type_string = self.api_single_key()
        except NotImplementedError:
            # For generic attraction write type string based on the content type
            type_string = self.content_type.model_class().api_single_key()

        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "long": self.long,
            "type": type_string,
            # Transfer the rating as a string to avoid rounding errors
            "avg_rating": str(self.avg_rating),
            "rating_count": self.rating_count
        }

    @property
    def to_json(self):
        raise NotImplementedError("to_json not implemented")

    def __str__(self):
        return self.name


class ManagedAttraction(Attraction, ABC):
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    address = models.CharField(max_length=150)

    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)

    telephone = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)

    @classmethod
    def short_related(cls) -> List[str]:
        return ["region"]

    @classmethod
    def explore_filter(cls, query_set, request):
        # https://hollyland.iywebs.cloudns.ph/attractions/api/museums?region_id=4&region_id=2
        if "region_id" in request.GET:
            query_set = query_set.filter(region_id__in=list(map(
                int,
                request.GET.getlist("region_id"),
            )))
        # SELECT "attractions2_attraction".*
        # FROM "attractions2_winery"
        # INNER JOIN "attractions2_attraction" ON
        # ("attractions2_winery"."attraction_ptr_id" = "attractions2_attraction"."id")
        # WHERE "attractions2_winery"."region_id" IN (2, 3)
        # assert False, qset.query

        return query_set

    @classmethod
    def short_query(cls):
        return cls.objects \
            .defer("description", "website") \
            .select_related(*cls.short_related())

    @property
    def to_short_json(self):
        data = super(ManagedAttraction, self).to_short_json

        data.update({
            "region": self.region.to_json,
            "address": self.address,
            "city": self.city,
            "telephone": self.telephone,
        })

        return data

    @property
    def to_json(self):
        json_result = self.to_short_json

        json_result.update({
            "description": self.description,
            "website": self.website,
        })

        return json_result

    class Meta:
        abstract = True


class AttractionComment(models.Model):
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    user = models.ForeignKey(GoogleUser, on_delete=models.CASCADE)

    text = models.TextField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField()

    images = models.ManyToManyField(
        ImageAsset,
        related_name="attraction_comment_image"
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['attraction', '-created']),
        ]

    @property
    def to_json(self):
        return {
            "user": self.user.to_json,
            "rating": self.rating,
            "text": self.text,
            "created": self.created.isoformat("T")
        }

    @property
    def user_name(self) -> str:
        return self.user.name
