"""Views for the nests app."""

import csv
from django.core.serializers import serialize

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework_gis.filters import DistanceToPointFilter
from django.shortcuts import render

from vespadb.nests.filters import NestFilter
from vespadb.nests.models import Nest
from vespadb.nests.serializers import AdminNestPatchSerializer, NestPatchSerializer, NestSerializer
from vespadb.permissions import IsAdmin, IsUser


class NestsViewSet(viewsets.ModelViewSet):
    """ViewSet for the Nest model."""

    queryset = Nest.objects.all()
    serializer_class = NestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        DistanceToPointFilter,
    ]
    filterset_fields = [
        "location",
        "reported_datetime",
        "status",
        "nature_reserve",
        "public_domain",
    ]
    filterset_class = NestFilter
    ordering_fields = ["reported_datetime", "status"]
    distance_filter_field = "location"
    distance_filter_convert_meters = True

    def get_serializer_class(self) -> BaseSerializer:
        """
        Return the class to use for the serializer. Defaults to using self.serializer_class.

        Admins get full serialization, others get basic serialization depending on the incoming request.

        :return: Serializer class
        """
        if self.request.method == "PATCH":
            if self.request.user.is_staff:
                return AdminNestPatchSerializer
            return NestPatchSerializer
        return super().get_serializer_class()

    def get_permissions(self) -> list[BasePermission]:
        """Determine the set of permissions that apply to the current action.

        - For 'update' and 'partial_update' actions, authenticated users are allowed to make changes.
        - The 'destroy' action is restricted to admin users only.
        - All other actions are available to authenticated users for modification, with readonly access for unauthenticated users.

        Returns
        -------
            List[BasePermission]: A list of permission instances that should be applied to the action.
        """
        if self.action in {"create", "update", "partial_update"}:
            permission_classes = [IsUser()]
        elif self.action == "destroy":
            permission_classes = [IsAdmin()]
        else:
            permission_classes = [AllowAny()]
        return permission_classes
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def geojson(self, request: Request) -> Response:
        """Serve Nest data in GeoJSON format."""
        nests = self.get_queryset()
        data = serialize('geojson', nests, geometry_field='location', fields=('id', 'location'))
        return HttpResponse(data, content_type='application/json')

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin])
    def bulk_import(self, request: Request) -> Response:
        """Allow bulk import of nests for admin users only.

        :param request: The request object.
        :return: HTTP Response indicating the status of the operation.
        """
        # Placeholder for bulk import logic.
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin])
    def export(self, request: Request) -> HttpResponse:
        """
        Export nests data in CSV format for admin users only.

        :param request: The request object.
        :return: HTTP response with the CSV data.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="nests_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Creation Datetime", "Status", "Location", "Address"])  # Specify fields as needed.

        nests = Nest.objects.all().values_list("id", "creation_datetime", "status", "location", "address")
        for nest in nests:
            writer.writerow(nest)

        return response

def map_view(request: Request) -> HttpResponse:
    """Render the map view."""
    return render(request, 'nests/map.html')
