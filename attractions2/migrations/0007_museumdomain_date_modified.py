# Generated by Django 3.2.9 on 2021-11-08 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0006_attraction_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='museumdomain',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
