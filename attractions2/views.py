from typing import Optional

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

# Create your views here.
from django.urls import reverse

from attractions2 import forms, models
from attractions2.base_views import EditView
from attractions2.pager import Pager


@staff_member_required
def museums(request, page_number: int):
    paginator = Paginator(models.Museum.objects.all(), 30)
    page = paginator.page(page_number)

    return render(
        request,
        "attractions/museums.html",
        {
            "page": page,
            "pager": Pager(page, museums)
        }
    )


class EditMuseum(EditView):
    template_name = "attractions/museum.html"
    id_argument = "museum_id"
    form_class = forms.MuseumForm

    def get_instance(self, pk: Optional[int]) -> models.Museum:
        if pk is None:
            return models.Museum()
        else:
            return models.Museum.objects.get(id=pk)

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

    def get_action(self, pk: Optional[int]) -> str:
        if pk is None:
            return reverse("add_museum")
        else:
            return reverse("edit_museum", kwargs={"museum_id": pk})

    def redirect_index(self):
        return redirect("museums")
