"""VespaDB Observations admin module."""

import json
import logging
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.contrib.gis import admin as gis_admin
from django.core.mail import send_mail
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.timezone import now
from rest_framework.test import APIRequestFactory

from vespadb.observations.filters import MunicipalityExcludeFilter, ProvinceFilter, ObserverReceivedEmailFilter
from vespadb.observations.forms import SendEmailForm
from vespadb.observations.models import Municipality, Observation, Province
from vespadb.observations.views import ObservationsViewSet

logger = logging.getLogger(__name__)


class FileImportForm(forms.Form):
    """Form for uploading JSON or CSV files."""

    file = forms.FileField()


class ObservationAdmin(gis_admin.GISModelAdmin):
    """Admin class for Observation model."""

    list_display = (
        "id",
        "wn_validation_status",
        "created_by",
        "observation_datetime",
        "province",
        "municipality",
        "nest_location",
        "nest_type",
        "nest_height",
        "nest_size",
        "eradication_date",
        "eradication_result",
        "eradicator_name",
        "reserved_by",
        "modified_by",
    )
    list_filter = (
        "observation_datetime",
        "eradication_date",
        "eradicator_name",
        "wn_validation_status",
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        ProvinceFilter,
        MunicipalityExcludeFilter,
        "municipality",
        "anb",
        "reserved_by",
        "created_by",
        "modified_by",
        ObserverReceivedEmailFilter
    )
    search_fields = ("id", "eradicator_name", "observer_name")
    filter_horizontal = ()
    ordering = ("-observation_datetime",)
    raw_id_fields = ("municipality", "province")
    actions = ["send_email_to_observers", "mark_as_eradicated", "mark_as_not_visible"]

    def changelist_view(self, request: HttpRequest, extra_context: Any = None) -> TemplateResponse:
        """
        Override the changelist view to add custom context.

        :param request: HttpRequest object
        :param extra_context: Additional context data
        :return: TemplateResponse object
        """
        extra_context = extra_context or {}
        extra_context["import_file_url"] = "import-file/"
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self) -> Any:
        """
        Get the custom URLs for the admin interface.

        :return: List of URLs
        """
        urls = super().get_urls()
        custom_urls = [
            path("import-file/", self.admin_site.admin_view(self.import_file), name="import_file"),
            path("bulk-import/", self.admin_site.admin_view(self.bulk_import_view), name="bulk_import"),
            path("send-email/", self.admin_site.admin_view(self.send_email_to_observers), name="send-email"),
        ]
        return custom_urls + urls

    def import_file(self, request: HttpRequest) -> HttpResponse:
        """
        Render the file import form and handle the form submission.

        :param request: HttpRequest object
        :return: HttpResponse object
        """
        if request.method == "POST":
            form = FileImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]
                file_name = file.name

                if file_name.endswith(".json"):
                    data = json.load(file)
                    request.data = {"data": data}
                    request.content_type = "application/json"
                elif file_name.endswith(".csv"):
                    request.data = {"file": file}
                    request.content_type = "multipart/form-data"
                else:
                    self.message_user(request, "Unsupported file format.", level="error")
                    return redirect("admin:observations_observation_changelist")

                return self.bulk_import_view(request)
        else:
            form = FileImportForm()
        return render(request, "admin/file_form.html", {"form": form})

    def bulk_import_view(self, request: HttpRequest) -> HttpResponse:
        """
        Handle the bulk import by calling the API endpoint.

        :param request: HttpRequest object
        :return: HttpResponse object
        """
        factory = APIRequestFactory()
        content_type = "json" if request.content_type == "application/json" else "multipart"
        api_request = factory.post("/observations/bulk_import/", data=request.data, format=content_type)
        api_request.user = request.user

        # Initialize the viewset with the new request
        viewset = ObservationsViewSet.as_view({"post": "bulk_import"})
        response = viewset(api_request)
        if response.status_code == 201:  # noqa: PLR2004
            self.message_user(request, "Observations imported successfully.")
        else:
            self.message_user(request, f"Failed to import observations: {response.data}", level="error")
        return redirect("admin:observations_observation_changelist")

    @admin.action(description="Verzend emails naar observatoren")
    def send_email_to_observers(
        self, request: HttpRequest, queryset: QuerySet[Observation]
    ) -> TemplateResponse | HttpResponse:
        """
        Send emails to the observers of the selected observations.

        :param request: HttpRequest object
        :param queryset: QuerySet of selected observations
        :return: TemplateResponse or HttpResponse object
        """
        if "apply" in request.POST:
            form = SendEmailForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data["subject"]
                message = form.cleaned_data["message"]
                resend = form.cleaned_data["resend"]

                success_list = []
                fail_list = []

                for observation in queryset:
                    if not observation.observer_email:
                        fail_list.append(observation.id)
                        continue
                    if observation.observer_received_email and not resend:
                        fail_list.append(observation.id)
                        continue
                    try:
                        send_mail(subject, message, "vespawatch@inbo.be", [observation.observer_email])
                        logger.info(f"Email sent to {observation.observer_email} for observation {observation.id}")
                        observation.observer_received_email = True
                        observation.save()
                        success_list.append(observation.id)
                    except Exception as e:
                        logger.exception(
                            f"Failed to send email to {observation.observer_email} for observation {observation.id}: {e}"
                        )
                        fail_list.append(observation.id)

                return TemplateResponse(
                    request,
                    "admin/send_email_result.html",
                    {
                        "success_list": success_list,
                        "fail_list": fail_list,
                    },
                )

        else:
            form = SendEmailForm()

        return render(request, "admin/send_email.html", {"observations": queryset, "form": form})

    @admin.action(description="Markeer observatie(s) als bestreden")
    def mark_as_eradicated(self, request: HttpRequest, queryset: Any) -> None:
        """
        Admin action to mark selected observations as eradicated.

        Parameters
        ----------
        - modeladmin (ModelAdmin): The current model admin instance.
        - request (HttpRequest): The current request object.
        - queryset (Any): The queryset of selected observations.

        Returns
        -------
        - None
        """
        count = queryset.update(eradication_date=now())
        self.message_user(request, f"{count} observations marked as eradicated.", messages.SUCCESS)

    @admin.action(description="Markeer observatie(s) als niet zichtbaar")
    def mark_as_not_visible(self, request: HttpRequest, queryset: Any) -> None:
        """
        Admin action to mark selected observations as not visible.

        Parameters
        ----------
        - request (HttpRequest): The current request object.
        - queryset (Any): The queryset of selected observations.

        Returns
        -------
        - None
        """
        count = queryset.update(visible=False)
        self.message_user(request, f"{count} observations marked as not visible.", messages.SUCCESS)


class ProvinceAdmin(admin.ModelAdmin):
    """Admin class for Province model."""

    list_display = ("id", "name")
    search_fields = ("name",)


class MunicipalityAdmin(admin.ModelAdmin):
    """Admin class for Municipality model."""

    list_display = ("id", "name", "province")
    list_filter = ("province",)
    search_fields = ("name",)


admin.site.register(Observation, ObservationAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
