from datetime import datetime, timezone
import json
import re
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import jwt

from tenbis import models
from tenbis.forms import MultipleSearchForm
from tenbis.btprint import BluetoothPrint

CODE_RE = re.compile("[0-9]{20}")


@csrf_exempt
@login_required
def homepage(request):
    if request.method == "POST" and request.content_type == "application/json":
        data = json.loads(request.body.decode("utf-8"))
        code = CODE_RE.findall(data["all_data"])

        if code:
            instance, created = models.Coupon.objects.get_or_create(code=code[0])

            if created:
                instance.save()

            return HttpResponse("code added\n", content_type="text/plain")

    coupon = list(models.Coupon.objects.filter(used=False).order_by("date")[0:1])
    print_url = None
    print_link = None
    barcode_image = None
    form = None

    if coupon:
        coupon = coupon[0]

        if request.POST:
            form = MultipleSearchForm(request.POST)

            if form.is_valid():
                coupon_list = []
                cnt = form.cleaned_data["count"]

                coupons = models.Coupon.objects.filter(used=False).order_by("date")[
                    0:cnt
                ]

                for coupon in coupons:
                    coupon_list.append(coupon.pk)

                token = jwt.encode(
                    {"target": "show", "coupons": coupon_list},
                    settings.SECRET_KEY,
                    algorithm="HS256",
                )

                return redirect("tenbis_multiple", token=token)
        else:
            form = MultipleSearchForm()
    else:
        coupon = None

    return render(
        request,
        "10bis/display.html",
        {
            "coupon": coupon,
            "category": "10bis",
            "barcode_image": barcode_image,
            "form": form,
        },
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
        json.dumps(
            {
                "0": {
                    "type": 1,
                    "path": (
                        "https://www.scandit.com/wp-content/themes/scandit/barcode-generator.php?"
                        + urlencode(
                            {
                                "symbology": "itf",
                                "value": str(coupon.code),
                                "size": "200",
                                "ec": "L",
                            }
                        )
                    ),
                    "align": 1,
                },
                "1": {
                    "type": 0,
                    "content": str(coupon.code),
                    "bold": 0,
                    "align": 1,
                    "format": 0,
                },
            }
        ),
        content_type="application/json",
    )


def show_multiple(request, token):
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded.get("target") == "show"
    coupons = list(models.Coupon.objects.filter(pk__in=decoded["coupons"], used=False))

    if request.method == "POST":
        if request.POST.get("sure") == "yes":
            for coupon in coupons:
                coupon.used = True
                coupon.used_date = datetime.now(timezone.utc)
                coupon.save()

        return redirect("tenbis")

    count = len(coupons)

    print_link = reverse("tenbis_multiple_print", kwargs={"token": token})

    print_url = "my.bluetoothprint.scheme://" + request.build_absolute_uri(
        print_link
    )

    return render(
        request,
        "10bis/multiple.html",
        {
            "coupons": coupons,
            "category": "10bis",
            "token": token,
            "count": count,
            "print_url": print_url
        },
    )


def print_multiple(request, token):
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded.get("target") == "show"
    coupons = list(models.Coupon.objects.filter(pk__in=decoded["coupons"], used=False))

    printer = BluetoothPrint()
    printer.add_text("found {} coupons".format(len(coupons)))

    for coupon in coupons:
        printer.add_text("------------")
        printer.add_text(coupon.date.replace(microsecond=0).isoformat().replace('+00:00', 'Z'))
        printer.add_barcode(coupon.code)
        printer.add_text(coupon.code)

    return printer.response()


