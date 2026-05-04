"""Mint a short-lived GitHub App installation token, write to /out/token.

Designed to run inside a one-shot python:3.11-slim container with pyjwt + requests
installed. The token is the only thing written to disk; nothing is printed to stdout.

Required mounts:
  /run/secrets/pem   ro   — the App's private key PEM (1 file, mode 0400)
  /out/token         rw   — empty file the token is written into

Required env vars:
  GITHUB_APP_ID            numeric App ID
  GITHUB_INSTALLATION_ID   numeric Installation ID

Exit codes:
  0  success — token written to /out/token
  1  any failure — the token file is left empty
"""

import os
import sys
import time

import jwt
import requests


def main():
    """Mint and write the token."""
    try:
        app_id = os.environ["GITHUB_APP_ID"]
        installation_id = os.environ["GITHUB_INSTALLATION_ID"]
        pem = open("/run/secrets/pem").read()
    except (KeyError, FileNotFoundError) as exc:
        print(f"Missing input: {exc}", file=sys.stderr)
        sys.exit(1)

    now = int(time.time())
    encoded_jwt = jwt.encode(
        {"iat": now - 60, "exp": now + 540, "iss": app_id},
        pem,
        algorithm="RS256",
    )
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    if response.status_code >= 400:
        print(
            f"GitHub App token mint failed: {response.status_code} {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)
    token = response.json().get("token")
    if not token:
        print(f"GitHub returned 200 but no token: {response.json()}", file=sys.stderr)
        sys.exit(1)
    open("/out/token", "w").write(token)


if __name__ == "__main__":
    main()
