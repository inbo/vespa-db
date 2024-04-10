"""."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from vespadb.users.models import VespaUser


@admin.register(VespaUser)
class VespaUserAdmin(UserAdmin):
    """Admin class for the VespaUser model."""

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
