# Generated by Django 3.2.24 on 2024-03-22 11:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "0052_fix_interface_redundancy_group_created"),
        ("layer8_app", "0005_rename_auviktenantbuildingrelationships_auviktenantbuildingrelationship"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auviktenantbuildingrelationship",
            name="auvik_tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="auvik_tenants", to="layer8_app.auviktenant"
            ),
        ),
        migrations.AlterField(
            model_name="auviktenantbuildingrelationship",
            name="building",
            field=models.ForeignKey(
                limit_choices_to={"location_type__name": "Building"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="buildings",
                to="dcim.location",
            ),
        ),
        migrations.CreateModel(
            name="AuvikDeviceVendors",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("auvik_vendor_name", models.CharField(max_length=255)),
                (
                    "nautobot_manufacturer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="manufacturers",
                        to="dcim.manufacturer",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AuvikDeviceModels",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("auvik_model_name", models.CharField(max_length=255)),
                (
                    "nautobot_device_type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="device_types",
                        to="dcim.devicetype",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
