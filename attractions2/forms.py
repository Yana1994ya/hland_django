import csv
import gzip
import io
import tempfile

from django import forms
from django.core.exceptions import ValidationError

from attractions2 import base_models
from attractions2 import models
from attractions2.trail import analyze_trail


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

    region = forms.ModelChoiceField(queryset=base_models.Region.objects)

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


class UserUploadImageForm(forms.Form):
    image = forms.ImageField(required=True)


class TagField(forms.ModelMultipleChoiceField):
    def __init__(self, query_set):
        super(TagField, self).__init__(
            query_set,
            widget=forms.CheckboxSelectMultiple,
            required=False
        )

    def label_from_instance(self, obj):
        return obj.name


class TrailForm(forms.Form):
    name = forms.CharField()

    difficulty = forms.ChoiceField(choices=[
        ("E", "easy"),
        ("M", "moderate"),
        ("H", "hard")
    ])

    owner = forms.ModelChoiceField(models.GoogleUser.objects.all())

    image = forms.ImageField(required=False)
    additional_image = forms.ImageField(required=False)

    coordinates = forms.FileField(required=False)

    length = forms.IntegerField(required=False, widget=forms.TextInput(attrs={
        "readonly": "readonly"
    }))

    elevation_gain = forms.IntegerField(required=False, widget=forms.TextInput(attrs={
        "readonly": "readonly"
    }))

    long = forms.FloatField(required=False, widget=forms.TextInput(attrs={
        "readonly": "readonly"
    }))

    lat = forms.FloatField(required=False, widget=forms.TextInput(attrs={
        "readonly": "readonly"
    }))

    suitabilities = TagField(
        models.TrailSuitability.objects.all()
    )
    activities = TagField(
        models.TrailActivity.objects.all(),
    )

    attractions = TagField(
        models.TrailAttraction.objects.all(),
    )

    def clean(self):
        data = super().clean()
        coordinates = data.get("coordinates")

        if coordinates is None:
            if "length" not in self.initial:
                self.add_error("coordinates", "New trail requires coordinates")

        if coordinates is not None:
            fh = io.TextIOWrapper(coordinates, encoding="utf-8")
            reader = csv.reader(fh)
            row = next(reader)
            lat_ind = row.index("Latitude")
            lon_ind = row.index("Longitude")
            elv_ind = row.index("Elevation")

            tmp = tempfile.TemporaryFile("w+b")
            with gzip.open(tmp, "wt", compresslevel=9) as gw:
                writer = csv.writer(gw)
                writer.writerow(["Latitude", "Longitude", "Altitude"])

                for row in reader:
                    writer.writerow([
                        row[lat_ind],
                        row[lon_ind],
                        row[elv_ind]
                    ])

            tmp.seek(0, io.SEEK_SET)

            analyze = analyze_trail(tmp)
            tmp.seek(0, io.SEEK_SET)

            data.update({
                "coordinates": tmp,
                "length": analyze.distance,
                "elevation_gain": analyze.elevation_gain,
                "long": analyze.center_longitude,
                "lat": analyze.center_latitude
            })
        return data
