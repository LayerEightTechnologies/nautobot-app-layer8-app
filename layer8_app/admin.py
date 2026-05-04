"""Layer8 App Admin interface."""

# Auvik integration is disabled. The model definitions remain in models.py for
# migration history; admin registrations below are commented out and will be
# revived when Auvik support returns.
#
# from django.contrib import admin
# from nautobot.apps.admin import NautobotModelAdmin
#
# from .models import AuvikTenant, AuvikTenantBuildingRelationship, AuvikDeviceModels, AuvikDeviceVendors
#
#
# @admin.register(AuvikTenant)
# class AuvikTenantAdmin(NautobotModelAdmin):
#     """Admin interface for AuvikTenant."""
#
#     list_display = ("name", "auvik_tenant_id")
#
#
# @admin.register(AuvikTenantBuildingRelationship)
# class AuvikTenantBuildingRelationshipsAdmin(NautobotModelAdmin):
#     """Admin interface for AuvikTenantBuildingRelationships."""
#
#     list_display = ("auvik_tenant", "building")
#
#
# @admin.register(AuvikDeviceModels)
# class AuvikDeviceModelsAdmin(NautobotModelAdmin):
#     """Admin interface for AuvikDeviceModels."""
#
#     list_display = ("auvik_model_name", "nautobot_device_type")
#
#
# @admin.register(AuvikDeviceVendors)
# class AuvikDeviceVendorsAdmin(NautobotModelAdmin):
#     """Admin interface for AuvikDeviceVendors."""
#
#     list_display = ("auvik_vendor_name", "nautobot_manufacturer")
