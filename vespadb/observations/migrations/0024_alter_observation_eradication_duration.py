# Generated by Django 5.0.6 on 2024-09-08 16:16

from django.db import migrations, models
from typing import Any

def delete_invalid_observations(apps: Any, schema_editor: Any) -> None:
    """."""
    Observation = apps.get_model('observations', 'Observation')
    # Delete all observations where eradication_duration is not a valid integer
    invalid_observations = Observation.objects.filter(
        eradication_duration__isnull=False
    ).exclude(
        eradication_duration__regex=r'^\d+$'
    )
    invalid_observations.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0023_alter_observation_eradication_date'),
    ]

    operations = [
        migrations.RunPython(delete_invalid_observations),
        migrations.AlterField(
            model_name='observation',
            name='eradication_duration',
            field=models.IntegerField(blank=True, help_text='Duration of the eradication in minutes', null=True),
        ),
    ]