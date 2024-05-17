"""VespaDB Observations admin module."""

from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path
from rest_framework.test import APIRequestFactory

from vespadb.observations.models import Observation
from vespadb.observations.views import ObservationsViewSet


class FileImportForm(forms.Form):
    """Form for uploading JSON or CSV files."""

    file = forms.FileField()


class ObservationAdmin(gis_admin.GISModelAdmin):
    """Admin class for Observation model."""

    list_display = (
        "id",
        "observation_datetime",
        "eradication_datetime",
        "eradicator_name",
        "wn_validation_status",
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        "municipality",
        "province",
        "reserved_by",
        "created_by",
        "modified_by",
    )
    list_filter = (
        "observation_datetime",
        "eradication_datetime",
        "eradicator_name",
        "wn_validation_status",
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        "municipality",
        "province",
        "reserved_by",
        "created_by",
        "modified_by",
    )
    search_fields = ("id", "eradicator_name", "observer_name")
    filter_horizontal = ()
    ordering = ("-observation_datetime",)
    raw_id_fields = ("municipality", "province")

    def changelist_view(self, request: HttpRequest, extra_context: Any = None) -> TemplateResponse:
        """
        Override the changelist view to add custom context.

        Args:
            request (HttpRequest): The HTTP request object.
            extra_context (Any): Additional context data.

        Returns
        -------
            TemplateResponse: The template response object.
        """
        extra_context = extra_context or {}
        extra_context["import_file_url"] = "import-file/"
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self) -> Any:
        """
        Get the custom URLs for the admin interface.

        Returns
        -------
            List[Any]: List of URL patterns.
        """
        urls = super().get_urls()
        custom_urls = [
            path("import-file/", self.admin_site.admin_view(self.import_file), name="import_file"),
            path(
                "bulk-import/", self.admin_site.admin_view(self.bulk_import_view), name="bulk_import"
            ),  # Add this line
        ]
        return custom_urls + urls

    def import_file(self, request: HttpRequest) -> HttpResponse:
        """
        Render the file import form and handle the form submission.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns
        -------
            HttpResponse: The HTTP response object.
        """
        if request.method == "POST":
            form = FileImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data["file"]

                # Redirect to the bulk import view with the file
                request.session["file"] = file
                return self.bulk_import_view(request)
        else:
            form = FileImportForm()
        return render(request, "admin/file_form.html", {"form": form})

    def bulk_import_view(self, request: HttpRequest) -> HttpResponse:
        """
        Handle the bulk import by calling the API endpoint.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns
        -------
            HttpResponse: The HTTP response object.
        """
        file = request.session.pop("file", None)
        if file:
            factory = APIRequestFactory()
            request_copy = factory.post("/observations/bulk_import/", {"file": file}, format="multipart")
            request_copy.user = request.user

            # Initialize the viewset with the new request
            viewset = ObservationsViewSet.as_view({"post": "bulk_import"})
            response = viewset(request_copy)
            if response.status_code == 201:  # noqa: PLR2004
                self.message_user(request, "Observations imported successfully.")
            else:
                self.message_user(request, f"Failed to import observations: {response.data}", level="error")
            return redirect("admin:observations_observation_changelist")
        return redirect("admin:observations_observation_changelist")


admin.site.register(Observation, ObservationAdmin)
