# spa/views.py
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
import os
from django.http import HttpRequest

class SPAView(View):
    """
    A Django View that serves the index.html file of a Vue.js application.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handles GET requests. Returns the index.html file in the STATIC_ROOT/vue directory.
        If the file is not found, it returns a 501 status code with a message.

        Args:
            request (HttpRequest): The Django request object.

        Returns:
            HttpResponse: The Django response object.
        """
        try:
            with open(os.path.join(settings.STATIC_ROOT, 'vue', 'index.html'), 'r') as file:
                return HttpResponse(file.read())
        except FileNotFoundError:
            return HttpResponse(
                """
                index.html not found! Build your Vue.js app.
                """,
                status=501,
            )
