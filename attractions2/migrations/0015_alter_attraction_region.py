# Generated by Django 3.2.9 on 2021-11-22 15:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('attractions2', '0013_auto_20211120_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attraction',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='attractions2.region'),
        ),
    ]