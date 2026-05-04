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


_MANUFACTURERS = [
    {"name": "APC", "description": "APC"},
    {"name": "Aerohive"},
    {"name": "Apple"},
    {"name": "Aruba"},
    {"name": "Cisco"},
    {"name": "Dell"},
    {"name": "Fortinet"},
    {"name": "Generic", "description": "Generic devices such as patch panels"},
    {"name": "HPE"},
    {"name": "Juniper"},
    {"name": "MikroTik", "description": "MikroTik"},
    {"name": "Power Dsine"},
    {"name": "Raspberry Pi Foundation"},
    {"name": "Ruckus", "description": "Ruckus"},
    {"name": "TP-Link", "description": "TP-Link"},
    {"name": "Yamaha"},
]

# Platforms. `network_driver_mappings` is intentionally NOT stored per-Platform —
# it's a computed property on Platform that resolves the supplied `network_driver`
# string against Nautobot's `NETWORK_DRIVERS` Django settings. Built-in drivers
# (cisco_ios, juniper_junos, mikrotik_routeros, etc.) already have sensible default
# mappings; custom drivers (aruba_osswitch, cisco_s300, ruckus_icx, tplink_jetstream)
# can be added via `NETWORK_DRIVERS` in nautobot_config.py if/when needed.
_PLATFORMS = [
    {"name": "Aruba OS YA.16", "manufacturer": "HPE", "network_driver": "aruba_osswitch", "napalm_driver": "arubaoss"},
    {"name": "CBS", "manufacturer": "Cisco", "network_driver": "cisco_s300", "napalm_driver": "cbs"},
    {"name": "FortiOS", "manufacturer": "Fortinet", "network_driver": "fortinet_fortios", "napalm_driver": "fortios"},
    {"name": "IOS 12", "manufacturer": "Cisco", "network_driver": "cisco_ios", "napalm_driver": "ios"},
    {"name": "IOS 15", "manufacturer": "Cisco", "network_driver": "cisco_ios", "napalm_driver": "ios"},
    {"name": "Junos 21", "manufacturer": "Juniper", "network_driver": "juniper_junos", "napalm_driver": "junos"},
    {"name": "Mikrotik", "manufacturer": "MikroTik", "network_driver": "mikrotik_routeros",
     "napalm_driver": "mikrotik_routeros"},
    {"name": "Ruckus ICX", "manufacturer": "Ruckus", "network_driver": "ruckus_icx", "napalm_driver": "icx"},
    {"name": "Ruckus VSZ", "manufacturer": "Ruckus", "network_driver": "", "napalm_driver": ""},
    {"name": "TP-Link JetStream", "manufacturer": "TP-Link", "network_driver": "tplink_jetstream",
     "napalm_driver": "tplink"},
]

# Roles. `cf_basic_type` (when set) populates the Layer8 'Basic Type' custom field on the Role,
# which downstream code uses to map external concepts onto Nautobot Roles.
_ROLES = [
    {"name": "Access Switch", "content_types": ["dcim.device"], "color": "9e9e9e", "cf_basic_type": "access-switch"},
    {"name": "Administrative", "content_types": ["extras.contactassociation"], "color": "2196f3",
     "description": "Unit plays an administrative role"},
    {"name": "Anycast", "content_types": ["ipam.ipaddress"], "color": "ffc107"},
    {"name": "Billing", "content_types": ["extras.contactassociation"], "color": "4caf50",
     "description": "Unit plays a billing role"},
    {"name": "CARP", "content_types": ["ipam.ipaddress"], "color": "4caf50"},
    {"name": "CPE", "content_types": ["dcim.device"], "color": "9e9e9e", "cf_basic_type": "cpe"},
    {"name": "Core Gateway", "content_types": ["dcim.device"], "color": "9e9e9e", "cf_basic_type": "core-router"},
    {"name": "Core Switch", "content_types": ["dcim.device"], "color": "9e9e9e", "cf_basic_type": "core-switch"},
    {"name": "Distribution Switch", "content_types": ["dcim.device"], "color": "9e9e9e",
     "cf_basic_type": "access-switch"},
    {"name": "GLBP", "content_types": ["ipam.ipaddress"], "color": "4caf50"},
    {"name": "Guest", "content_types": ["ipam.vlan"], "color": "9e9e9e"},
    {"name": "HSRP", "content_types": ["ipam.ipaddress"], "color": "4caf50"},
    {"name": "In-Unit Distribution Switch", "content_types": ["dcim.device"], "color": "9e9e9e",
     "cf_basic_type": "iud-switch"},
    {"name": "Loopback", "content_types": ["ipam.ipaddress"], "color": "9e9e9e"},
    {"name": "Management", "content_types": ["ipam.vlan"], "color": "9e9e9e"},
    {"name": "On Site", "content_types": ["extras.contactassociation"], "color": "111111",
     "description": "Unit plays an on site role"},
    {"name": "Patch Panel", "content_types": ["dcim.device"], "color": "9e9e9e", "cf_basic_type": "patchpanel"},
    {"name": "Public Static IP Pool", "content_types": ["ipam.prefix"], "color": "9e9e9e"},
    {"name": "Public-IP", "content_types": ["ipam.vlan"], "color": "9e9e9e"},
    {"name": "Secondary", "content_types": ["ipam.ipaddress"], "color": "2196f3"},
    {"name": "Standard", "content_types": ["ipam.vlan"], "color": "9e9e9e"},
    {"name": "Support", "content_types": ["extras.contactassociation"], "color": "ffeb3b",
     "description": "Unit plays a support role"},
    {"name": "UPS", "content_types": ["dcim.device"], "color": "9e9e9e", "description": "UPS"},
    {"name": "Unknown", "content_types": ["dcim.device"], "color": "9e9e9e"},
    {"name": "VIP", "content_types": ["ipam.ipaddress"], "color": "4caf50"},
    {"name": "VRRP", "content_types": ["ipam.ipaddress"], "color": "4caf50"},
    {"name": "Wireless Access Point", "content_types": ["dcim.device"], "color": "9e9e9e"},
    {"name": "X-Connect", "content_types": ["ipam.vlan"], "color": "9e9e9e"},
]

_PROVIDERS = [
    {"name": "Vorboss"},
]


def create_default_seed_data(sender, apps, **kwargs):
    """Seed the Manufacturers, Platforms, Roles, and Providers Layer8 expects to exist.

    Idempotent: keyed on `name` for every model, so re-running on an instance that already
    has these records is a no-op (the non-key attributes are refreshed each time).
    """
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    Platform = apps.get_model("dcim", "Platform")
    Role = apps.get_model("extras", "Role")
    Provider = apps.get_model("circuits", "Provider")
    ContentType = apps.get_model("contenttypes", "ContentType")

    for entry in _MANUFACTURERS:
        Manufacturer.objects.update_or_create(
            name=entry["name"],
            defaults={"description": entry.get("description", "")},
        )

    for entry in _PLATFORMS:
        try:
            mfr = Manufacturer.objects.get(name=entry["manufacturer"])
        except Manufacturer.DoesNotExist:
            print(f"[layer8_app seed] manufacturer '{entry['manufacturer']}' missing for platform '{entry['name']}'")
            continue
        Platform.objects.update_or_create(
            name=entry["name"],
            defaults={
                "manufacturer": mfr,
                "network_driver": entry.get("network_driver", "") or "",
                "napalm_driver": entry.get("napalm_driver", "") or "",
                "description": entry.get("description", ""),
            },
        )

    for entry in _ROLES:
        defaults = {
            "color": entry.get("color", "9e9e9e"),
            "description": entry.get("description", ""),
        }
        role, _ = Role.objects.update_or_create(name=entry["name"], defaults=defaults)
        cts = []
        for ct_str in entry["content_types"]:
            app_label, model = ct_str.split(".")
            try:
                cts.append(ContentType.objects.get(app_label=app_label, model=model))
            except ContentType.DoesNotExist:
                print(f"[layer8_app seed] ContentType {ct_str} missing; skipping for role '{entry['name']}'")
        role.content_types.set(cts)
        if entry.get("cf_basic_type"):
            role._custom_field_data["basic_type"] = entry["cf_basic_type"]
            role.save()

    for entry in _PROVIDERS:
        # Provider has `comments`, not `description`. We don't seed any other fields
        # (asn, portal_url, etc.) so the defaults dict is empty by design.
        Provider.objects.update_or_create(name=entry["name"], defaults={})
