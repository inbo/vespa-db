"""User utility functions."""

from typing import Literal, cast

from vespadb.users.models import UserType, VespaUser


def get_system_user(user_type: Literal[UserType.SYNC]) -> VespaUser:
    """Get the system user specifically for SYNC."""
    if user_type != UserType.SYNC:
        raise ValueError("This function only supports UserType.SYNC.")

    system_user, _ = VespaUser.objects.get_or_create(
        username="sync", defaults={"user_type": UserType.SYNC.value}
    )
    return cast(VespaUser, system_user)  # make mypy happy
