"""Utility to fetch the Layer8 Core API token from a Nautobot Secret."""

from django.core.exceptions import ObjectDoesNotExist

from nautobot.extras.models import Secret


def get_api_token():
    """Get the API token from secret storage."""
    auth_token_secret_name = "Layer8 Core API Key"  # nosec B105

    try:
        auth_token_secret_object = Secret.objects.get(name=auth_token_secret_name)
    except ObjectDoesNotExist:
        raise Exception(f"Secret '{auth_token_secret_name}' not found.")

    try:
        auth_token = auth_token_secret_object.get_value()
    except Exception as e:
        raise Exception(f"Failed to retrieve value for secret '{auth_token_secret_name}': {e}")

    if not auth_token:
        raise Exception(f"Secret '{auth_token_secret_name}' is empty.")

    return auth_token
