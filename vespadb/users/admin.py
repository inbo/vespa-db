"""Vespawatch admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from typing import Any, Iterable, List
from vespadb.observations.models import Province, Municipality
from vespadb.users.models import VespaUser
from vespadb.users.forms import AssignProvinceForm


@admin.register(VespaUser)
class VespaUserAdmin(UserAdmin):
    """Admin class voor het VespaUser model."""

    model = VespaUser
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            _("Custom Fields"),
            {
                "fields": (
                    "user_type",
                    "personal_data_access",
                    "municipalities",
                )
            },
        ),
    )
    filter_horizontal = ("municipalities",)

    actions = ["assign_province_municipalities"]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "personal_data_access",
        "reservation_count",
    )
    search_fields = ("username", "email", "first_name", "last_name")

    def get_urls(self) -> List[str]:
        """Voeg aangepaste URL toe voor het toewijzen van gemeenten."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "assign-province/",
                self.admin_site.admin_view(self.assign_province_view),
                name="assign_province",
            ),
        ]
        return custom_urls + urls # type: ignore[no-any-return]

    def assign_province_view(self, request: HttpRequest) -> Any:
        """View om alle gemeenten van een provincie toe te wijzen aan geselecteerde gebruikers."""
        if request.method == "POST":
            form = AssignProvinceForm(request.POST)
            if form.is_valid():
                province = form.cleaned_data["province_name"]
                user_ids = request.POST.getlist("_selected_action")
                municipalities = Municipality.objects.filter(province=province)

                for user_id in user_ids:
                    user = VespaUser.objects.get(id=user_id)
                    user.municipalities.add(*municipalities)

                self.message_user(
                    request, f"Alle gemeenten uit {province.name} zijn toegewezen aan geselecteerde gebruikers."
                )
                return HttpResponseRedirect(request.get_full_path())

            self.message_user(request, "Ongeldige formulierinvoer.", level="error")

        else:
            form = AssignProvinceForm()
            user_ids = request.GET.getlist("_selected_action")
            users = VespaUser.objects.filter(id__in=user_ids)

        return render(
            request,
            "admin/assign_province.html",
            {"form": form, "users": users},
        )

    @admin.action(description="Wijs alle gemeenten van een provincie toe aan geselecteerde gebruikers")
    def assign_province_municipalities(
        self,
        request: HttpRequest,
        queryset: Iterable[VespaUser],
    ) -> HttpResponseRedirect:
        """Redirect naar de assign-province view."""
        return HttpResponseRedirect(
            "assign-province/?_selected_action=" + "&_selected_action=".join([str(u.id) for u in queryset])
        )
