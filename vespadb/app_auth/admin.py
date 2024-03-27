"""Session admin for the app_auth app."""

from typing import Any

from django.contrib import admin
from django.contrib.sessions.models import Session
from django.urls import reverse
from django.utils.html import format_html

from vespadb.users.models import VespaUser as User


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """A Django admin interface for managing Session instances."""

    # Defines the columns to display in the Django admin list view.
    list_display = ("session_key", "username", "expire_date", "expire_session")

    def username(self, obj: Session) -> str | None:
        """
        Retrieve the username associated with the given session.

        Args:
            obj (Session): The session object from which to retrieve the username.

        Returns
        -------
            str: The username associated with the session, if any. Returns None if no user is associated.
        """
        session_data = obj.get_decoded()
        user_id = session_data.get("_auth_user_id")

        if user_id:
            user = User.objects.get(id=user_id)
            return str(user.username)
        return None

    def expire_session(self, obj: Session) -> Any:
        """
        Generate HTML for an 'Expire Session' button linked to the expire_session view for the given session.

        Args:
            obj (Session): The session object for which to generate the expire button.

        Returns
        -------
            str: HTML string for the 'Expire Session' button.
        """
        return format_html('<a href="{}" class="button">Expire Session</a>', reverse("expire_session", args=[obj.pk]))
