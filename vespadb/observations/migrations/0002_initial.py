# Generated by Django 5.0.3 on 2024-03-27 14:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('observations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_observations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='observation',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_observations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='observation',
            name='municipality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='observations', to='observations.municipality'),
        ),
        migrations.AddField(
            model_name='observation',
            name='reserved_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reserved_observations', to=settings.AUTH_USER_MODEL),
        ),
    ]
