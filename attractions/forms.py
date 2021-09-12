from django import forms


class CategoryImageForm(forms.Form):
    image = forms.ImageField()


class AttractionImageForm(forms.Form):
    image = forms.ImageField()
