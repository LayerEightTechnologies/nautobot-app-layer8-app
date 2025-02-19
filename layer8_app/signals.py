"""Signals for Layer8 App."""


def create_custom_fields(sender, apps, **kwargs):
    """Create custom fields for Layer8 App."""
    pass


def create_default_locationtypes(sender, apps, **kwargs):
    """Create default location types for Layer8 App."""
    LocationTypes = apps.get_model("dcim", "LocationType")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct_strings = [
        "dcim.device",
        "circuits.circuit",
        "circuits.circuittermination",
        "ipam.namespace",
        "ipam.prefix",
        "ipam.vlan",
        "ipam.vlangroup",
    ]

    cts = []
    for ct_str in ct_strings:
        app_label, model_name = ct_str.split(".")
        try:
            ct_obj = ContentType.objects.get(app_label=app_label, model=model_name)
        except:
            print(f"Content Type {ct_str} not found.")
            continue
        cts.append(ct_obj)

    building, _ = LocationTypes.objects.update_or_create(
        name="Building",
        defaults={
            "nestable": True,
        },
    )
    building.content_types.set(cts)
    room, _ = LocationTypes.objects.update_or_create(
        name="Room",
        defaults={
            "nestable": True,
            "parent": building,
        },
    )
    room.content_types.set(cts)
