# Regenerating the Layer8 Core API Python Client

This plugin talks to the Layer8 Core API via a generated Python client distributed as a separate **private** GitHub repo: [`LayerEightTechnologies/layer8-core-api-py-client`](https://github.com/LayerEightTechnologies/layer8-core-api-py-client).

The OpenAPI 3.0.1 specification that drives the generation lives **in this plugin repo** at:

```
development/layer8-core-api.openapi.json
```

It is the canonical copy used to regenerate the client. Whenever the Layer8 Core API surface changes, both the spec in this repo *and* the regenerated client in the sibling repo need to be updated.

## When to regenerate

- A new endpoint or schema was added to the Layer8 Core API.
- An existing endpoint's request/response shape changed.
- The OpenAPI generator itself improved (new minor version) and you want the upgrade — though we don't usually chase that without a reason.

If you're just changing how the plugin *uses* the existing endpoints, no regeneration is needed.

## Two-step workflow

### Step 1 — Update the OpenAPI spec in this repo

The canonical source of the OpenAPI spec is the Layer8 Core API service itself (not this repo — this repo just holds a copy). To refresh:

1. Get the latest spec from wherever the Core API team publishes it.
2. Replace `development/layer8-core-api.openapi.json` with the new file.
3. Sanity-check the diff with `git diff development/layer8-core-api.openapi.json` — look for unexpectedly large changes that suggest the upstream spec drifted in shape (e.g. tag renames, security scheme changes).
4. **Confirm the security scheme is `x-api-key`.** The generator picks up auth helpers from `components.securitySchemes`. The deployment uses an API key in the `x-api-key` header, so the spec MUST declare:
   ```json
   "components": {
     "securitySchemes": {
       "x-api-key": {
         "type": "apiKey",
         "in": "header",
         "name": "x-api-key"
       }
     }
   }
   ```
   And `"security": [{"x-api-key": []}]` at the global level. If the upstream spec uses `bearer` instead, see [Patching `bearer` → `x-api-key`](#patching-bearer--x-api-key) below before regenerating.
5. Commit the spec change to this repo as part of your PR (it's the input that drives the regenerated client).

### Step 2 — Regenerate the Python client

The fastest path is the Claude Code slash command:

```
/regen-core-client
```

(See [`.claude/commands/regen-core-client.md`](../../.claude/commands/regen-core-client.md) for what it does.)

It expects a sibling clone of the client repo at `../layer8-core-api-py-client`. Pass `--client-dir <path>` to override, or `--no-push` to stop after generation without committing.

If you'd rather run it by hand, the equivalent commands are:

```bash
# From the plugin repo root:
docker run --rm \
  -v "$(pwd)/..:/work" \
  openapitools/openapi-generator-cli:latest generate \
    -i /work/nautobot-app-layer8-app/development/layer8-core-api.openapi.json \
    -g python-pydantic-v1 \
    -o /work/layer8-core-api-py-client \
    --package-name layer8_core_api_py_client \
    --skip-validate-spec \
    --additional-properties=projectName=layer8-core-api-py-client,packageVersion=0.1.0,packageUrl=https://github.com/LayerEightTechnologies/layer8-core-api-py-client

# Strip the generator's boilerplate that we don't ship:
cd ../layer8-core-api-py-client
rm -f .travis.yml .gitlab-ci.yml git_push.sh .github/workflows/python.yml
rmdir .github/workflows .github 2>/dev/null || true

# Inspect what changed:
git status -s
git diff --stat

# If sane, commit and push:
git add .
git commit -m "Regenerate client from spec ($(date -u +%Y-%m-%d))"
git push origin main
```

## Why `--skip-validate-spec`

The upstream spec contains schema names with spaces (`Customer Patch`, `User Type Assignments`, etc.) and a handful of `$ref`s pointing at URL-encoded names (`#/components/schemas/Group%20Members`). The validator rejects both. The generator handles them fine at generation time — it's only the strict pre-flight validator that complains. Skipping it produces a working client.

If the platform team cleans up the spec to remove spaces from schema names, this flag can be removed.

## Why `python-pydantic-v1`

Nautobot 2.4 ships Pydantic 1.10.x as a transitive dependency. Generating against Pydantic V2 would require either pinning or a `pydantic.v1` shim, which is more friction than we need. We can revisit V2 when Nautobot drops V1 — track that as a follow-up.

## Patching `bearer` → `x-api-key`

If the upstream spec ever regresses to a `bearer` security scheme, run this Python snippet from the plugin repo root before regenerating:

```python
python3 - <<'PY'
import json, pathlib
spec_path = pathlib.Path("development/layer8-core-api.openapi.json")
spec = json.loads(spec_path.read_text())

spec["components"]["securitySchemes"].pop("bearer", None)
spec["components"]["securitySchemes"]["x-api-key"] = {
    "type": "apiKey", "in": "header", "name": "x-api-key"
}
if spec.get("security"):
    spec["security"] = [{"x-api-key": []}]

for path in spec["paths"].values():
    for op in path.values():
        if isinstance(op, dict) and "security" in op:
            op["security"] = [
                {"x-api-key": v} if k == "bearer" else {k: v}
                for entry in op["security"]
                for k, v in entry.items()
            ]

spec_path.write_text(json.dumps(spec, indent=2) + "\n")
print("patched")
PY
```

This is what was applied as a one-off when the spec first migrated. It should not be necessary on every regen — flag it to the platform team if you find yourself running it twice.

## Where the generated method names come from

The spec has no `operationId` declarations, so the generator synthesises method names from the path + HTTP verb. Examples:

| HTTP / path | Generated method |
|---|---|
| `GET /buildings` | `BuildingsApi.buildings_get(...)` |
| `GET /buildings/{id}` | `BuildingsApi.buildings_id_get(id)` |
| `POST /buildings` | `BuildingsApi.buildings_post(building_patch=...)` |
| `PATCH /buildings/{id}` | `BuildingsApi.buildings_id_patch(id, building_patch=...)` |
| `DELETE /buildings/{id}` | `BuildingsApi.buildings_id_delete(id)` |
| `GET /rooms` | `RoomsApi.rooms_get(...)` |
| `GET /tenancies` | `TenanciesApi.tenancies_get(...)` |

These names are *deterministic* given a fixed generator + spec — but they will change if either drifts. Long-term fix: add `operationId` to every operation in the spec upstream.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop isn't running | Start Docker Desktop. |
| Generator exits with `Errors found, validation failed` | Pre-flight validator hit known issues (schema names with spaces, etc.) | Add `--skip-validate-spec`. |
| `pip install` of the client repo fails with 401 | GitHub auth missing | Locally: `gh auth login`. In CI/prod: ensure the GitHub App installation token is being minted and mounted as a BuildKit secret. |
| Method names changed unexpectedly | Generator version drift OR spec drift | Pin the generator (`openapitools/openapi-generator-cli:v7.x.y`) and capture the regenerated method names; update call sites in `layer8_app/helpers/core_api.py` and `layer8_app/ssot_jobs/sync_tenant_api.py`. |
| Pydantic complains about types at import | Generated code targets V2 | Confirm `-g python-pydantic-v1` (not `python-pydantic` or `python`). |
| `pyproject.toml` in client repo has `GIT_USER_ID/GIT_REPO_ID` placeholder | Generator quirk; we don't pass `--git-user-id` / `--git-repo-id` | Either patch manually post-generation, or add `pyproject.toml` to the client repo's `.openapi-generator-ignore`. Cosmetic only — doesn't affect installs. |

## Related files

- [`development/layer8-core-api.openapi.json`](../../development/layer8-core-api.openapi.json) — the spec
- [`.claude/commands/regen-core-client.md`](../../.claude/commands/regen-core-client.md) — the slash command definition
- [`layer8_app/helpers/core_api.py`](../../layer8_app/helpers/core_api.py) — the plugin-side factory that constructs an authenticated client
- [`layer8_app/ssot_jobs/sync_tenant_api.py`](../../layer8_app/ssot_jobs/sync_tenant_api.py) — the primary call site
- Client repo: [`LayerEightTechnologies/layer8-core-api-py-client`](https://github.com/LayerEightTechnologies/layer8-core-api-py-client)
