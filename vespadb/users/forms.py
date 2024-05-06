"""Forms voor VespaUser admin."""

from django import forms
from vespadb.observations.models import Province


class AssignProvinceForm(forms.Form):
    """Form om alle gemeenten in een provincie aan een gebruiker toe te wijzen."""

    province_name = forms.ModelChoiceField(
        queryset=Province.objects.all(), 
        label="Province name",
        help_text="Select a province"
    )
