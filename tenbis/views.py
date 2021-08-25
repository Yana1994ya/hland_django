from datetime import datetime
import json
import re
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import jwt

from tenbis import models

CODE_RE = re.compile("[0-9]{20}")


@csrf_exempt
def homepage(request):
    if request.method == "POST" and request.content_type == "application/json":
        data = json.loads(request.body.decode("utf-8"))
        code = CODE_RE.findall(data["all_data"])

        if code:
            instance, created = models.Coupon.objects.get_or_create(code=code[0])

            if created:
                instance.save()

            return HttpResponse("code added\n", content_type="text/plain")

    if not request.user.is_authenticated:
        return HttpResponseRedirect("/")

    coupon = list(models.Coupon.objects.filter(used=False).order_by("date")[0:1])
    print_url = None
    print_link = None
    barcode_image = None

    if coupon:
        coupon = coupon[0]

        token = jwt.encode(
            {"target": "print", "coupon_id": coupon.pk},
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        print_link = reverse("tenbis_print", kwargs={"token": token})

        print_url = "my.bluetoothprint.scheme://" + request.build_absolute_uri(print_link)
        barcode_image = (
                "https://www.scandit.com/wp-content/themes/scandit/barcode-generator.php?" +
                urlencode({
                    "symbology": "itf",
                    "value": str(coupon.code),
                    "size": "150",
                    "ec": "L"
                })
        )
    else:
        coupon = None

    return render(
        request,
        "10bis/display.html",
        {"coupon": coupon, "category": "10bis", "print_url": print_url, "print_link": print_link,
         "barcode_image": barcode_image},
    )


def mark_used(request, coupon_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/")

    if request.method == "POST":
        coupon = get_object_or_404(models.Coupon, pk=coupon_id)
        coupon.used = True
        coupon.used_date = datetime.now()

        coupon.save()

    return redirect("tenbis")


def show_print(request, token):
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded.get("target") == "print"
    coupon_id = decoded["coupon_id"]

    coupon = get_object_or_404(models.Coupon, pk=coupon_id)

    return HttpResponse(
        json.dumps({
            "0": {
                "type": 1,
                "path": (
                        "https://www.scandit.com/wp-content/themes/scandit/barcode-generator.php?" +
                        urlencode({
                            "symbology": "itf",
                            "value": str(coupon.code),
                            "size": "200",
                            "ec": "L"
                        })
                ),
                "align": 1
            },
            "1": {
                "type": 0,
                "content": str(coupon.code),
                "bold": 0,
                "align": 1,
                "format": 0
            }
        }),
        content_type="application/json"
    )
