# Generated by Django 5.0.6 on 2024-10-22 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0029_alter_observation_observer_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='observer_phone_number',
            field=models.CharField(blank=True, help_text='Phone number of the observer', max_length=200, null=True),
        ),
    ]