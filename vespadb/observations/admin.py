"""Vespa-DB Observations admin module."""

import json
import logging
from typing import Any

from django.utils import timezone
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin as gis_admin
from django.core.mail import send_mail
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry, Point
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework.test import APIRequestFactory
from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from vespadb.observations.models import Import
from django.urls import reverse
from django.utils.html import format_html

from vespadb.observations.filters import MunicipalityExcludeFilter, ObserverReceivedEmailFilter, ProvinceFilter
from vespadb.observations.forms import SendEmailForm
from vespadb.observations.models import Municipality, Observation, Province
from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates
from vespadb.observations.views import ObservationsViewSet
from vespadb.users.models import UserType
from vespadb.users.utils import get_import_user

logger = logging.getLogger(__name__)


class FileImportForm(forms.Form):
    """Form for uploading JSON or CSV files."""

    file = forms.FileField()


class NestStatusFilter(SimpleListFilter):
    """Custom filter for selecting multiple nest statuses in the admin panel."""

    title: str = _("Nest Status")
    parameter_name: str = "nest_status"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        """
        Return a list of tuples for the different nest statuses.

        :param request: The HTTP request object.
        :param model_admin: The current model admin instance.
        :return: A list of tuples containing the status values and labels.
        """
        return [
            ("eradicated", "Eradicated"),
            ("reserved", "Reserved"),
            ("open", "Open"),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        """
        Filter the queryset based on the selected nest statuses.

        :param request: The HTTP request object.
        :param queryset: The current queryset.
        :return: The filtered queryset based on the selected statuses, or the original queryset if no value is provided.
        """
        value = self.value()
        if not value:
            return queryset

        statuses = value.split(",")
        query = Q()

        if "eradicated" in statuses:
            query |= Q(eradication_date__isnull=False)
        if "reserved" in statuses:
            query |= Q(reserved_datetime__isnull=False)
        if "open" in statuses:
            query |= Q(reserved_datetime__isnull=True, eradication_date__isnull=True)

        return queryset.filter(query)


class ObservationAdminForm(forms.ModelForm):
    """Custom form for the Observation model."""

    class Meta:
        """Meta class for the ObservationAdminForm."""

        model = Observation
        fields = "__all__"
        widgets = {
            "eradication_date": forms.DateInput(attrs={"type": "date"}),
        }

class VisibilityFilter(SimpleListFilter):
    """Custom filter for observation visibility in the admin panel."""

    title = _("Zichtbaarheid")
    parameter_name = "visibility"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        """
        Return a list of tuples for the different visibility options.

        :param request: The HTTP request object.
        :param model_admin: The current model admin instance.
        :return: A list of tuples containing the visibility values and labels.
        """
        return [
            ("visible", "Zichtbare nesten"),
            ("not_visible", "Niet zichtbare nesten"),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        """
        Filter the queryset based on the selected visibility status.

        :param request: The HTTP request object.
        :param queryset: The current queryset.
        :return: The filtered queryset based on the selected visibility, or the original queryset if no value is provided.
        """
        value = self.value()
        if value == "visible":
            return queryset.filter(visible=True)
        elif value == "not_visible":
            return queryset.filter(visible=False)
        return queryset

class ObservationAdmin(gis_admin.GISModelAdmin):
    """Admin class for Observation model."""

    form = ObservationAdminForm

    list_display = (
        "id",
        "wn_id",
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
        "modified_datetime",
        "public_domain",
        "reserved_datetime",
        "visible",
    )
    
    list_filter = (
        "observation_datetime",
        "eradication_date",
        "eradicator_name",
        NestStatusFilter,
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        "public_domain",
        ProvinceFilter,
        MunicipalityExcludeFilter,
        "municipality",
        "anb",
        VisibilityFilter,
        "reserved_by",
        "modified_datetime",
        "modified_by",
        "created_by",
        "modified_by",
        ObserverReceivedEmailFilter,
    )
    search_fields = ("id", "wn_id", "eradicator_name", "observer_name")
    filter_horizontal = ()
    ordering = ("-observation_datetime",)
    raw_id_fields = ("municipality", "province")
    actions = ["send_email_to_observers", "mark_as_eradicated", "mark_as_not_visible"]

    readonly_fields = (
        "notes",
        "source",
        "wn_id",
        "wn_validation_status",
        "observer_name",
        "observer_phone_number",
        "created_datetime",
        "created_by",
        "wn_modified_datetime",
        "wn_created_datetime",
        "wn_cluster_id",
        "modified_by",
        "modified_datetime",
        "province",
        "anb",
        "municipality",
    )

    def get_readonly_fields(self, request: HttpRequest, obj: Observation | None = None) -> list[str]:
        """."""
        if obj:  # editing an existing object
            return [*self.readonly_fields, "location"]
        return list(self.readonly_fields)

    def save_model(self, request: HttpRequest, obj: Observation, form: Any, change: bool) -> None:
        """."""
        if not change:  # Creating a new object
            obj.created_by = request.user
            obj.created_datetime = now()

        obj.modified_by = request.user
        obj.modified_datetime = now()

        # Auto-edit based on location
        if obj.location:
            if not isinstance(obj.location, Point):
                obj.location = GEOSGeometry(obj.location, srid=4326)
            point = obj.location.transform(4326, clone=True)
            long, lat = point.x, point.y
            obj.anb = check_if_point_in_anb_area(long, lat)
            municipality = get_municipality_from_coordinates(long, lat)
            obj.municipality = municipality
            obj.province = municipality.province if municipality else None
        if not obj.source:
            obj.source = "Waarnemingen.be"

        super().save_model(request, obj, form, change)

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
            path("send-email/", self.admin_site.admin_view(self.send_email_view), name="send-email"),  # Correcte URL naam
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
                if Import.objects.filter(file_path__endswith=file_name, created_at__gte=timezone.now() - timezone.timedelta(hours=1)).exists():
                    self.message_user(request, f"File {file_name} was recently imported. Are you sure you want to import it again?", level="warning")

                if not (file_name.endswith(".json") or file_name.endswith(".csv")):
                    self.message_user(request, "Unsupported file format.", level="error")
                    return redirect("admin:observations_observation_changelist")

                if Import.objects.filter(file_path__endswith=file_name, created_at__gte=timezone.now() - timezone.timedelta(hours=1)).exists():
                    self.message_user(request, f"File {file_name} was recently imported. Are you sure you want to import it again?", level="warning")

                try:
                    factory = APIRequestFactory()
                    api_request = factory.post(
                        "/observations/async_bulk_import/",
                        data={"file": file},
                        format="multipart",
                    )
                    api_request.user = get_import_user(UserType.IMPORT)
                    viewset = ObservationsViewSet.as_view({"post": "async_bulk_import"})
                    response = viewset(api_request)

                    if response.status_code == 202:
                        data = response.data
                        import_id = data["import_id"]
                        detail_url = reverse("admin:observations_import_change", args=[import_id])
                        status_url = reverse("admin:import_status")
                        self.message_user(
                            request,
                            format_html(
                                'Import job initiated. Import ID: <a href="{}">{}</a>. '
                                'Check <a href="{}">status page</a> for progress.',
                                detail_url, import_id, status_url
                            ),
                            level="success",
                        )
                    else:
                        self.message_user(request, f"Failed to initiate import: {response.data}", level="error")
                except Exception as e:
                    self.message_user(request, f"Error initiating import: {str(e)}", level="error")
                    logger.exception(f"Import error: {str(e)}")

                return redirect("admin:observations_observation_changelist")
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
        api_request.user = get_import_user(UserType.IMPORT)  # Use import user

        # Call the API endpoint
        viewset = ObservationsViewSet.as_view({"post": "bulk_import"})
        response = viewset(api_request)

        # On success (create or update), show meaningful messages
        if response.status_code in (200, 201):
            data = response.data
            created = data.get("created_ids", [])
            updated = data.get("updated_ids", [])

            if created:
                messages.success(
                    request,
                    f"Created new observation{'s' if len(created) > 1 else ''} with ID"
                    f"{'s' if len(created) > 1 else ''}: {', '.join(map(str, created))}."
                )
            if updated:
                if len(updated) == 1:
                    messages.success(
                        request,
                        f"Observation with ID {updated[0]} already exists; update successful."
                    )
                else:
                    messages.success(
                        request,
                        f"Updated existing observations with IDs: {', '.join(map(str, updated))}."
                    )
            if not created and not updated:
                messages.info(request, "No observations were created or updated.")
        else:
            # On error, display the error details
            messages.error(request, f"Failed to import observations: {response.data}")

        return redirect("admin:observations_observation_changelist")
    
    def send_email_view(self, request: HttpRequest) -> HttpResponse:
        """View to display the form and send emails."""
        if request.method == 'POST':
            form = SendEmailForm(request.POST)
            if form.is_valid():
                subject = form.cleaned_data["subject"]
                message = form.cleaned_data["message"]
                resend = form.cleaned_data["resend"]

                selected_observations = request.session.get('selected_observations', [])
                queryset = Observation.objects.filter(pk__in=selected_observations)

                success_list = []
                fail_list = []

                for observation in queryset:
                    if not observation.observer_email:
                        logger.warning(f"Observation {observation.id} has no observer email.")
                        fail_list.append(observation.id)
                        continue
                    if observation.observer_received_email and not resend:
                        logger.warning(f"Observation {observation.id} already received an email.")
                        fail_list.append(observation.id)
                        continue
                    try:
                        send_mail(subject, message, from_email=settings.DEFAULT_FROM_EMAIL,recipient_list=[observation.observer_email])
                        logger.debug(f"Email sent to {observation.observer_email} for observation {observation.id}")
                        observation.observer_received_email = True
                        observation.save()
                        success_list.append(observation.id)
                    except Exception as e:
                        logger.exception(f"Failed to send email to {observation.observer_email} for observation {observation.id}: {e}")
                        fail_list.append(observation.id)

                if success_list:
                    messages.success(request, f"Emails successfully sent to {len(success_list)} observers.")
                if fail_list:
                    messages.warning(request, f"Failed to send emails for {len(fail_list)} observations.")

                return redirect('admin:observations_observation_changelist')
        else:
            form = SendEmailForm()

        return render(request, 'admin/send_email.html', {'form': form})

    @admin.action(description="Verzend emails naar observatoren")
    def send_email_to_observers(self, request: HttpRequest, queryset: QuerySet[Observation]) -> HttpResponse:
        """
        Action to prepare sending emails.
        """
        # Sla de geselecteerde observaties op in de sessie
        request.session['selected_observations'] = list(queryset.values_list('pk', flat=True))
        
        # Redirect naar de juiste naam van de custom URL
        return redirect('admin:send-email')

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

@admin.register(Import)
class ImportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "status",
        "progress",
        "created_at",
        "completed_at",
        "user",
        "created_count",
        "updated_count",
        "error_message_summary",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "error_message"]
    readonly_fields = [
        "id",
        "file_path",
        "status",
        "progress",
        "created_at",
        "completed_at",
        "user",
        "error_message",
        "task_id",
        "created_ids",
        "updated_ids",
    ]

    def created_count(self, obj):
        """Display the number of created observations."""
        return len(obj.created_ids)
    created_count.short_description = "Created Observations"

    def updated_count(self, obj):
        """Display the number of updated observations."""
        return len(obj.updated_ids)
    updated_count.short_description = "Updated Observations"

    def error_message_summary(self, obj):
        """Display a truncated error message in the list view."""
        return obj.error_message[:100] + "..." if obj.error_message and len(obj.error_message) > 100 else obj.error_message
    error_message_summary.short_description = "Error Message"

    def get_urls(self):
        """Add a custom URL for the import status page."""
        urls = super().get_urls()
        custom_urls = [
            path("status/", self.admin_site.admin_view(self.import_status_view), name="import_status"),
        ]
        return custom_urls + urls

    def import_status_view(self, request):
        """Display a custom page with recent import statuses."""
        imports = Import.objects.all().order_by("-created_at")[:10]
        context = {
            "imports": imports,
            "title": "Recent Imports",
        }
        return render(request, "admin/import_status.html", context)
    
admin.site.register(Observation, ObservationAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
