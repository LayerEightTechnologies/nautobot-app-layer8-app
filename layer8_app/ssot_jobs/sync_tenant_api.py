"""SSOT job: sync Buildings and Rooms from the Layer8 Core API into Nautobot DCIM Locations."""

from typing import Annotated, Optional

from diffsync import DiffSync

from nautobot.dcim.models import Location

from nautobot_ssot.contrib import NautobotModel, NautobotAdapter, CustomFieldAnnotation
from nautobot_ssot.jobs.base import DataSource

from layer8_core_api_py_client.api.buildings_api import BuildingsApi
from layer8_core_api_py_client.api.rooms_api import RoomsApi
from layer8_core_api_py_client.exceptions import ApiException

from ..helpers.core_api import core_api_client


name = "Layer8 App SSoT Jobs"  # pylint:disable=invalid-name


class BuildingModel(NautobotModel):
    """DiffSync model for Buildings (Nautobot Locations of LocationType 'Building')."""

    _model = Location
    _modelname = "location"
    _identifiers = ("external_id", "location_type__name")
    _attributes = ("name", "status__name")

    # Set both `name` and `key` to work around a bug in nautobot_ssot.contrib.adapter
    # (line ~92): the load path checks `metadata.name in database_object.cf` but does
    # `database_object.cf[metadata.key]`. With only `key=` set, `metadata.name` is
    # None and the custom field never gets loaded into the diffsync model.
    external_id: Annotated[int, CustomFieldAnnotation(name="external_id", key="external_id")]
    name: str
    location_type__name: str
    status__name: str = "Planned"

    @classmethod
    def get_queryset(cls):
        """Limit the loaded queryset to Locations of LocationType 'Building'.

        Without this override, contrib's default `cls._model.objects.all()` returns
        every Location (both Buildings and Rooms), which would cause RoomModel and
        BuildingModel to double-load each other's records.
        """
        return Location.objects.filter(location_type__name="Building")


class RoomModel(NautobotModel):
    """DiffSync model for Rooms (Nautobot Locations of LocationType 'Room', nested under Buildings)."""

    _model = Location
    _modelname = "room"
    _identifiers = ("external_id", "location_type__name")
    _attributes = ("name", "status__name", "parent__name")

    # Set both `name` and `key` to work around a bug in nautobot_ssot.contrib.adapter
    # (line ~92): the load path checks `metadata.name in database_object.cf` but does
    # `database_object.cf[metadata.key]`. With only `key=` set, `metadata.name` is
    # None and the custom field never gets loaded into the diffsync model.
    external_id: Annotated[int, CustomFieldAnnotation(name="external_id", key="external_id")]
    name: str
    location_type__name: str
    parent__name: Optional[str] = None
    status__name: str = "Planned"

    @classmethod
    def get_queryset(cls):
        """Limit the loaded queryset to Locations of LocationType 'Room'."""
        return Location.objects.filter(location_type__name="Room")


class TenantApiNautobotAdapter(NautobotAdapter):
    """DiffSync adapter for Nautobot (target)."""

    location = BuildingModel
    room = RoomModel
    top_level = ("location", "room")


class TenantApiRemoteAdapter(DiffSync):
    """DiffSync adapter for the Layer8 Core API (source)."""

    location = BuildingModel
    room = RoomModel
    top_level = ("location", "room")

    def __init__(self, *args, api_client, **kwargs):
        """Initialize the adapter."""
        super().__init__(*args, **kwargs)
        self.api_client = api_client
        # Maps Core-API building.id (int) -> building_name (str). Built during
        # load_buildings() and consumed during load_rooms() to resolve parent
        # links. Rooms whose building isn't in this map are skipped.
        self._building_index = {}

    def load_buildings(self):
        """Load buildings from the Core API into DiffSync models."""
        try:
            buildings = BuildingsApi(self.api_client).buildings_get(limit="1000")
        except ApiException as e:
            raise Exception(f"Failed to fetch buildings from Layer8 Core API: {e}")

        for building in buildings:
            self._building_index[building.id] = building.building_name
            status_name = "Active" if building.status == "Live Building" else "Planned"
            self.add(
                self.location(
                    external_id=int(building.id),
                    name=building.building_name,
                    location_type__name="Building",
                    status__name=status_name,
                )
            )

    def load_rooms(self):
        """Load rooms from the Core API into DiffSync models, skipping orphans."""
        try:
            rooms = RoomsApi(self.api_client).rooms_get(limit="10000")
        except ApiException as e:
            raise Exception(f"Failed to fetch rooms from Layer8 Core API: {e}")

        for room in rooms:
            parent_name = self._building_index.get(room.building_id)
            if parent_name is None:
                continue
            status_name = "Active" if room.is_active else "Retired"
            self.add(
                self.room(
                    external_id=int(room.id),
                    name=room.room_number,
                    location_type__name="Room",
                    parent__name=parent_name,
                    status__name=status_name,
                )
            )

    def load(self):
        """Load buildings then rooms from the Core API."""
        self.load_buildings()
        self.load_rooms()


class BuildingDataSource(DataSource):
    """SSOT job that syncs Buildings and Rooms from the Layer8 Core API into Nautobot."""

    class Meta:
        """Metadata for the job."""

        name = "Layer8 Core API Data Source"
        description = (
            "Synchronizes building and room records from the Layer8 Core API "
            "into Nautobot DCIM Locations."
        )
        has_sensitive_variables = False

    def load_source_adapter(self):
        """Load the source adapter."""
        self.source_adapter = TenantApiRemoteAdapter(api_client=core_api_client())
        self.source_adapter.load()
        return self.source_adapter

    def load_target_adapter(self):
        """Load the target adapter."""
        self.target_adapter = TenantApiNautobotAdapter(job=self)
        self.target_adapter.load()
        return self.target_adapter

    def run(self, dryrun=False, memory_profiling=False, *args, **kwargs):
        """Run the job."""
        self.dryrun = dryrun
        self.memory_profiling = memory_profiling
        super().run(dryrun=self.dryrun, memory_profiling=self.memory_profiling, *args, **kwargs)


jobs = [BuildingDataSource]
