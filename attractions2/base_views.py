import abc
from typing import NoReturn, Optional

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from attractions2 import models
from attractions2.forms import BaseAttractionForm


class EditView(View, abc.ABC):
    form_class = BaseAttractionForm
    model = models.Attraction

    @classmethod
    def id_argument(cls) -> str:
        return cls.model.api_single_key() + "_id"

    @classmethod
    def get_id(cls, kwargs: dict) -> int:
        return kwargs[cls.id_argument()]

    @classmethod
    def get_instance(cls, pk: Optional[int]) -> models.Attraction:
        if pk is None:
            return cls.model()
        else:
            return cls.model.objects.get(id=pk)

    @classmethod
    def get_action(cls, pk: Optional[int]) -> str:
        if pk is None:
            return reverse(f"add_{cls.model.api_single_key()}")
        else:
            return reverse(f"edit_{cls.model.api_single_key()}", kwargs={cls.id_argument(): pk})

    @classmethod
    def template_name(cls) -> str:
        return f"attractions/{cls.model.api_single_key()}.html"

    @classmethod
    def redirect_index(cls):
        return redirect(cls.model.api_multiple_key())

    def get_initial(self, instance: models.Attraction) -> dict:
        if instance.id is None:
            return {}
        else:
            return {
                "name": instance.name,
                "description": instance.description,
                "website": instance.website,
                "lat": instance.lat,
                "long": instance.long,
                "region": instance.region,
                "address": instance.address,
                "suitability": instance.suitability.all()
            }

    @abc.abstractmethod
    def success_message(self, instance: models.Attraction) -> str:
        raise NotImplementedError("success_message is not implemented")

    def update_instance(self, instance: models.Attraction, cleaned_data: dict) -> NoReturn:
        instance.name = cleaned_data["name"]
        instance.description = cleaned_data["description"]
        instance.website = cleaned_data["website"]
        instance.lat = cleaned_data["lat"]
        instance.long = cleaned_data["long"]
        instance.region = cleaned_data["region"]
        instance.address = cleaned_data["address"]

        if cleaned_data["image"]:
            instance.main_image = models.ImageAsset.upload_file(
                cleaned_data["image"],
                old_asset=instance.main_image
            )

    def handle_m2m(self, instance: models.Attraction, cleaned_data: dict) -> NoReturn:
        instance.suitability.set(cleaned_data["suitability"])

    def get(self, request, **kwargs):
        pk = self.get_id(kwargs)
        instance = self.get_instance(pk)
        initial = self.get_initial(instance)

        form = self.form_class(initial=initial)

        return render(
            request,
            self.template_name(),
            {
                "create": pk is None,
                "instance": instance,
                "form": form,
                "action": self.get_action(pk)
            }
        )

    def post(self, request, **kwargs):
        pk = self.get_id(kwargs)
        instance = self.get_instance(pk)

        form = self.form_class(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            self.update_instance(instance, form.cleaned_data)
            instance.save()

            if form.cleaned_data["additional_image"]:
                instance.additional_images.add(models.ImageAsset.upload_file(
                    form.cleaned_data["additional_image"],
                    old_asset=None
                ))

            # Delete any additional image chosen for delete
            for additional_id in request.POST.getlist("delete_additional"):
                additional = instance.additional_images.get(pk=int(additional_id))
                instance.additional_images.remove(additional)

                additional.delete()

            self.handle_m2m(instance, form.cleaned_data)

            # Done, redirect back to get rid of the post and show the image
            messages.add_message(request, messages.INFO, self.success_message(instance))

            if request.POST.get("next") == "exit":
                return self.redirect_index()
            else:
                return HttpResponseRedirect(self.get_action(instance.id))

        return render(
            request,
            self.template_name(),
            {
                "create": pk is None,
                "instance": instance,
                "form": form,
                "action": self.get_action(pk)
            }
        )
