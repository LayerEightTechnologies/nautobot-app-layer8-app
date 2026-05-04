"""API views for the Layer8 app.

Auvik-specific viewsets are commented out below; revive them when Auvik
support returns.
"""

# from nautobot.apps.api import NautobotModelViewSet
#
# from ..models import AuvikTenantBuildingRelationship, AuvikTenant
# from .serializers import AuvikTenantBuildingRelationshipSerializer, AuvikTenantSerializer
#
#
# class AuvikTenantBuildingRelationshipViewSet(NautobotModelViewSet):
#     """API view for AuvikTenantBuildingRelationship objects."""
#
#     queryset = AuvikTenantBuildingRelationship.objects.all()
#     serializer_class = AuvikTenantBuildingRelationshipSerializer
#
#
# class AuvikTenantViewSet(NautobotModelViewSet):
#     """API view for AuvikTenant objects."""
#
#     queryset = AuvikTenant.objects.all()
#     serializer_class = AuvikTenantSerializer
