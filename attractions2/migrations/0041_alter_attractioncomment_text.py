# Generated by Django 3.2.9 on 2022-03-11 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0040_auto_20220311_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attractioncomment',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
