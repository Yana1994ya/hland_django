from django import forms


class MultipleSearchForm(forms.Form):
    count = forms.IntegerField(min_value=1, max_value=10)
