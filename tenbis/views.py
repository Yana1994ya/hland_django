from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import re
from tenbis import models

CODE_RE = re.compile("[0-9]{20}")


@csrf_exempt
def homepage(request):
    if request.method == "POST" and request.content_type == "text/plain":
        data = request.body.decode("utf-8")
        code = CODE_RE.findall(data)

        if code:
            instance, created = models.Coupon.objects.get_or_create(code=code[0])

            if created:
                instance.save()

            return HttpResponse("code added\n", content_type='text/plain')

    return HttpResponse("unsupported\n", content_type='text/plain')
