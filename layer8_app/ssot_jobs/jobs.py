"""Jobs for Layer8 integration with SSoT App."""

from diffsync.enum import DiffSyncFlags
from django.urls import reverse
from nautobot.extras.jobs import BooleanVar, ObjectVar
from nautobot_ssot.jobs.base import DataSource, DataMapping

from .diffsync.adapters.layer8 import Layer8Adapter
from .diffsync.adapters.auvik import AuvikAdapter
from .diffsync.adapters.nautobot import NautobotAdapter, NautobotAuvikAdapter

import openapi_client

from ..helpers.get_m2m_token import get_api_token
from ..models import AuvikTenantBuildingRelationship

name = "Layer8 App SSoT Jobs"  # pylint:disable=invalid-name


def tenant_api(get_api_token=get_api_token):
    """Return the authenticated API client for the Tenant API."""
    api_token = get_api_token()
    configuration = openapi_client.Configuration(host="https://bcs-api.wavenetuk.com/v2.5.6")
    api_client = openapi_client.ApiClient(
        configuration, header_name="Authorization", header_value=f"Bearer {api_token}"
    )
    api_instance = openapi_client.DefaultApi(api_client)
    return api_instance


class Layer8DataSource(DataSource):
    """Class to provide a data source for Layer8 integration with SSoT App."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)
    bulk_import = BooleanVar(description="Enable using bulk create option for object creation.", default=False)

    class Meta:
        """Metadata for the data source."""

        name = "Tenant API Data Source"
        data_source = "Tenant API"
        description = "Data source for Tenant API integration with Nautobot SSoT App."
        has_sensitive_variables = False

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping(
                "Buildings",
                "https://bcs-api.wavenetuk.com/v2.5.6/buildings",
                "Locations",
                reverse("dcim:location_list"),
            ),
            DataMapping(
                "Rooms",
                "https://bcs-api.wavenetuk.com/v2.5.6/rooms",
                "Locations",
                reverse("dcim:location_list"),
            ),
        )

    def load_source_adapter(self):
        """Load data from Layer8 into DiffSync models."""
        if self.debug:
            self.logger.info("Connecting to Wavenet Tenant API...")
        client = tenant_api()
        self.source_adapter = Layer8Adapter(job=self, sync=self.sync, api_client=client)
        if self.debug:
            self.logger.info("Loading data from Wavenet Tenant API.")
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.target_adapter = NautobotAdapter(job=self, sync=self.sync)
        if self.debug:
            self.logger.info("Loading data from Nautobot.")
        self.target_adapter.load()

    def run(  # pylint: disable=arguments-differ, too-many-arguments
        self, dryrun, memory_profiling, debug, bulk_import, *args, **kwargs
    ):
        """Perform data syncrhonization."""
        self.bulk_import = bulk_import
        self.debug = debug
        self.dryrun = dryrun
        self.memory_profiling = memory_profiling
        super().run(dryrun=self.dryrun, memory_profiling=self.memory_profiling, *args, **kwargs)


class AuvikDataSource(DataSource):
    """Class to provide a data source for Auvik integration with SSoT App."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)
    # building_to_sync = ChoiceVar(
    #     description="Choose a building to synchronize from Auvik. <br /><small>Note: building must already be mapped to an Auvik Tenant in the <a href='/admin/layer8_app/auviktenantbuildingrelationship/'>admin section</a>.</small>",
    #     choices=AuvikTenantBuildingRelationship.objects.values_list("auvik_tenant_id", "building__name"),
    # )

    building_to_sync = ObjectVar(
        model=AuvikTenantBuildingRelationship,
        display_field="building.name",
        description="Choose a building to synchronize from Auvik. <br /><small>Note: building must already be mapped to an Auvik Tenant in the <a href='/admin/layer8_app/auviktenantbuildingrelationship/'>admin section</a>.</small>",
        query_params={
            "depth": 1,
        },
    )

    # Add DiffSync_Flags to skip unmatched records in Nautobot
    # i.e. if a record is in Nautobot but not in Auvik, it will not be deleted
    # This is useful for keeping records in Nautobot that are not present in / managed by Auvik
    # https://diffsync.readthedocs.io/en/latest/core_engine/index.html#global-and-model-flags
    def __init__(self):
        """Initialize the Auvik Data Source."""
        super().__init__()
        self.diffsync_flags = DiffSyncFlags.SKIP_UNMATCHED_DST

    class Meta:
        """Metadata for the data source."""

        name = "Auvik Data Source"
        data_source = "Auvik"
        description = """This data source will pull data from the Auvik API and synchronize it with Nautobot."""
        has_sensitive_variables = False

    # Get the Auvik Tenant Building Relationship
    # AuvikTenantBuildingRelationship.objects.get(building_id=(Location.objects.get(name="Record Hall - Hatton")))
    # Location.objects.get(id=AuvikTenantBuildingRelationship.objects.get(auvik_tenant_id=(AuvikTenant.objects.get(name="wnrecordhall"))).building_id)

    # @classmethod
    # def data_mappings(cls):
    #     """List describing the data mappings involved in this DataSource."""
    #     return (
    #         DataMapping(
    #             "Tenants",
    #             "https://api.auvik.com/v1/tenants",
    #             "Auvik Tenants",
    #             reverse("layer8_app:auviktenant_list"),
    #         ),
    #     )

    def load_source_adapter(self):
        """Load data from Auvik into DiffSync models."""
        if self.debug:
            self.logger.info("Connecting to Auvik API...")
        self.source_adapter = AuvikAdapter(job=self, sync=self.sync, building_id=self.building_to_sync)
        if self.debug:
            self.logger.info("Loading data from Auvik API.")
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.target_adapter = NautobotAuvikAdapter(job=self, sync=self.sync)
        if self.debug:
            self.logger.info("Loading data from Nautobot.")
        self.target_adapter.load()

    def run(  # pylint: disable=arguments-differ, too-many-arguments
        self, dryrun, memory_profiling, debug, building_to_sync, *args, **kwargs
    ):
        """Perform data syncrhonization."""
        self.debug = debug
        self.dryrun = dryrun
        self.memory_profiling = memory_profiling
        self.building_to_sync = building_to_sync
        super().run(
            dryrun=self.dryrun,
            memory_profiling=self.memory_profiling,
            building_to_sync=self.building_to_sync,
            *args,
            **kwargs,
        )


jobs = [Layer8DataSource, AuvikDataSource]
