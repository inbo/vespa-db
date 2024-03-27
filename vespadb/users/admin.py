"""."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from vespadb.users.models import VespaUser


@admin.register(VespaUser)
class VespaUserAdmin(UserAdmin):
    """Admin class for the VespaUser model."""

    model = VespaUser
