from django.db import models


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