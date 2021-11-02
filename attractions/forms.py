from django import forms

from attractions import models


class CategoryImageForm(forms.Form):
    image = forms.ImageField()


def attraction_types():
    result = []

    for category in models.Category.objects.filter(parent_id=6):
        result.append((category.id, category.name))

    return result


def regions():
    result = []

    for category in models.Category.objects.filter(parent_id=1):
        result.append((category.id, category.name))

    return result


class AttractionImageForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))

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

    attraction_type = forms.ChoiceField(choices=attraction_types(), widget=forms.Select(
        attrs={
            "class": "form-control"
        }
    ))

    region = forms.ChoiceField(choices=regions(), widget=forms.Select(
        attrs={
            "class": "form-control"
        }
    ))

