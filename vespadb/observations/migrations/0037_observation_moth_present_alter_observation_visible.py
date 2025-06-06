# Generated by Django 5.1.4 on 2025-03-10 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0036_observation_queen_present'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='moth_present',
            field=models.BooleanField(blank=True, help_text='Shows if moths were present during the eradication', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='visible',
            field=models.BooleanField(default=True, help_text='Flag indicating if the observation is visible', null=True),
        ),
    ]
