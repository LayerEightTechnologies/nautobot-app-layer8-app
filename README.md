# Layer8 App

A Nautobot 2.x plugin that integrates Nautobot with the Layer8 Platform.

## What it does

- **Bootstraps Layer8-specific seed data** on `nautobot_database_ready`:
  - Custom fields (e.g. `external_id`, `monitoring_profile`, `cabling_model`, `circuit_role`).
  - Default LocationTypes (`Building`, `Room`, with sensible content_types).
  - Manufacturers, Platforms, Roles (incl. `basic_type` custom-field values), and the `Vorboss` Provider.
- **Provides an SSOT job** (built on `nautobot-ssot`) to sync Buildings and Rooms from the **Layer8 Core API** into Nautobot DCIM Locations.
- **Adds bespoke UI** for two manual workflows: bulk patch-panel creation per building, and bulk floodwired cable creation between a device and a patch panel.

## SSOT job

`Layer8 Core API Data Source` (in [layer8_app/ssot_jobs/sync_tenant_api.py](layer8_app/ssot_jobs/sync_tenant_api.py)) is built on `nautobot_ssot.contrib`:

- Source: `https://core-api.${INSTANCE_FQDN}` (auth: `x-api-key` from the `Layer8 Core API Key` Nautobot Secret).
- Models: `BuildingModel` and `RoomModel`, both wrapping `dcim.Location` with the `external_id` custom field as the durable identifier (it stores the Core API's primary key).
- Order matters: buildings load first to seed a `building_id → name` index that the room loader uses to resolve parent linkage. Rooms whose building isn't in the filter set are skipped.
- Idempotent.

The dormant Auvik integration (preserved on disk for future revival) has been disabled.

## Configuration

The plugin needs:

- `INSTANCE_FQDN` env var on the Nautobot container — used to construct the Core API base URL.
- A Nautobot Secret named `Layer8 Core API Key` whose value is a Layer8 Core API key.

In production this Secret comes from Azure Key Vault via `nautobot-secrets-providers[azure]`. In local dev, the simplest path is the built-in `Environment Variable` Secret provider — see [docs/dev/dev_environment.md](docs/dev/dev_environment.md).

## OpenAPI client

The plugin depends on a private Python client generated from the Layer8 Core API spec (`development/layer8-core-api.openapi.json`). The client lives in its own private repo: [`LayerEightTechnologies/layer8-core-api-py-client`](https://github.com/LayerEightTechnologies/layer8-core-api-py-client).

To regenerate after a spec change, use the [`/regen-core-client`](.claude/commands/regen-core-client.md) Claude Code slash command, or follow the manual steps in [docs/dev/regenerating_openapi_client.md](docs/dev/regenerating_openapi_client.md).

## Installation

In production, the plugin is installed by `pip install git+https://github.com/LayerEightTechnologies/nautobot-app-layer8-app.git` from the Nautobot image's Dockerfile. The build needs a GitHub App installation token (BuildKit secret) so it can transitively clone the private client. See the Layer8 monorepo's `apps/nautobot/Dockerfile` and `deploy/prod/scripts/deploy.sh`.

For local dev: `invoke build && invoke debug`. See [docs/dev/dev_environment.md](docs/dev/dev_environment.md) for the GitHub App credential requirements.
