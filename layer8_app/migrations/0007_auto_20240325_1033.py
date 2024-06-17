# Generated by Django 3.2.24 on 2024-03-25 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "0052_fix_interface_redundancy_group_created"),
        ("layer8_app", "0006_auto_20240322_1151"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auvikdevicemodels",
            name="nautobot_device_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="device_types",
                to="dcim.devicetype",
            ),
        ),
        migrations.AlterField(
            model_name="auvikdevicevendors",
            name="nautobot_manufacturer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="manufacturers",
                to="dcim.manufacturer",
            ),
        ),
    ]
