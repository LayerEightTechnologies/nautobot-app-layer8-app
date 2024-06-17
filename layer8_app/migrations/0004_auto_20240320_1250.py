# Generated by Django 3.2.24 on 2024-03-20 12:50

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "0052_fix_interface_redundancy_group_created"),
        ("layer8_app", "0003_auto_20240320_1243"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="auviktenant",
            name="building",
        ),
        migrations.CreateModel(
            name="AuvikTenantBuildingRelationships",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                (
                    "auvik_tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auvik_tenant",
                        to="layer8_app.auviktenant",
                    ),
                ),
                (
                    "building",
                    models.ForeignKey(
                        limit_choices_to={"location_type__name": "Building"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="building",
                        to="dcim.location",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
