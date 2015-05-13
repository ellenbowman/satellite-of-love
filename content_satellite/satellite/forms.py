from django import forms
from models import Service, Ticker

# https://docs.djangoproject.com/en/1.7/ref/forms/api/
# https://docs.djangoproject.com/en/1.7/ref/forms/fields/#django.forms.ModelMultipleChoiceField	

class FilterForm(forms.Form):
	tickers = forms.CharField(required=False)
	notes = forms.CharField(
		widget=forms.Textarea,
		required=False)
	services = forms.ModelMultipleChoiceField(
		widget=forms.SelectMultiple(),
		queryset=Service.objects.all().order_by('pretty_name'), 
		required=False)	
	
	