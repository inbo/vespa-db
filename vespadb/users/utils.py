"""User utility functions."""

from typing import Literal, cast

from vespadb.users.models import UserType, VespaUser


def get_system_user(user_type: Literal[UserType.SYNC, UserType.IMPORT]) -> VespaUser:
    """Get System Users based on usertype."""
    system_user, _ = VespaUser.objects.get_or_create(username=user_type.value, defaults={"user_type": user_type.value})
    return cast(VespaUser, system_user)  # make mypy happy
