from urllib.parse import urlencode

from django.db import models


# Create your models here.
class Coupon(models.Model):
    code = models.CharField(max_length=24, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    used_date = models.DateTimeField(null=True, default=None)

    def barcode(self, size=150):
        return (
            "https://www.scandit.com/wp-content/themes/scandit/barcode-generator.php?"
            + urlencode(
                {
                    "symbology": "itf",
                    "value": str(self.code),
                    "size": str(size),
                    "ec": "L",
                }
            )
        )
