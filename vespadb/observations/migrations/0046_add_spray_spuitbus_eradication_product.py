# Generated for adding spray_spuitbus option to eradication_product choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0045_observation_observation_observa_b2ea93_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='eradication_product',
            field=models.CharField(blank=True, choices=[
                ('spray_spuitbus', 'Spray of spuitbus'),
                ('permas_d', 'Permas-D'),
                ('vloeibare_stikstof', 'Vloeibare stikstof'),
                ('ficam_d', 'Ficam D'),
                ('topscore_pal', 'Topscore PAL'),
                ('diatomeeenaarde', 'Diatomeeënaarde'),
                ('ether_aceton_ethyl_acetaat', 'Ether, aceton of ethylacetaat'),
                ('vespa', 'Vespa'),
                ('andere', 'Andere')
            ], help_text='Product used for the eradication', max_length=50, null=True),
        ),
    ]