"""Forms voor VespaUser admin."""

from django import forms

from vespadb.observations.models import Province


class AssignProvinceForm(forms.Form):
    """Form om alle gemeenten in een provincie aan een gebruiker toe te wijzen."""

    province_name = forms.ModelChoiceField(
        queryset=Province.objects.all(), label="Province name", help_text="Select a province"
    )


class LoginSerializer(forms.Form):
    """Serializer for user login view."""

    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=128, widget=forms.PasswordInput())

    def clean(self):
        """Validate the credentials."""
        from django.contrib.auth import authenticate

        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data["user"] = user
        return cleaned_data


class ChangePasswordSerializer(forms.Form):
    """Serializer for password change endpoint."""

    old_password = forms.CharField(required=True)
    new_password = forms.CharField(required=True)