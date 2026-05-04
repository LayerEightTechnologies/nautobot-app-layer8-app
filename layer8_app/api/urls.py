"""URLs for the Layer8 App API.

Auvik-specific routes are commented out below; revive them when Auvik
support returns.
"""

from rest_framework import routers

# from .views import AuvikTenantBuildingRelationshipViewSet, AuvikTenantViewSet

router = routers.DefaultRouter()
# router.register(r"auvik-tenant-building-relationships", AuvikTenantBuildingRelationshipViewSet)
# router.register(r"auvik-tenants", AuvikTenantViewSet)
urlpatterns = router.urls
