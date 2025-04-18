# Generated by Django 5.0.3 on 2024-03-27 20:50

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ANB',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('domain', models.CharField(max_length=255)),
                ('province', models.CharField(max_length=255)),
                ('regio', models.CharField(max_length=255)),
                ('liberties', models.CharField(max_length=255)),
                ('administrator', models.CharField(max_length=255)),
                ('contact', models.EmailField(max_length=255)),
                ('polygon', django.contrib.gis.db.models.fields.MultiPolygonField(srid=31370)),
            ],
        ),
    ]
