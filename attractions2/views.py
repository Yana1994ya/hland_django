from typing import NoReturn

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from attractions2 import forms, models
from attractions2.base_views import EditView
from attractions2.pager import Pager


@staff_member_required
def display(request, model, page_number: int):
    paginator = Paginator(model.objects.all().order_by("name"), 30)
    page = paginator.page(page_number)

    return render(
        request,
        f"attractions/{model.api_multiple_key()}.html",
        {
            "page": page,
            "pager": Pager(page, model, display)
        }
    )


@staff_member_required
def homepage(request):
    return render(
        request,
        "attractions/homepage.html"
    )


class EditMuseum(EditView):
    form_class = forms.MuseumForm
    model = models.Museum

    def success_message(self, instance: models.Museum) -> str:
        return f"Museum {instance.name} was saved successfully"

    def get_initial(self, instance: models.Museum) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["domain"] = instance.domain

        return initial

    def update_instance(self, instance: models.Museum, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.domain = cleaned_data["domain"]


class EditWinery(EditView):
    form_class = forms.WineryForm
    model = models.Winery

    def success_message(self, instance: models.Winery) -> str:
        return f"Winery {instance.name} was saved successfully"


class EditZoo(EditView):
    form_class = forms.ZooForm
    model = models.Zoo

    def success_message(self, instance: models.Zoo) -> str:
        return f"Zoo {instance.name} was saved successfully"


class EditTrail(EditView):
    form_class = forms.TrailForm
    model = models.Trail

    def success_message(self, instance: models.Trail) -> str:
        return f"Trail {instance.name} was saved successfully"

    def get_initial(self, instance: models.Trail) -> dict:
        initial = super().get_initial(instance)

        if instance:
            initial.update({
                "difficulty": instance.difficulty,
                "length": instance.length,
                "elv_gain": instance.elv_gain
            })

        return initial

    def update_instance(self, instance: models.Trail, cleaned_data: dict) -> NoReturn:
        super().update_instance(instance, cleaned_data)

        instance.difficulty = cleaned_data["difficulty"]
        instance.length = cleaned_data["length"]
        instance.elv_gain = cleaned_data["elv_gain"]
        # If trail has no attribution, attribute it to yana.
        if instance.owner_id is None:
            instance.owner = models.GoogleUser.objects.get(
                pk="ac2d93aa-c627-5ffd-805e-d01191f28b44")
