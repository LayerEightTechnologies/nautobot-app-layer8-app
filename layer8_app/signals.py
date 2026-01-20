"""Signals for Layer8 App."""


def create_custom_fields(sender, apps, **kwargs):
    """Create custom fields for Layer8 App."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    CustomFieldChoice = apps.get_model("extras", "CustomFieldChoice")
    Role = apps.get_model("extras", "Role")
    Circuit = apps.get_model("circuits", "Circuit")
    Interface = apps.get_model("dcim", "Interface")
    Device = apps.get_model("dcim", "Device")
    Location = apps.get_model("dcim", "Location")
    Tenant = apps.get_model("tenancy", "Tenant")

    from nautobot.extras.choices import CustomFieldTypeChoices

    fields = [
        {
            "name": "Basic Type",
            "label": "basic_type",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "default": None,
            "content_types": [ContentType.objects.get_for_model(Role)],
        },
        {
            "name": "Cabling Model",
            "label": "cabling_model",
            "type": CustomFieldTypeChoices.TYPE_SELECT,
            "default": "IUD",
            "choices": [
                {"value": "FLOOD", "weight": 100},
                {"value": "IUD", "weight": 200},
            ],
            "content_types": [ContentType.objects.get_for_model(Location)],
        },
        {
            "name": "Circuit Role",
            "label": "circuit_role",
            "type": CustomFieldTypeChoices.TYPE_SELECT,
            "default": "Auxillary",
            "choices": [
                {"value": "Primary", "weight": 100},
                {"value": "Secondary", "weight": 200},
                {"value": "Tertiary", "weight": 300},
                {"value": "Auxillary", "weight": 400},
            ],
            "content_types": [ContentType.objects.get_for_model(Circuit)],
        },
        {
            "name": "DIA Allocation",
            "label": "dia_allocation",
            "type": CustomFieldTypeChoices.TYPE_INTEGER,
            "default": 0,
            "content_types": [ContentType.objects.get_for_model(Location)],
        },
        {
            "name": "External ID",
            "label": "external_id",
            "type": CustomFieldTypeChoices.TYPE_INTEGER,
            "default": None,
            "content_types": [ContentType.objects.get_for_model(Location), ContentType.objects.get_for_model(Tenant)],
        },
        {
            "name": "Primary MAC Address",
            "label": "primary_mac_address",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "default": None,
            "content_types": [ContentType.objects.get_for_model(Device)],
        },
        {
            "name": "Site Primary WAN Interface",
            "label": "site_primary_wan_interface",
            "type": CustomFieldTypeChoices.TYPE_BOOLEAN,
            "default": False,
            "content_types": [ContentType.objects.get_for_model(Interface)],
        },
        {
            "name": "Technical Reference",
            "label": "technical_reference",
            "type": CustomFieldTypeChoices.TYPE_TEXT,
            "default": None,
            "content_types": [ContentType.objects.get_for_model(Location)],
        },
        {
            "name": "Monitoring Profile",
            "label": "monitoring_profile",
            "type": CustomFieldTypeChoices.TYPE_JSON,
            "default": {"monitoredBy": None, "monitoringFields": {}},
            "content_types": [
                ContentType.objects.get_for_model(Device),
                ContentType.objects.get_for_model(Interface),
                ContentType.objects.get_for_model(Location),
            ],
        },
    ]

    for field_data in fields:
        defaults = {
            "type": field_data["type"],
            "label": field_data["name"],
            "default": field_data["default"],
        }
        custom_field, created = CustomField.objects.update_or_create(
            key=field_data["label"],
            defaults=defaults,
        )

        custom_field.content_types.set(field_data["content_types"])

        if "choices" in field_data and created:
            choices = []
            for choice in field_data["choices"]:
                choices.append(
                    CustomFieldChoice(custom_field=custom_field, value=choice["value"], weight=choice["weight"])
                )
            CustomFieldChoice.objects.bulk_create(choices)


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


# TODO: Populate the database with some basic DeviceTypes (+ Interfaces), Manufacturers, Platforms, CircuitTypes, Providers etc
# def create_device_types(sender, apps, **kwargs):
#     """Create default device types for Layer8 App."""
#     DeviceType = apps.get_model("dcim", "DeviceType")
#     Manufacturer = apps.get_model("dcim", "Manufacturer")
#     Platform = apps.get_model("dcim", "Platform")
#     DeviceBayTemplate = apps.get_model("dcim", "DeviceBayTemplate")
#     DeviceRole = apps.get_model("dcim", "DeviceRole")
#     RackRole = apps.get_model("dcim", "RackRole")
#     Rack = apps.get_model("dcim", "Rack")
#     RackGroup = apps.get_model("dcim", "RackGroup")
#     Site = apps.get_model("dcim", "Site")
#     ContentType = apps.get_model("contenttypes", "ContentType")

#     manufacturer, _ = Manufacturer.objects.update_or_create(
#         name="Layer8",
#     )

#     platform, _ = Platform.objects.update_or_create(
#         name="Layer8 Platform",
#         manufacturer=manufacturer,
#     )

#     device_role, _ = DeviceRole.objects.update_or_create(
#         name="Layer8 Device",
#         manufacturer=manufacturer,
#         slug="layer8-device",
#     )

#     rack_role, _ = RackRole.objects.update_or_create(
#         name="Layer8 Rack",
#         slug="layer8-rack",
#     )

#     site, _ = Site.objects.update_or_create(
#         name="Layer8 Site",
#         slug="layer8-site",
#     )

#     rack_group, _ = RackGroup.objects.update_or_create(
#         name="Layer8 Rack Group",
#         slug="layer8-rack-group",
#     )

#     rack, _ = Rack.objects.update_or_create(
#         name="Layer8 Rack",
#         site=site,
#         group=rack_group,
#         role=rack_role,
#         u_height=42,
#     )

#     device_type, _ = DeviceType.objects.update_or_create(
#         manufacturer=manufacturer,
#         model="Layer8 Device",
#         slug="layer8-device",
#         u_height=1,
#         device_role=device_role,
#         platform=platform,
#         subdevice_role=ContentType.objects.get(app_label="dcim", model="device"),
#     )

#     DeviceBayTemplate.objects.update_or_create(
#         device_type=device_type,
#         name="Layer8 Device Bay",
#         u_height=1,
#     )
