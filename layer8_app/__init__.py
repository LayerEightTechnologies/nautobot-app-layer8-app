"""App declaration for layer8_app."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig
from nautobot.core.signals import nautobot_database_ready

from . import navigation
from .signals import create_custom_fields, create_default_locationtypes

__version__ = metadata.version(__name__)


class Layer8AppConfig(NautobotAppConfig):
    """App configuration for the layer8_app app."""

    name = "layer8_app"
    verbose_name = "Layer8 App"
    version = __version__
    author = "Layer8 Technologies Ltd"
    description = "Layer8 App for provisioning custom objects and providing SSOT jobs."
    base_url = "layer8-app"
    required_settings = []
    min_version = "2.0.0"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}
    jobs = "jobs.jobs"

    nav_menu_items = navigation.menu_items

    def ready(self):
        """Run when the application is ready."""
        super().ready()
        nautobot_database_ready.connect(create_default_locationtypes, sender=self)
        nautobot_database_ready.connect(create_custom_fields, sender=self)


config = Layer8AppConfig  # pylint:disable=invalid-name
