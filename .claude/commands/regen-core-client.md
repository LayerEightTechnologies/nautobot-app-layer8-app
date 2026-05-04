---
description: Regenerate the Layer8 Core API Python client from this repo's OpenAPI spec and push to its private repo.
argument-hint: [--no-push] [--client-dir PATH]
allowed-tools: Bash(docker:*), Bash(git:*), Bash(rm:*), Bash(rmdir:*), Bash(ls:*), Bash(mkdir:*), Bash(test:*), Bash(diff:*), Bash(cat:*), Bash(head:*), Bash(grep:*), Bash(wc:*), Read, Edit, Write
---

# Regenerate `layer8-core-api-py-client`

You are regenerating the Layer8 Core API Python client. The canonical OpenAPI spec lives in this plugin repo at `development/layer8-core-api.openapi.json`. Your job is to regenerate the client into a sibling clone of `LayerEightTechnologies/layer8-core-api-py-client`, show the user what changed, and (unless `--no-push` was passed) push the result to `main`.

The arguments the user passed are: `$ARGUMENTS`

## Procedure

### 1. Preconditions

- Verify Docker is running: `docker version --format "{{.Server.Version}}"`. If the daemon isn't reachable, abort with a clear message ("start Docker Desktop and re-run").
- Verify the spec exists: `development/layer8-core-api.openapi.json`. If missing, abort.
- Verify the spec uses the `x-api-key` security scheme (not `bearer`). Quick check: `grep -c '"x-api-key"' development/layer8-core-api.openapi.json` should be > 0. If it still references `bearer`, follow the patching procedure in `docs/dev/regenerating_openapi_client.md` BEFORE regenerating.

### 2. Locate the client repo working copy

- If the user passed `--client-dir <path>`, use that absolute or relative path.
- Otherwise default to `../layer8-core-api-py-client` (sibling of this plugin repo).
- Verify the directory exists, contains a `.git` directory, and the remote URL contains `layer8-core-api-py-client`. If any check fails, abort and tell the user how to clone it: `gh repo clone LayerEightTechnologies/layer8-core-api-py-client ../layer8-core-api-py-client`.
- Confirm `git status -s` in the client repo is clean. If there are uncommitted changes, stop and tell the user — don't blow over their work.

### 3. Generate

Run the openapi-generator Docker image. Mount the parent directory so both the spec and the client repo are accessible:

```bash
docker run --rm \
  -v <ABS-PATH-TO-PARENT-OF-PLUGIN-REPO>:/work \
  openapitools/openapi-generator-cli:latest generate \
  -i /work/<plugin-repo-dirname>/development/layer8-core-api.openapi.json \
  -g python-pydantic-v1 \
  -o /work/<client-repo-dirname> \
  --package-name layer8_core_api_py_client \
  --skip-validate-spec \
  --additional-properties=projectName=layer8-core-api-py-client,packageVersion=0.1.0,packageUrl=https://github.com/LayerEightTechnologies/layer8-core-api-py-client
```

Construct the absolute paths from the actual locations (use `pwd` from this repo to derive them). The `--skip-validate-spec` flag is necessary because the upstream spec has known schema-name-with-spaces issues that the validator rejects.

### 4. Strip generator boilerplate

Remove the bits we don't ship from the regenerated tree (these are re-emitted on every run, so we have to strip after every generation):

```bash
cd <client-repo-dir>
rm -f .travis.yml .gitlab-ci.yml git_push.sh
rm -f .github/workflows/python.yml
rmdir .github/workflows .github 2>/dev/null || true
```

### 5. Inspect the diff

In the client repo, run `git status -s` and `git diff --stat`. If the diff is empty, tell the user "spec unchanged — no regeneration needed" and stop. Otherwise summarise the diff for the user (count of files changed, breakdown by directory: `models/`, `api/`, `docs/`, top-level).

If any *.py files were added under `api/` (new endpoints) or `models/` (new schemas), surface that prominently.

### 6. Smoke-test the regenerated client

Quickly validate the regenerated package is at least syntactically importable:

```bash
python3 -c "
import ast, pathlib
errors = []
for p in pathlib.Path('<client-repo-dir>/layer8_core_api_py_client').rglob('*.py'):
    try:
        ast.parse(p.read_text(), filename=str(p))
    except SyntaxError as e:
        errors.append(f'{p}: {e}')
print('OK' if not errors else f'{len(errors)} parse errors:\\n' + '\\n'.join(errors))
"
```

If parse errors are reported, abort with the list.

### 7. Commit and push (unless `--no-push`)

If `--no-push` is in the user's arguments, stop here. Tell the user the changes are staged-but-uncommitted in `<client-repo-dir>` and exit.

Otherwise:

- Show the user the summary diff one more time and ask for confirmation before pushing. **Do not push without an explicit "yes" / "go" / "push it" from the user.**
- On confirmation, in the client repo:
  ```bash
  git add .
  git -c user.email="<user-email>" -c user.name="<user-name>" commit -m "Regenerate client from spec ($(date -u +%Y-%m-%d))"
  git push origin main
  ```
  Use the email and name from `git config user.email` / `user.name` (run them in the plugin repo to inherit the developer's identity).
- After push, confirm the push succeeded by reading the last line of `git log -1 --oneline`.

### 8. Aftercare

Tell the user:
- The new client commit hash and short message.
- That `pip install git+https://github.com/LayerEightTechnologies/layer8-core-api-py-client.git@main` will pick up the regenerated client on the next install.
- If method names changed (new endpoints, renamed operations), point them at `layer8_app/helpers/core_api.py` and `layer8_app/ssot_jobs/sync_tenant_api.py` as the call sites that may need updating.

## Notes for you, the agent

- Be careful with paths. `docker run -v <host-path>:<container-path>` requires absolute host paths. Derive them from `pwd` rather than guessing.
- The spec is shared in this plugin repo, but the regenerated output goes to a SEPARATE repo. Don't accidentally overwrite this plugin's own files with generated content.
- The client repo's `pyproject.toml` has placeholder `repository = "https://github.com/GIT_USER_ID/GIT_REPO_ID"` — that's a known generator quirk. If the user wants it fixed, suggest passing `--git-user-id LayerEightTechnologies --git-repo-id layer8-core-api-py-client` to a future regen, OR adding `pyproject.toml` to `.openapi-generator-ignore` and patching it manually once.
- If the user reports that `pip install` of the regenerated client fails on the test server, the first thing to check is whether the GitHub App's installation token is still valid (1h expiry). The deploy script should re-mint on every run.
