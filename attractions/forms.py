from django import forms


class CategoryImageForm(forms.Form):
    image = forms.ImageField()
