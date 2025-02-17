# Generated by Django 5.0.6 on 2024-07-18 11:07

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0020_alter_observation_eradication_method_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='anb',
            name='administrator',
            field=models.CharField(help_text='Administrator of the ANB', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='anb',
            name='contact',
            field=models.EmailField(help_text='Contact email of the ANB', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='anb',
            name='domain',
            field=models.CharField(help_text='Domain of the ANB', max_length=255),
        ),
        migrations.AlterField(
            model_name='anb',
            name='liberties',
            field=models.CharField(help_text='Liberties of the ANB', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='anb',
            name='polygon',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(help_text='Geographical polygon of the ANB', srid=31370),
        ),
        migrations.AlterField(
            model_name='anb',
            name='province',
            field=models.CharField(help_text='Province of the ANB', max_length=255),
        ),
        migrations.AlterField(
            model_name='anb',
            name='regio',
            field=models.CharField(help_text='Region of the ANB', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='datpublbs',
            field=models.DateField(blank=True, help_text='Publication date of the municipality data', null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='length',
            field=models.FloatField(blank=True, help_text='Length of the municipality boundary', null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='name',
            field=models.CharField(help_text='Name of the municipality', max_length=255),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='nis_code',
            field=models.CharField(help_text='NIS code of the municipality', max_length=255),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='numac',
            field=models.CharField(blank=True, help_text='NUMAC of the municipality', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='oidn',
            field=models.BigIntegerField(blank=True, help_text='OIDN of the municipality', null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='polygon',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(help_text='Geographical polygon of the municipality', srid=31370),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='province',
            field=models.ForeignKey(blank=True, help_text='Province to which the municipality belongs', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='municipalities', to='observations.province'),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='surface',
            field=models.FloatField(blank=True, help_text='Surface area of the municipality', null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='terrid',
            field=models.BigIntegerField(blank=True, help_text='TERRID of the municipality', null=True),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='uidn',
            field=models.BigIntegerField(blank=True, help_text='UIDN of the municipality', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='admin_notes',
            field=models.TextField(blank=True, help_text='Admin notes for the observation', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='anb',
            field=models.BooleanField(default=False, help_text='Flag indicating if the observation is in ANB area'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='created_by',
            field=models.ForeignKey(help_text='User who created the observation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_observations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='observation',
            name='created_datetime',
            field=models.DateTimeField(auto_now_add=True, help_text='Datetime when the observation was created'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_aftercare',
            field=models.CharField(blank=True, choices=[('nest_volledig_verwijderd', 'Nest volledig verwijderd'), ('nest_gedeeltelijk_verwijderd', 'Nest gedeeltelijk verwijderd'), ('nest_laten_hangen', 'Nest laten hangen')], help_text='Aftercare result of the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_date',
            field=models.DateTimeField(blank=True, help_text='Date when the nest was eradicated', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_duration',
            field=models.CharField(blank=True, help_text='Duration of the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_method',
            field=models.CharField(blank=True, choices=[('diepvries', 'Diepvries'), ('telescoopsteel', 'Telescoopsteel'), ('doos', 'doos'), ('vloeistofverstuiver', 'Vloeistofverstuiver'), ('poederverstuiver', 'Poederverstuiver'), ('stofzuiger', 'Stofzuiger')], help_text='Method used for the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_notes',
            field=models.TextField(blank=True, help_text='Notes about the eradication', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_persons',
            field=models.IntegerField(blank=True, help_text='Number of persons involved in the eradication', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_problems',
            field=models.CharField(blank=True, choices=[('steken', 'Steken'), ('nest_gevallen', 'Nest gevallen'), ('duizeligheid', 'Duizeligheid'), ('gif_spuiten', 'Gif Spuiten')], help_text='Problems encountered during the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_product',
            field=models.CharField(blank=True, choices=[('permas_d', 'Permas-D'), ('vloeibare_stikstof', 'Vloeibare stikstof'), ('vespa_ficam_d', 'Vespa Ficam D'), ('topscore_pal', 'Topscore PAL'), ('diatomeeenaarde', 'Diatomeeenaarde'), ('andere', 'Andere')], help_text='Product used for the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradication_result',
            field=models.CharField(blank=True, choices=[('successful', 'Succesvol behandeld'), ('unsuccessful', 'Niet succesvol behandeld'), ('untreated', 'Niet behandeld'), ('unknown', 'Onbekend')], help_text='Result of the eradication', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='eradicator_name',
            field=models.CharField(blank=True, help_text='Name of the person who eradicated the nest', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='images',
            field=models.JSONField(blank=True, default=list, help_text='List of images associated with the observation', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(help_text='Geographical location of the observation', srid=4326),
        ),
        migrations.AlterField(
            model_name='observation',
            name='modified_by',
            field=models.ForeignKey(help_text='User who last modified the observation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_observations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='observation',
            name='modified_datetime',
            field=models.DateTimeField(auto_now=True, help_text='Datetime when the observation was last modified'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='municipality',
            field=models.ForeignKey(blank=True, help_text='Municipality where the observation was made', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='observations', to='observations.municipality'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='nest_height',
            field=models.CharField(blank=True, choices=[('lager_dan_4_meter', 'Lager dan 4 meter'), ('hoger_dan_4_meter', 'Hoger dan 4 meter')], help_text='Height of the nest', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='nest_location',
            field=models.CharField(blank=True, choices=[('buiten_onbedekt_op_gebouw', 'Buiten, onbedekt op gebouw'), ('buiten_onbedekt_in_boom_of_struik', 'Buiten, onbedekt in boom of struik'), ('buiten_maar_overdekt_door_constructie', 'Buiten, maar overdekt door constructie'), ('buiten_natuurlijk_overdekt', 'Buiten, natuurlijk overdekt'), ('binnen_in_gebouw_of_constructie', 'Binnen, in gebouw of constructie')], help_text='Location of the nest', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='nest_size',
            field=models.CharField(blank=True, choices=[('kleiner_dan_25_cm', 'Kleiner dan 25 cm'), ('groter_dan_25_cm', 'Groter dan 25 cm')], help_text='Size of the nest', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='nest_type',
            field=models.CharField(blank=True, choices=[('actief_embryonaal_nest', 'actief embryonaal nest'), ('actief_primair_nest', 'actief primair nest'), ('actief_secundair_nest', 'actief secundair nest'), ('inactief_leeg_nest', 'inactief/leeg nest'), ('potentieel_nest', 'potentieel nest')], help_text='Type of the nest', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='observation_datetime',
            field=models.DateTimeField(help_text='Datetime when the observation was made'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='observer_email',
            field=models.EmailField(blank=True, help_text='Email of the observer', max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='observer_name',
            field=models.CharField(blank=True, help_text='Name of the observer', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='observer_phone_number',
            field=models.CharField(blank=True, help_text='Phone number of the observer', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='observer_received_email',
            field=models.BooleanField(default=False, help_text='Flag indicating if observer received email'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='province',
            field=models.ForeignKey(blank=True, help_text='Province where the observation was made', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='observations', to='observations.province'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='public_domain',
            field=models.BooleanField(blank=True, help_text='Flag indicating if the observation is in the public domain', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='reserved_by',
            field=models.ForeignKey(blank=True, help_text='User who reserved the observation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reserved_observations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='observation',
            name='reserved_datetime',
            field=models.DateTimeField(blank=True, help_text='Datetime when the observation was reserved', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='source',
            field=models.CharField(blank=True, help_text='Source of the observation', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='species',
            field=models.IntegerField(help_text='Species of the observed nest'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='visible',
            field=models.BooleanField(default=True, help_text='Flag indicating if the observation is visible'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_admin_notes',
            field=models.TextField(blank=True, help_text='Admin notes about the observation', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_cluster_id',
            field=models.IntegerField(blank=True, help_text='Cluster ID of the observation', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_created_datetime',
            field=models.DateTimeField(blank=True, help_text='Datetime when the observation was created in the source system', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_id',
            field=models.IntegerField(blank=True, help_text='Unique ID for the observation', null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_modified_datetime',
            field=models.DateTimeField(blank=True, help_text='Datetime when the observation was modified in the source system', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_notes',
            field=models.TextField(blank=True, help_text='Notes about the observation', null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='wn_validation_status',
            field=models.CharField(blank=True, choices=[('onbekend', 'Unknown'), ('goedgekeurd_met_bewijs', 'Approved (with evidence)'), ('goedgekeurd_door_admin', 'Approved (by admin)'), ('goedgekeurd_automatische_validatie', 'Approved (automatic validation)'), ('in_behandeling', 'In progress'), ('afgewezen', 'Rejected'), ('nog_niet_te_beoordelen', 'Not evaluable yet')], help_text='Validation status of the observation', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='length',
            field=models.FloatField(blank=True, help_text='Length of the province boundary', null=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='name',
            field=models.CharField(help_text='Name of the province', max_length=255),
        ),
        migrations.AlterField(
            model_name='province',
            name='nis_code',
            field=models.CharField(help_text='NIS code of the province', max_length=255),
        ),
        migrations.AlterField(
            model_name='province',
            name='oidn',
            field=models.BigIntegerField(blank=True, help_text='OIDN of the province', null=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='polygon',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(help_text='Geographical polygon of the province', srid=31370),
        ),
        migrations.AlterField(
            model_name='province',
            name='surface',
            field=models.FloatField(blank=True, help_text='Surface area of the province', null=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='terrid',
            field=models.BigIntegerField(blank=True, help_text='TERRID of the province', null=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='uidn',
            field=models.BigIntegerField(blank=True, help_text='UIDN of the province', null=True),
        ),
    ]
