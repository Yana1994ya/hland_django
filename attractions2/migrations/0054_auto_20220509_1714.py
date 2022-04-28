# Generated by Django 3.2.9 on 2022-05-09 17:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('attractions2', '0053_auto_20220508_1945'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tour',
            name='destination',
        ),
        migrations.RemoveField(
            model_name='tour',
            name='overnight',
        ),
        migrations.AlterField(
            model_name='tour',
            name='package',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='attractions2.package'),
        ),
        migrations.AlterField(
            model_name='tour',
            name='start_location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='attractions2.startlocation'),
        ),
        migrations.AlterField(
            model_name='tour',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='attractions2.tourtheme'),
        ),
        migrations.AlterField(
            model_name='tour',
            name='tour_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='attractions2.tourtype'),
        ),
        migrations.DeleteModel(
            name='Overnight',
        ),
        migrations.DeleteModel(
            name='TourDestination',
        ),
    ]