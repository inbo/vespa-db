"""Observation admin forms."""

from django import forms


class SendEmailForm(forms.Form):
    """Form for sending emails to observers."""

    subject = forms.CharField(max_length=255, initial="mail")
    message = forms.CharField(widget=forms.Textarea, initial="mail")
    resend = forms.BooleanField(
        required=False, label="Observers die al een email hebben gekregen opnieuw een email versturen?"
    )
