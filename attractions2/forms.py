from django import forms

from attractions2 import models


class BaseAttractionForm(forms.Form):
    name = forms.CharField()

    description = forms.CharField(required=False, widget=forms.Textarea())

    long = forms.FloatField(widget=forms.TextInput(attrs={
        "type": "number",
        "max": "36",
        "min": "33",
        "step": "0.0000001"
    }), min_value=33, max_value=36)

    lat = forms.FloatField(widget=forms.TextInput(attrs={
        "type": "number",
        "max": "34",
        "min": "26",
        "step": "0.0000001"
    }), min_value=26, max_value=34)

    image = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={"accept": "image/*"}
    ))

    additional_image = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={"accept": "image/*"}
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


class ManagedAttractionForm(BaseAttractionForm):
    address = forms.CharField()

    website = forms.URLField(widget=forms.TextInput(attrs={
        "type": "url"
    }), required=False)

    region = forms.ModelChoiceField(queryset=models.Region.objects)

    telephone = forms.RegexField(
        regex="^[0-9]{9,10}$"
    )

    city = forms.CharField()


class MuseumForm(ManagedAttractionForm):
    domain = forms.ModelChoiceField(queryset=models.MuseumDomain.objects)


class WineryForm(ManagedAttractionForm):
    pass


class ZooForm(ManagedAttractionForm):
    pass


class OffRoadForm(ManagedAttractionForm):
    trip_type = forms.ModelChoiceField(queryset=models.OffRoadTripType.objects)
