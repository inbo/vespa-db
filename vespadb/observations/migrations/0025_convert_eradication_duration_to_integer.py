from django.db import migrations
from typing import Any

def convert_eradication_duration(apps: Any, schema_editor: Any) -> None:
    """Convert eradication duration from hours to minutes."""
    Observation = apps.get_model('observations', 'Observation')
    for observation in Observation.objects.all():
        if observation.eradication_duration:
            try:
                # Assuming the current format is in hours
                hours = float(observation.eradication_duration)
                minutes = int(hours * 60)
                observation.eradication_duration = minutes
                observation.save()
            except ValueError:
                # If conversion fails, set to null
                observation.eradication_duration = None
                observation.save()

class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0024_alter_observation_eradication_duration'),
    ]

    operations = [
        migrations.RunPython(convert_eradication_duration),
    ]