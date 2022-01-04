from typing import NoReturn

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from attractions2 import forms, models
from attractions2.base_views import EditView
from attractions2.pager import Pager


@staff_member_required
def display(request, model, page_number: int):
    paginator = Paginator(model.objects.all().only("name").order_by("name"), 30)
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


class EditOffRoad(EditView):
    form_class = forms.OffRoadForm
    model = models.OffRoad

    def success_message(self, instance: models.OffRoad) -> str:
        return f"OffRoad trip {instance.name} was saved successfully"

    def get_initial(self, instance: models.OffRoad) -> dict:
        initial = super().get_initial(instance)

        if instance.id is not None:
            initial["trip_type"] = instance.trip_type

        return initial

    def update_instance(self, instance: models.OffRoad, cleaned_data: dict):
        super().update_instance(instance, cleaned_data)
        instance.trip_type = cleaned_data["trip_type"]

    @classmethod
    def template_name(cls) -> str:
        return "attractions/edit_offroad.html"
