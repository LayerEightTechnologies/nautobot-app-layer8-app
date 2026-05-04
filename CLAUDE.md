# Layer8 App — Nautobot plugin

A Nautobot 2.x plugin that:

1. **Bootstraps Layer8 seed data** on `nautobot_database_ready`: custom fields, default LocationTypes (Building, Room), Manufacturers, Platforms, Roles (with `basic_type` custom-field values), and the Vorboss Provider.
2. **Provides one SSOT job** (built on `nautobot-ssot.contrib`) to sync Buildings and Rooms from the Layer8 Core API into Nautobot DCIM Locations.
3. **Adds bespoke UI** for bulk patch-panel and floodwired-cable creation.

The legacy Wavenet Tenant API integration has been deleted. The Auvik integration is **disabled** (source preserved on disk under `helpers/auvik_api.py`, `ssot_jobs/diffsync/adapters/auvik.py`, and `ssot_jobs/diffsync/models/`) — see "Dormant code" below.

Plugin slug / Django app label: `layer8_app`. URL base: `layer8-app`. Min Nautobot: 2.0.0; tested in dev at 2.4.32 / Pydantic 1.10.26.

## Layout

```
layer8_app/
├── __init__.py            # Layer8AppConfig (signals + nav menu)
├── models.py              # AuvikTenant + 3 other Auvik models (DEPRECATED, DB tables retained)
├── signals.py             # Three nautobot_database_ready handlers:
│                          #   create_default_locationtypes  (Building, Room)
│                          #   create_custom_fields          (9 custom fields)
│                          #   create_default_seed_data      (Manufacturers, Platforms, Roles, Provider)
├── jobs.py                # Top-level Job registration: BuildingDataSource + DecomissionDevice
├── helpers/
│   ├── core_api.py        # core_api_base_url() + core_api_client() factory
│   ├── get_m2m_token.py   # Reads "Layer8 Core API Key" Nautobot Secret
│   └── auvik_api.py       # DORMANT (Auvik)
├── ssot_jobs/
│   ├── sync_tenant_api.py # PRIMARY: BuildingDataSource (contrib-style, Buildings + Rooms)
│   ├── jobs.py            # DORMANT (AuvikDataSource lives here, no live import)
│   └── diffsync/
│       ├── adapters/
│       │   ├── auvik.py    # DORMANT
│       │   └── nautobot.py # DORMANT (NautobotAuvikAdapter; legacy NautobotAdapter is dead code)
│       └── models/         # DORMANT
├── views.py / forms.py / urls.py / navigation.py  # Patch panel & cable UIs
├── api/                   # DRF — Auvik viewsets commented out; router.urls only
├── admin.py               # All admin registrations commented out (Auvik)
├── migrations/            # 0001–0009 (Auvik tables retained for migration history)
├── templates/layer8_app/  # cable_create.html, patch_panel_create.html
└── tests/                 # test_api.py, test_basic.py
```

## Configuration

Two runtime requirements:

| What | Where | Used by |
|---|---|---|
| `INSTANCE_FQDN` env var on the Nautobot container | `nautobot.env` (prod) / `creds.env` (dev) | `helpers/core_api.core_api_base_url()` to build `https://core-api.${INSTANCE_FQDN}` |
| `Layer8 Core API Key` Nautobot Secret | Azure KV in prod, `Environment Variable` provider in dev | `helpers/get_m2m_token.get_api_token()` |

`Layer8AppConfig.required_settings = []` — there is no `PLUGINS_CONFIG` for this app.

## Custom fields auto-created on `nautobot_database_ready`

Defined in [layer8_app/signals.py](layer8_app/signals.py). 9 fields, idempotent (`update_or_create` keyed on `key`):

| Key | Type | Content types | Notes |
|---|---|---|---|
| `basic_type` | TEXT | extras.Role | Set by the seed signal on Roles for Layer8 type mapping |
| `cabling_model` | SELECT | dcim.Location | choices: FLOOD / IUD (default IUD) |
| `circuit_role` | SELECT | circuits.Circuit | Primary / Secondary / Tertiary / Auxillary |
| `dia_allocation` | INTEGER | dcim.Location | |
| `external_id` | INTEGER | dcim.Location, tenancy.Tenant | Stores the Core API's primary key (`id`), NOT its `external_id` string field |
| `primary_mac_address` | TEXT | dcim.Device | Auvik-driven (kept for revival) |
| `site_primary_wan_interface` | BOOLEAN | dcim.Interface | Auvik-driven |
| `technical_reference` | TEXT | dcim.Location | |
| `monitoring_profile` | JSON | dcim.{Device,Interface,Location} | Auvik-driven shape: `{"monitoredBy": str\|null, "monitoringFields": {...}}` |

The three Auvik-driven fields are kept so a future Auvik revival doesn't need a migration.

## Default LocationTypes

`Building` (top-level, nestable) and `Room` (parent=Building, nestable). Both have content_types: `dcim.device`, `circuits.{circuit,circuittermination}`, `ipam.{namespace,prefix,vlan,vlangroup}`.

## Seed data (`create_default_seed_data`)

Idempotent (`update_or_create` keyed on `name`):

- **Manufacturers** (16): APC, Aerohive, Apple, Aruba, Cisco, Dell, Fortinet, Generic, HPE, Juniper, MikroTik, Power Dsine, Raspberry Pi Foundation, Ruckus, TP-Link, Yamaha.
- **Platforms** (10): Aruba OS YA.16, CBS, FortiOS, IOS 12, IOS 15, Junos 21, Mikrotik, Ruckus ICX, Ruckus VSZ, TP-Link JetStream. Each has `network_driver` + `napalm_driver`. `network_driver_mappings` is a computed property derived from the `NETWORK_DRIVERS` Django setting and is intentionally not seeded.
- **Roles** (28): mixture of `dcim.device` switches/routers, `ipam.ipaddress` IP roles (Anycast, HSRP, VRRP, …), `ipam.vlan`/`ipam.prefix` roles, and `extras.contactassociation` roles. Some carry a `basic_type` custom-field value (e.g. Access Switch → `access-switch`, Core Gateway → `core-router`).
- **Providers** (1): Vorboss.

## SSOT design

One job: `Layer8 Core API Data Source` (`BuildingDataSource` in [ssot_jobs/sync_tenant_api.py](layer8_app/ssot_jobs/sync_tenant_api.py)). Uses `nautobot_ssot.contrib`. Both `BuildingModel` and `RoomModel` wrap `dcim.Location`.

Notable behaviours:

- `_identifiers = ("external_id", "location_type__name")` — the custom field `external_id` stores the Core API PK (`id`), and `location_type__name` distinguishes Buildings from Rooms.
- Each model overrides `get_queryset` to filter by location_type (`Location.objects.filter(location_type__name="Building")` / `"Room"`). Without this, contrib's default would double-load every Location for both models.
- `CustomFieldAnnotation` is declared with **both** `name=` and `key=` set to the same value, working around a contrib bug at `nautobot_ssot/contrib/adapter.py:92` that checks `metadata.name in db_obj.cf` but reads via `metadata.key`.
- Buildings load first to populate a `building_id → name` map; rooms then resolve `parent__name` from that map. Rooms whose building isn't in the filter set are skipped.

## Standalone Jobs

Just one: `DecomissionDevice` (JobButtonReceiver on Device) — renames to `[Decommed] <name>`, sets status `Decommissioning`, clears `monitoring_profile`, removes primary IP, removes IPs from all interfaces, removes cables. Permanent.

## UI views

Live under `/plugins/layer8-app/`:

- `cable/create/` and `cable/create-expandable/` — bulk create cables between a device's free physical interfaces and the next free interfaces on a patch panel.
- `patchpanel/create/` — for a chosen Building, create a patch panel `Device` of a chosen DeviceType in every Room.

## Local development

`uvx invoke build && uvx invoke debug` (or installed `invoke`). Prerequisites:

1. **Docker Desktop running** — Docker BuildKit is required for the secret mount.
2. **GitHub App credentials in shell env** — `LAYER8_GITHUB_APP_ID`, `LAYER8_GITHUB_INSTALLATION_ID`, `LAYER8_GITHUB_APP_PRIVATE_KEY` (path to PEM). Without these the build skips the BuildKit secret and the private dep clone fails.
3. **`development/creds.env`** — at minimum `INSTANCE_FQDN=...` and `LAYER8_CORE_API_KEY=...` if you're using the env-var Secret provider.

The dev `Dockerfile` (`# syntax=docker/dockerfile:1.4`) reads `/run/secrets/github_token` (mounted by `tasks.py::_github_token_for_build`) and configures `git config insteadOf` to inject the token into transitive `pip install git+https://...` clones. The token is written under `HOME=/tmp/build-home` so it never lands in any persisted layer.

To regenerate the OpenAPI client after a spec change: `/regen-core-client` (slash command) or follow [docs/dev/regenerating_openapi_client.md](docs/dev/regenerating_openapi_client.md).

## Production deployment

Image is rebuilt by `pip install git+https://...nautobot-app-layer8-app.git` (no version pin, `main` branch) baked into `layer8/nautobot:prod`. The Layer8 monorepo (`/opt/layer8/apps/nautobot/Dockerfile`) handles this; a sibling BuildKit secret holds a GitHub App installation token minted at deploy time.

Update flow on the test VM (Vorboss UKS):

```
cd /opt/layer8/deploy/prod && ./scripts/update.sh main
```

For ad-hoc Django/ORM inspection on a live container, pipe via stdin:

```bash
docker exec -i nautobot nautobot-server shell <<'PY'
from layer8_app.helpers.core_api import core_api_client
from layer8_core_api_py_client.api.buildings_api import BuildingsApi
print(BuildingsApi(core_api_client()).buildings_get(limit='3'))
PY
```

## Dormant code (Auvik)

Files preserved for future revival but not imported from the live graph:

- `helpers/auvik_api.py` — Auvik client + secret retrieval helpers
- `ssot_jobs/jobs.py` — `AuvikDataSource` job class (dormant)
- `ssot_jobs/diffsync/adapters/auvik.py` — full Auvik DiffSync adapter (~745 lines)
- `ssot_jobs/diffsync/adapters/nautobot.py` — `NautobotAuvikAdapter` (used by `AuvikDataSource`); the legacy `NautobotAdapter` in this file is dead code from the deleted `Layer8DataSource`
- `ssot_jobs/diffsync/models/` — DiffSync model definitions for the Auvik sync

To revive: re-add the `layer8-auvik-api-client` git dep to `pyproject.toml`; uncomment the imports/registrations in `jobs.py`, `admin.py`, `api/{serializers,views,urls}.py`. The four Auvik DB tables in `models.py` and `migrations/` are still present.

## External integrations

- Layer8 Core API (`https://core-api.${INSTANCE_FQDN}`) — Buildings, Rooms, and (future) Tenancies.
- Auvik (DORMANT, was `https://auvikapi.eu1.my.auvik.com/v1`).

## Where things may surprise you

- **Spec quirks**: the upstream `layer8-core-api.openapi.json` has schema names with spaces (`Customer Patch`, `User Type Assignments`, …) and some `$ref`s with URL-encoded names. Generation requires `--skip-validate-spec`. We patched `Room.external_id` and `Room Patch.external_id` locally to be nullable + non-required because the API actually returns null for some rooms. `Customer Patch`, `Tenancy`, `Tenancy Patch`, etc. have similar shapes — if you hit deserialization errors with those endpoints, the same fix applies.
- **`CustomFieldAnnotation(key=...)` alone is broken** in this `nautobot_ssot` version — pass `name=` too.
- **Contrib's default `_get_queryset` doesn't filter by `_modelname`** — for nested types backed by the same Django model, override `get_queryset` per DiffSync model.
- **Job signature**: Nautobot 2.4 calls `Job.run(dryrun=...)` without `memory_profiling`. Make `memory_profiling=False` a default.
