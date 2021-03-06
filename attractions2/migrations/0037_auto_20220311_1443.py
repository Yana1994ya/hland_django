# Generated by Django 3.2.9 on 2022-03-11 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0036_auto_20220311_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='trail',
            name='avg_rating',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='trail',
            name='rating_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
