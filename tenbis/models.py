from django.db import models


# Create your models here.
class Coupon(models.Model):
    code = models.CharField(max_length=24, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
