# Generated by Django 5.1.4 on 2024-12-18 16:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0032_rename_wn_notes_observation_notes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Export',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('filters', models.JSONField(default=dict, help_text='Filters applied to the export')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', help_text='Status of the export', max_length=20)),
                ('progress', models.IntegerField(default=0, help_text='Progress percentage of the export')),
                ('file_path', models.CharField(blank=True, help_text='Path to the exported file', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Datetime when the export was created')),
                ('completed_at', models.DateTimeField(blank=True, help_text='Datetime when the export was completed', null=True)),
                ('error_message', models.TextField(blank=True, help_text='Error message if the export failed', null=True)),
                ('task_id', models.CharField(blank=True, help_text='Celery task ID for the export', max_length=255, null=True)),
                ('user', models.ForeignKey(blank=True, help_text='User who requested the export', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
