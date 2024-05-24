"""Healtcheck endpoint."""

from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views import View


class HealthCheckView(View):
    """View to handle health check requests."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Return a simple health check response.

        Parameters
        ----------
        request : HttpRequest
            The incoming request.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        JsonResponse
            A JSON response indicating the health status.
        """
        return JsonResponse({"status": "ok"}, status=200)
