from django import forms


class ApplicationLogoForm(forms.Form):
    logo = forms.ImageField()


class FeatureImageForm(forms.Form):
    image = forms.ImageField()
    caption = forms.CharField(max_length=250)