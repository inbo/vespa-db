"""Admin configuration for vespadb users - Optimized for performance."""

import logging
from typing import Any, List, Optional, Set

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path

from vespadb.observations.models import Municipality, Province
from vespadb.users.forms import AssignProvinceForm
from vespadb.users.models import VespaUser

logger = logging.getLogger(__name__)


class MunicipalitiesAssignForm(forms.Form):
    """Form for assigning municipalities to users."""
    
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        help_text="Select a province to assign all its municipalities to the selected users"
    )
    
    municipality_names = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text="Enter municipality names as a comma-separated list"
    )
    
    def clean(self) -> dict[str, Any]:
        """Validate that at least one field is provided."""
        cleaned_data = super().clean()
        province = cleaned_data.get("province")
        municipality_names = cleaned_data.get("municipality_names")
        
        if not province and not municipality_names:
            raise forms.ValidationError(
                "Please either select a province or provide a comma-separated list of municipality names."
            )
        
        return cleaned_data


class VespaUserChangeForm(UserChangeForm):
    """Form to change a VespaUser model."""

    class Meta:
        """Meta class for the VespaUserChangeForm."""

        model = VespaUser
        fields = "__all__"


class VespaUserAdmin(UserAdmin):
    """Admin class for the VespaUser model - Optimized for performance."""

    form = VespaUserChangeForm
    filter_horizontal = ("municipalities", "groups", "user_permissions")
    
    # OPTIMIZED: Essential fields for list display
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "user_type", "reservation_count")
    
    # OPTIMIZED: Efficient filters
    list_filter = ("is_staff", "is_superuser", "user_type", "is_active", "date_joined")
    
    # OPTIMIZED: Enable search for autocomplete functionality
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    # OPTIMIZED: Add pagination for better performance with large user sets
    list_per_page = 50
    list_max_show_all = 200
    
    fieldsets = UserAdmin.fieldsets + (
        (
            "Vespa",
            {
                "fields": (
                    "user_type",
                    "municipalities",
                    "reservation_count",
                )
            },
        ),
    )
    actions = ["assign_municipalities_action"]

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related for many-to-many relationships."""
        return super().get_queryset(request).prefetch_related('municipalities', 'groups')

    def get_urls(self) -> list[Any]:
        """Get custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "assign-municipalities/",
                self.admin_site.admin_view(self.assign_municipalities_view),
                name="assign_municipalities",
            ),
        ]
        return custom_urls + urls

    def assign_municipalities_action(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Admin action to assign municipalities to selected users."""
        if not queryset.exists():
            self.message_user(request, "No users selected.", messages.WARNING)
            return

        request.session["selected_users"] = list(queryset.values_list("id", flat=True))
        return redirect("admin:assign_municipalities")

    assign_municipalities_action.short_description = "Assign municipalities to selected users"

    def assign_municipalities_view(self, request: HttpRequest) -> HttpResponse:
        """View to assign municipalities to selected users."""
        user_ids = request.session.get("selected_users", [])
        users = VespaUser.objects.filter(id__in=user_ids)
        
        if not users.exists():
            self.message_user(request, "No users selected.", messages.WARNING)
            return redirect("admin:users_vespauser_changelist")
        
        if request.method == "POST":
            form = MunicipalitiesAssignForm(request.POST)
            if form.is_valid():
                province = form.cleaned_data.get("province")
                municipality_names_str = form.cleaned_data.get("municipality_names", "")
                
                municipalities_to_assign: Set[Municipality] = set()
                not_found_municipalities: List[str] = []
                
                # Process province selection
                if province:
                    province_municipalities = Municipality.objects.filter(province=province)
                    municipalities_to_assign.update(province_municipalities)
                
                # Process comma-separated municipality names
                if municipality_names_str:
                    municipality_names = [name.strip() for name in municipality_names_str.split(",") if name.strip()]
                    
                    for name in municipality_names:
                        try:
                            municipality = Municipality.objects.get(name=name)
                            municipalities_to_assign.add(municipality)
                        except Municipality.DoesNotExist:
                            not_found_municipalities.append(name)
                
                # Assign municipalities to users
                total_assigned = 0
                for user in users:
                    existing_municipalities = set(user.municipalities.all())
                    # Only add municipalities that the user doesn't already have
                    new_municipalities = municipalities_to_assign - existing_municipalities
                    if new_municipalities:
                        user.municipalities.add(*new_municipalities)
                        total_assigned += len(new_municipalities)
                
                # Show success message
                if total_assigned > 0:
                    self.message_user(
                        request,
                        f"Successfully assigned {total_assigned} municipality/municipalities to {users.count()} user(s).",
                        messages.SUCCESS,
                    )
                else:
                    self.message_user(
                        request,
                        "No new municipalities were assigned. Users may already have these municipalities.",
                        messages.INFO,
                    )
                
                # Show warning for municipalities not found
                if not_found_municipalities:
                    self.message_user(
                        request,
                        f"The following municipalities were not found: {', '.join(not_found_municipalities)}",
                        messages.WARNING,
                    )
                
                return redirect("admin:users_vespauser_changelist")
        else:
            form = MunicipalitiesAssignForm()
        
        context = {
            "form": form,
            "users": users,
            "title": "Assign Municipalities to Users",
        }
        return render(request, "admin/assign_municipalities.html", context)


admin.site.register(VespaUser, VespaUserAdmin)
