# Generated by Django 5.0.4 on 2024-04-04 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0008_municipality_province'),
        ('users', '0003_vespauser_postal_code_vespauser_province'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vespauser',
            name='postal_code',
        ),
        migrations.RemoveField(
            model_name='vespauser',
            name='province',
        ),
        migrations.AddField(
            model_name='vespauser',
            name='municipalities',
            field=models.ManyToManyField(blank=True, related_name='users', to='observations.municipality'),
        ),
    ]