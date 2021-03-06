# Generated by Django 3.2.9 on 2022-02-11 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0027_auto_20220210_2020'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrailSuitability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
        ),
        migrations.AddField(
            model_name='trail',
            name='suitability',
            field=models.ManyToManyField(related_name='suitable_trails', to='attractions2.TrailSuitability'),
        ),
    ]
