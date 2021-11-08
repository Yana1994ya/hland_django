from django import forms

from attractions2 import models


class BaseAttractionForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))

    description = forms.CharField(widget=forms.Textarea(attrs={
        "class": "form-control"
    }), required=False)

    address = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))

    website = forms.URLField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "type": "url"
    }), required=False)

    long = forms.FloatField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "type": "number",
        "max": "36",
        "min": "33",
        "step": "0.0000001"
    }), min_value=33, max_value=36)

    lat = forms.FloatField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "type": "number",
        "max": "34",
        "min": "26",
        "step": "0.0000001"
    }), min_value=26, max_value=34)

    image = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={
            "class": "form-control",
            "accept": "image/*"
        }
    ))

    additional_image = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={
            "class": "form-control",
            "accept": "image/*"
        }
    ))

    region = forms.ModelChoiceField(queryset=models.Region.objects, widget=forms.Select(
        attrs={
            "class": "form-control"
        }
    ))

    def clean_name(self):
        data = self.cleaned_data["name"]

        if data is not None:
            data = data \
                .replace("\u2013", "") \
                .replace("\t", " ") \
                .strip()

            while "  " in data:
                data = data.replace("  ", " ")

        return data

    def clean_address(self):
        data = self.cleaned_data["address"]

        if data is not None:
            data = data \
                .replace("\u2013", "") \
                .replace("\t", " ") \
                .strip()

            while "  " in data:
                data = data.replace("  ", " ")

        return data

    def clean_description(self):
        data = self.cleaned_data["description"]

        if data is not None:
            data = data \
                .replace("\u8203", "") \
                .replace("\u200b", "") \
                .replace("\u2013", "-") \
                .replace("\u2019", "'") \
                .replace("\r", "") \
                .strip()

            while "\n\n\n" in data:
                data = data.replace("\n\n\n", "\n\n")

            data = "\n".join(
                map(
                    str.rstrip,
                    data.split("\n")
                )
            )

        return data


class MuseumForm(BaseAttractionForm):
    domain = forms.ModelChoiceField(queryset=models.MuseumDomain.objects, widget=forms.Select(
        attrs={
            "class": "form-control"
        }
    ))
