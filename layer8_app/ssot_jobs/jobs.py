"""Dormant SSOT job source for Auvik integration.

Auvik integration is currently disabled. This module is preserved on disk so
that the AuvikDataSource job can be revived in the future without re-deriving
its DiffSync wiring. Nothing in the live import graph references this module —
to revive Auvik, re-add the appropriate `register_jobs` call from `jobs.py`
and re-enable the helper, admin, and API surface that was commented out at the
same time.
"""

from diffsync.enum import DiffSyncFlags
from nautobot.extras.jobs import BooleanVar, ObjectVar
from nautobot_ssot.jobs.base import DataSource

from .diffsync.adapters.auvik import AuvikAdapter
from .diffsync.adapters.nautobot import NautobotAuvikAdapter

from ..models import AuvikTenantBuildingRelationship

name = "Layer8 App SSoT Jobs"  # pylint:disable=invalid-name


class AuvikDataSource(DataSource):
    """Class to provide a data source for Auvik integration with SSoT App."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

    building_to_sync = ObjectVar(
        model=AuvikTenantBuildingRelationship,
        display_field="building.name",
        description=(
            "Choose a building to synchronize from Auvik. <br /><small>Note: building must already "
            "be mapped to an Auvik Tenant in the "
            "<a href='/admin/layer8_app/auviktenantbuildingrelationship/'>admin section</a>.</small>"
        ),
        query_params={
            "depth": 1,
        },
    )

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


jobs = [AuvikDataSource]
