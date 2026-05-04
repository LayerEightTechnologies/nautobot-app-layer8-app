"""Top-level jobs for the Layer8 app."""

from django.db.models import Q

from nautobot.apps.jobs import JobButtonReceiver, register_jobs
from nautobot.dcim.models import Cable, Interface
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddressToInterface

from .ssot_jobs.sync_tenant_api import BuildingDataSource

name = "Layer8 App Jobs"


class DecomissionDevice(JobButtonReceiver):
    """Class to provide a job that decomissions a device in a Connected building."""

    class Meta:
        """Metadata for the job."""

        name = "Decommission Device"
        description = """
        This job marks a device as decommissioned by doing the following actions:
            -- Rename to `[decommed] <device_hostname>`
            -- Set status to `decommissioning`
            -- Update monitoring profile on device to `null`
            -- Remove primary IPV4 address from device
            -- Remove IP addresses from all interfaces
            -- Remove all cables terminating on device
        """

    def receive_job_button(self, obj):
        """Run the job."""
        user = self.user
        self.logger.info(f"Decomissioning this device: ```{obj.__dict__}```")
        if not user.has_perm("dcim.change_device"):
            self.logger.error(f"User {user} does not have permission to change devices.")
            return

        try:
            obj.name = f"[Decommed] {obj.name}"
            obj.status = Status.objects.get(name="Decommissioning")
            obj.custom_field_data.update({"monitoring_profile": {"monitoredBy": None, "monitoringFields": {}}})
            obj.primary_ip4 = None
            obj.validated_save()

            interfaces = Interface.objects.filter(device=obj.id)
            for interface in interfaces:
                interface_ips = IPAddressToInterface.objects.filter(interface=interface)
                for ip in interface_ips:
                    ip.delete()

        except Exception as e:
            self.logger.error(f"Error while decomissioning {obj.name}: {str(e)}")
            return

        try:
            connected_cables = Cable.objects.filter(
                Q(_termination_a_device_id=obj.id) | Q(_termination_b_device_id=obj.id)
            )
            for cable in connected_cables:
                cable.delete()
        except Exception as e:
            self.logger.error(f"Error while removing connected cables for {obj.name}: {str(e)}")
            return


jobs = [BuildingDataSource, DecomissionDevice]
register_jobs(*jobs)
