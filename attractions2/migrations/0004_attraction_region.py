# Generated by Django 3.2.9 on 2021-11-07 16:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0003_auto_20211107_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='attraction',
            name='region',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='attractions2.region'),
            preserve_default=False,
        ),
    ]