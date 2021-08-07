from django import forms


class ApplicationLogoForm(forms.Form):
    logo = forms.ImageField()
