"""Helpers for constructing authenticated Layer8 Core API clients."""

import os

import layer8_core_api_py_client

from .get_m2m_token import get_api_token


def core_api_base_url():
    """Return the Layer8 Core API base URL for this Nautobot instance."""
    fqdn = os.environ.get("INSTANCE_FQDN", "").strip()
    if not fqdn:
        raise RuntimeError(
            "INSTANCE_FQDN env var is not set; cannot construct Layer8 Core API URL."
        )
    return f"https://core-api.{fqdn}"


def core_api_client(get_token=get_api_token, base_url_fn=core_api_base_url):
    """Return an authenticated layer8_core_api_py_client.ApiClient.

    Per-tag API classes (BuildingsApi, RoomsApi, TenanciesApi, etc.) are
    instantiated by callers from the returned client, e.g.::

        from layer8_core_api_py_client.api.buildings_api import BuildingsApi
        client = core_api_client()
        buildings = BuildingsApi(client).buildings_get(limit="1000")
    """
    configuration = layer8_core_api_py_client.Configuration(host=base_url_fn())
    configuration.api_key["x-api-key"] = get_token()
    return layer8_core_api_py_client.ApiClient(configuration)
