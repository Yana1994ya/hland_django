import boto3
from django.db import models
from django.conf import settings


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
    def url(self):
        s3 = boto3.client("s3", **settings.ASSETS["config"])
        return s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': self.key
            },
            ExpiresIn=3600
        )

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

    def __str__(self):
        return self.short_name
