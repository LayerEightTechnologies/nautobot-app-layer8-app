"""Signals for Layer8 App."""


def create_custom_fields(sender, apps, **kwargs):
    """Create custom fields for Layer8 App."""
    pass


def create_default_locationtypes(sender, apps, **kwargs):
    """Create default location types for Layer8 App."""
    LocationTypes = apps.get_model("dcim", "LocationType")
    Building = LocationTypes.objects.get_or_create(
        name="Building",
        nestable=True,
        content_types=[
            "dcim.device",
            "circuits.circuit",
            "circuits.circuit_termination",
            "ipam.namespace",
            "ipam.prefix",
            "ipam.vlan",
            "ipam.vlan_group",
        ],
    )
    LocationTypes.objects.get_or_create(
        name="Room",
        nestable=True,
        content_types=[
            "dcim.device",
            "circuits.circuit",
            "circuits.circuit_termination",
            "ipam.namespace",
            "ipam.prefix",
            "ipam.vlan",
            "ipam.vlan_group",
        ],
        parent=Building,
    )
